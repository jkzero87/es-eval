#!/usr/bin/env python3
"""Score MGSM results from results/mgsm_raw.jsonl (runnable mid-run).

- correct = last number in content equals gold (commas/dots stripped as
  thousands separators).
- lingua detection of content and reasoning_content (en/es/zh/other).
- Reasoning tokens counted via POST /tokenize.
- Per language: n, accuracy, median completion tokens, median reasoning
  tokens, median predicted_per_second, MTP acceptance (sum accepted /
  sum drafted), % finish_reason=length, prompt-lang x reasoning-lang matrix.
- From results/fertility.csv: per source, chars ratio es/en and
  tokens-per-char es vs en (splits 1.27 into translation vs tokenizer).
"""
import csv
import json
import re
import statistics
import sys
from pathlib import Path

import requests
from lingua import LanguageDetectorBuilder

ROOT = Path(__file__).resolve().parents[1]
RAW_IN = ROOT / "results" / "mgsm_raw.jsonl"
FERT_IN = ROOT / "results" / "fertility.csv"
TOKENIZE_URL = "http://127.0.0.1:8092/tokenize"
LANGS = ["en", "es", "zh"]
DETECT_COLS = ["en", "es", "zh", "other", "none"]

_detector = LanguageDetectorBuilder.from_all_languages().build()


def detect(text):
    if not text or not text.strip():
        return "none"
    lang = _detector.detect_language_of(text)
    if lang is None:
        return "other"
    code = lang.iso_code_639_1.name.lower()
    return code if code in LANGS else "other"


def last_number(text):
    if not text:
        return None
    # "," or "." followed by exactly 3 digits = thousands separator (1,234 / 1.234);
    # a remaining "," between digits is a decimal comma (1,5).
    cleaned = re.sub(r"(?<=\d)[,.](?=\d{3}(?!\d))", "", text)
    cleaned = re.sub(r"(?<=\d),(?=\d)", ".", cleaned)
    nums = re.findall(r"-?\d+(?:\.\d+)?", cleaned)
    return float(nums[-1]) if nums else None


def correct(record):
    pred = last_number(record.get("content") or "")
    gold = record.get("gold")
    return pred is not None and gold is not None and abs(pred - float(gold)) < 1e-9


def main():
    if not RAW_IN.exists():
        print(f"no {RAW_IN} yet", file=sys.stderr)
        sys.exit(1)

    records = []
    with RAW_IN.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    print(f"scored {len(records)} records so far")

    # --- per-language aggregates ---
    per_lang = {l: {
        "n": 0, "correct": 0, "completion_tokens": [], "reasoning_tokens": [],
        "pps": [], "drafted": 0, "accepted": 0, "length": 0,
        "reasoning_lang": {}, "content_lang": {},
    } for l in LANGS}

    for rec in records:
        l = rec["lang"]
        bucket = per_lang[l]
        bucket["n"] += 1
        if correct(rec):
            bucket["correct"] += 1
        usage = rec.get("usage") or {}
        if "completion_tokens" in usage:
            bucket["completion_tokens"].append(usage["completion_tokens"])
        tt = rec.get("timings") or {}
        if tt.get("predicted_per_second") is not None:
            bucket["pps"].append(tt["predicted_per_second"])
        if tt.get("draft_n") is not None:
            bucket["drafted"] += tt["draft_n"]
        if tt.get("draft_n_accepted") is not None:
            bucket["accepted"] += tt["draft_n_accepted"]
        if rec.get("finish_reason") == "length":
            bucket["length"] += 1
        rl = detect(rec.get("reasoning_content"))
        bucket["reasoning_lang"][rl] = bucket["reasoning_lang"].get(rl, 0) + 1
        cl = detect(rec.get("content"))
        bucket["content_lang"][cl] = bucket["content_lang"].get(cl, 0) + 1
        rc = rec.get("reasoning_content")
        if rc and rc.strip():
            try:
                r = requests.post(TOKENIZE_URL, json={"content": rc}, timeout=60)
                r.raise_for_status()
                bucket["reasoning_tokens"].append(len(r.json()["tokens"]))
            except Exception as e:
                print(f"  tokenize failed for id={rec['id']} {l}: {e}", file=sys.stderr)

    def med(xs):
        return statistics.median(xs) if xs else float("nan")

    print("\n=== Per language ===")
    header = (f"{'lang':<5} {'n':>4} {'acc':>7} {'med_compl':>10} {'med_reas_tk':>12} "
              f"{'med_pps':>9} {'mtp_acc':>9} {'%length':>8}")
    print(header)
    for l in LANGS:
        b = per_lang[l]
        acc = b["correct"] / b["n"] if b["n"] else float("nan")
        mtp = (b["accepted"] / b["drafted"]) if b["drafted"] else float("nan")
        pct_len = 100.0 * b["length"] / b["n"] if b["n"] else float("nan")
        print(f"{l:<5} {b['n']:>4} {acc:>7.4f} {med(b['completion_tokens']):>10.0f} "
              f"{med(b['reasoning_tokens']):>12.0f} {med(b['pps']):>9.2f} "
              f"{mtp:>9.4f} {pct_len:>8.1f}")

    for field, title in (("reasoning_lang", "reasoning_content"), ("content_lang", "content")):
        print(f"\n=== prompt-language x detected language of {title} ===")
        print(f"{'prompt':<8} " + "".join(f"{c:>8}" for c in DETECT_COLS))
        for l in LANGS:
            row = per_lang[l][field]
            print(f"{l:<8} " + "".join(f"{row.get(c, 0):>8}" for c in DETECT_COLS))

    # --- fertility split ---
    if FERT_IN.exists():
        agg = {}
        with FERT_IN.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = (row["source"], row["lang"])
                agg.setdefault(key, {"tokens": 0, "chars": 0})
                agg[key]["tokens"] += int(row["tokens"])
                agg[key]["chars"] += int(row["chars"])
        print("\n=== fertility split (es/en: longer translation vs tokenizer) ===")
        for source in sorted({k[0] for k in agg}):
            en = agg.get((source, "en"))
            es = agg.get((source, "es"))
            if not en or not es:
                continue
            char_ratio = es["chars"] / en["chars"]
            tpc_en = en["tokens"] / en["chars"]
            tpc_es = es["tokens"] / es["chars"]
            tok_ratio = es["tokens"] / en["tokens"]
            print(f"  {source}: chars es/en={char_ratio:.4f}  "
                  f"tokens/char en={tpc_en:.4f} es={tpc_es:.4f} "
                  f"({'+' if tpc_es >= tpc_en else '-'}{100 * (tpc_es / tpc_en - 1):.2f}%)  "
                  f"tokens es/en={tok_ratio:.4f}  "
                  f"(char factor {char_ratio:.4f} x tok/char factor {tpc_es / tpc_en:.4f} = {char_ratio * tpc_es / tpc_en:.4f})")
    else:
        print(f"\nno {FERT_IN}, skipping fertility split")


if __name__ == "__main__":
    main()
