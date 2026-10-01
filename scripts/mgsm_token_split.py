#!/usr/bin/env python3
"""Exact reasoning vs answer token counts for results/mgsm_raw.jsonl.

For each record, POSTs reasoning_content and content separately to the
server's /tokenize (no special tokens added; empty text counts 0 without a
request), 0.2 s apart, and appends {id, lang, reasoning_tokens,
answer_tokens} to results/mgsm_token_split.jsonl. Resumable: skips (id, lang)
already in the output. Safety: stops if any /tokenize call takes over 1 s
(the server is shared with a running benchmark).
"""
import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "mgsm_raw.jsonl"
OUT = ROOT / "results" / "mgsm_token_split.jsonl"
URL = "http://127.0.0.1:8092/tokenize"
PAUSE = 0.2
MAX_CALL_S = 1.0


def count(text):
    if not text:
        return 0, 0.0
    time.sleep(PAUSE)
    t0 = time.monotonic()
    r = requests.post(URL, json={"content": text}, timeout=10)
    dt = time.monotonic() - t0
    r.raise_for_status()
    return len(r.json()["tokens"]), dt


def main():
    done = set()
    if OUT.exists():
        for line in OUT.open(encoding="utf-8"):
            try:
                rec = json.loads(line)
                done.add((rec["id"], rec["lang"]))
            except (json.JSONDecodeError, KeyError):
                pass
    recs = [json.loads(l) for l in RAW.open(encoding="utf-8") if l.strip()]
    todo = [r for r in recs if (r["id"], r["lang"]) not in done]
    print(f"{len(done)} done, {len(todo)} to tokenize", flush=True)
    slowest = 0.0
    for k, r in enumerate(todo, 1):
        rt, t1 = count(r.get("reasoning_content"))
        at, t2 = count(r.get("content"))
        slowest = max(slowest, t1, t2)
        if max(t1, t2) > MAX_CALL_S:
            sys.exit(f"stopping: /tokenize took {max(t1, t2):.2f} s at id={r['id']} {r['lang']}")
        with OUT.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"id": r["id"], "lang": r["lang"],
                                "reasoning_tokens": rt, "answer_tokens": at}) + "\n")
        if k % 100 == 0:
            print(f"{k}/{len(todo)} slowest call so far {slowest * 1000:.1f} ms", flush=True)
    print(f"done: {len(todo)} records; slowest call {slowest * 1000:.1f} ms", flush=True)


if __name__ == "__main__":
    main()
