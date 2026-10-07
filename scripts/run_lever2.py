#!/usr/bin/env python3
"""Lever 2 (translate-then-answer) on MGSM es, per results/lever2_plan.md.

For each of the 250 MGSM es ids, three calls to the local llama-server:
1. translate es -> en: thinking OFF, temperature 0, max_tokens 1024;
2. answer the English text exactly like the en baseline (run_mgsm.py en
   prompt + GENERATION, thinking as in the baseline = server default);
3. translate the step-2 content en -> es: thinking OFF, temperature 0,
   max_tokens 2048, keep every number.

Appends one JSON line per id to results/mgsm_raw.lever2.jsonl: id, lang,
gold, tag, and per step ("translate_in", "answer", "translate_out") the
content, reasoning_content, finish_reason, usage, timings, wall; plus
"content" (= step-3 content, what the MGSM scorer reads), "total_tokens"
(sum of prompt + completion over the three calls) and "wall".
Resumable: skips ids already present. An id is written only if all three
calls succeed.

Options: --limit N (process at most N pending ids, for testing),
--stop-at HH:MM (local time; no new id is started at or after it),
--check (plumbing check on a non-MGSM sentence, prints and exits; no data).
"""
import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_mgsm import BASE, GENERATION, PROMPTS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA_IN = ROOT / "data" / "mgsm_es.jsonl"
RESULTS_DIR = ROOT / "results"
TAG = "lever2"
RAW_OUT = RESULTS_DIR / f"mgsm_raw.{TAG}.jsonl"
PROPS_OUT = RESULTS_DIR / f"server_props.{TAG}.json"

TRANSLATE_IN = ("Translate the following math problem from Spanish to English. "
                "Output only the translation, nothing else.\n\n")
TRANSLATE_OUT = ("Translate the following answer from English to Spanish. "
                 "Keep every number exactly as it is. Output only the translation, "
                 "nothing else.\n\n")
NO_THINK = {"chat_template_kwargs": {"enable_thinking": False}}


def log(msg):
    print(f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] {msg}", flush=True)


def call(payload):
    t0 = time.monotonic()
    r = requests.post(f"{BASE}/v1/chat/completions", json=payload, timeout=1800)
    r.raise_for_status()
    data = r.json()
    wall = time.monotonic() - t0
    choice = data["choices"][0]
    msg = choice.get("message") or {}
    return {
        "content": msg.get("content"),
        "reasoning_content": msg.get("reasoning_content"),
        "finish_reason": choice.get("finish_reason"),
        "usage": data.get("usage"),
        "timings": data.get("timings"),
        "wall": wall,
    }


def translate(prompt, text, max_tokens):
    return call({
        "messages": [{"role": "user", "content": prompt + text}],
        "temperature": 0,
        "max_tokens": max_tokens,
        **NO_THINK,
    })


def answer_en(question_en):
    return call({
        "messages": [{"role": "user", "content": PROMPTS["en"] + "\n\n" + question_en}],
        "temperature": GENERATION["temperature"],
        "top_p": GENERATION["top_p"],
        "top_k": GENERATION["top_k"],
        "seed": GENERATION["seed"],
        "max_tokens": GENERATION["max_tokens"],
    })


def tokens(step):
    u = step.get("usage") or {}
    return u.get("prompt_tokens", 0) + u.get("completion_tokens", 0)


def parse_stop_at(s):
    if s is None:
        return None
    hh, mm = s.split(":")
    now = dt.datetime.now()
    return now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--limit", type=int, help="process at most N pending ids")
    ap.add_argument("--stop-at", metavar="HH:MM", help="start no new id at/after this local time")
    ap.add_argument("--check", action="store_true",
                    help="plumbing check (non-MGSM sentence, thinking off); no data written")
    args = ap.parse_args()

    if args.check:
        s = translate(TRANSLATE_IN, "El gato duerme en la ventana.", 1024)
        rc = s["reasoning_content"]
        print(json.dumps({"content": s["content"], "reasoning_content": rc,
                          "finish_reason": s["finish_reason"], "usage": s["usage"]},
                         ensure_ascii=False, indent=2))
        print("thinking-off OK (no reasoning_content)" if not rc else "FAIL: reasoning_content present")
        sys.exit(0 if not rc else 1)

    stop_at = parse_stop_at(args.stop_at)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if not PROPS_OUT.exists():
        r = requests.get(f"{BASE}/props", timeout=30)
        r.raise_for_status()
        PROPS_OUT.write_text(json.dumps(r.json(), indent=2, ensure_ascii=False), encoding="utf-8")
        log(f"saved server props -> {PROPS_OUT.name}")

    items = [json.loads(l) for l in DATA_IN.open(encoding="utf-8") if l.strip()]
    done = set()
    if RAW_OUT.exists():
        for line in RAW_OUT.open(encoding="utf-8"):
            try:
                done.add(json.loads(line)["id"])
            except (json.JSONDecodeError, KeyError):
                pass
    pending = [it for it in items if it["id"] not in done]
    if args.limit is not None:
        pending = pending[:args.limit]
    log(f"tag={TAG} -> {RAW_OUT.name}; ids={len(items)} done={len(done)} "
        f"this run={len(pending)} stop_at={stop_at}")

    n_ok = 0
    for n, it in enumerate(pending, start=1):
        if stop_at is not None and dt.datetime.now() >= stop_at:
            log(f"stop_at {args.stop_at} reached; stopping before id={it['id']}")
            break
        try:
            s1 = translate(TRANSLATE_IN, it["question"], 1024)
            s2 = answer_en(s1["content"] or "")
            s3 = translate(TRANSLATE_OUT, s2["content"] or "", 2048)
        except Exception as e:
            log(f"id={it['id']}: FAILED ({e}); will retry next run")
            continue
        steps = {"translate_in": s1, "answer": s2, "translate_out": s3}
        rec = {
            "id": it["id"],
            "lang": "es",
            "gold": it["answer_number"],
            "tag": TAG,
            "question": it["question"],
            **steps,
            "content": s3["content"],
            "finish_reason": s3["finish_reason"],
            "total_tokens": sum(tokens(s) for s in steps.values()),
            "wall": sum(s["wall"] for s in steps.values()),
        }
        with RAW_OUT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        n_ok += 1
        log(f"({n}/{len(pending)}) id={it['id']} total={rec['total_tokens']} "
            f"[{tokens(s1)}+{tokens(s2)}+{tokens(s3)}] "
            f"finish={s1['finish_reason']}/{s2['finish_reason']}/{s3['finish_reason']} "
            f"wall={rec['wall']:.1f}s")
    log(f"run finished: {n_ok} written this run; total in file={len(done) + n_ok}/{len(items)}")


if __name__ == "__main__":
    main()
