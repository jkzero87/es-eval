#!/usr/bin/env python3
"""F1 baseline: run MGSM (en/es/zh) against the local llama-server.

- Loads mgsm test split (en, es, zh) from HF (question + answer_number).
- Interleaves by id (id0-en, id0-es, id0-zh, id1-...) so server drift spreads.
- POSTs /v1/chat/completions: temperature 1.0, top_p 0.95, top_k 20, seed 42,
  max_tokens 8192 (no reasoning_effort).
- Appends one JSON line per item to results/mgsm_raw.jsonl:
  id, lang, gold, content, reasoning_content, finish_reason, usage, timings,
  wall (seconds). Resumable: skips (id, lang) already present.
- Saves GET /props to results/server_props.json before the first item.

Run under nohup; logs go wherever stdout/stderr are redirected.
"""
import json
import sys
import time
from pathlib import Path

import requests
from datasets import load_dataset

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
RAW_OUT = RESULTS_DIR / "mgsm_raw.jsonl"
PROPS_OUT = RESULTS_DIR / "server_props.json"
BASE = "http://127.0.0.1:8092"

LANGS = ["en", "es", "zh"]
PROMPTS = {
    "en": "Solve step by step. End with a final line 'Answer: <number>'.",
    "es": "Resuelve paso a paso. Termina con una línea final 'Respuesta: <número>'.",
    "zh": "请逐步解答。最后一行写 '答案：<数字>'.",
}

GENERATION = {
    "temperature": 1.0,
    "top_p": 0.95,
    "top_k": 20,
    "seed": 42,
    "max_tokens": 8192,
}


def log(msg):
    print(f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] {msg}", flush=True)


def load_questions():
    qs = {}
    for lang in LANGS:
        try:
            ds = load_dataset("juletxara/mgsm", lang, split="test")
        except Exception as e:
            print(f"ERROR: failed to load juletxara/mgsm config={lang!r}: {e}", file=sys.stderr)
            raise
        qs[lang] = {i: (row["question"], row["answer_number"])
                    for i, row in enumerate(ds, start=1)}
    return qs


def done_pairs():
    done = set()
    if RAW_OUT.exists():
        with RAW_OUT.open(encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    done.add((rec["id"], rec["lang"]))
                except (json.JSONDecodeError, KeyError):
                    pass
    return done


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    # Save server props before the first item (idempotent: only if absent).
    if not PROPS_OUT.exists():
        r = requests.get(f"{BASE}/props", timeout=30)
        r.raise_for_status()
        PROPS_OUT.write_text(json.dumps(r.json(), indent=2, ensure_ascii=False), encoding="utf-8")
        log(f"saved server props -> {PROPS_OUT.name}")

    qs = load_questions()
    max_id = max(max(qs[l]) for l in LANGS)
    done = done_pairs()
    pending = [(i, l) for i in range(1, max_id + 1) for l in LANGS if (i, l) not in done]
    total = max_id * len(LANGS)
    log(f"ids 1..{max_id}, langs {LANGS}; done={len(done)} pending={len(pending)} total={total}")
    if not pending:
        log("nothing to do.")
        return

    n_ok = 0
    for n, (i, lang) in enumerate(pending, start=1):
        question, gold = qs[lang][i]
        payload = {
            "messages": [{"role": "user", "content": PROMPTS[lang] + "\n\n" + question}],
            "temperature": GENERATION["temperature"],
            "top_p": GENERATION["top_p"],
            "top_k": GENERATION["top_k"],
            "seed": GENERATION["seed"],
            "max_tokens": GENERATION["max_tokens"],
        }
        try:
            t0 = time.monotonic()
            r = requests.post(f"{BASE}/v1/chat/completions", json=payload, timeout=1800)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            log(f"id={i} {lang}: FAILED ({e}); will retry next run")
            continue
        wall = time.monotonic() - t0
        choice = data["choices"][0]
        msg = choice.get("message") or {}
        rec = {
            "id": i,
            "lang": lang,
            "gold": gold,
            "content": msg.get("content"),
            "reasoning_content": msg.get("reasoning_content"),
            "finish_reason": choice.get("finish_reason"),
            "usage": data.get("usage"),
            "timings": data.get("timings"),
            "wall": wall,
        }
        with RAW_OUT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        n_ok += 1
        tt = rec.get("timings") or {}
        n_pr = (rec.get("usage") or {}).get("completion_tokens", 0)
        log(f"({n}/{len(pending)}) id={i} {lang} finish={rec['finish_reason']} "
            f"completion={n_pr} wall={wall:.1f}s "
            f"predicted_per_s={tt.get('predicted_per_second', 0):.2f} "
            f"draft={tt.get('draft_n', 0)}/{tt.get('draft_n_accepted', 0)}")
    log(f"run finished: {n_ok}/{len(pending)} succeeded; total in file={len(done) + n_ok}/{total}")


if __name__ == "__main__":
    main()
