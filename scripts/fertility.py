#!/usr/bin/env python3
"""Token fertility analysis for parallel datasets.

For every item in data/{source}_{lang}.jsonl:
  - POST {"content": text} to http://127.0.0.1:8092/tokenize, count tokens.
  - Count characters (all languages).
  - Count whitespace words (en/es only).
Write results/fertility.csv (source, field, id, lang, tokens, chars, words).
Print summary: total tokens per language per source; es/en and zh/en ratios
(total and median per item); 5 highest es/en-ratio items with their Spanish text.
"""
import csv
import json
import statistics
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
TOKENIZE_URL = "http://127.0.0.1:8092/tokenize"

SOURCES = ["belebele", "mgsm"]
LANGS = ["en", "es", "zh"]


def load_items(source, lang):
    """Yield (field, id, text) for each record.
    belebele: field='passage' (id int) and field='question' (id str).
    mgsm: field='question' (id int).
    """
    path = DATA_DIR / f"{source}_{lang}.jsonl"
    with path.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            rid = rec["id"]
            if source == "belebele":
                if isinstance(rid, int):
                    yield "passage", rid, rec["flores_passage"]
                else:
                    yield "question", rid, rec["question"]
            else:
                yield "question", rid, rec["question"]


def load_texts(source, lang):
    """Map id -> text for a source/lang (for reporting top items)."""
    return {rid: text for field, rid, text in load_items(source, lang)}


def tokenize(text):
    r = requests.post(TOKENIZE_URL, json={"content": text}, timeout=60)
    r.raise_for_status()
    return len(r.json()["tokens"])


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = RESULTS_DIR / "fertility.csv"

    # by_item[(source, field, id)] = {lang: tokens}
    by_item = {}
    total = 0
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["source", "field", "id", "lang", "tokens", "chars", "words"])
        for source in SOURCES:
            for lang in LANGS:
                for field, rid, text in load_items(source, lang):
                    total += 1
                    tokens = tokenize(text)
                    chars = len(text)
                    words = len(text.split()) if lang in ("en", "es") else 0
                    w.writerow([source, field, rid, lang, tokens, chars, words])
                    by_item.setdefault((source, field, rid), {})[lang] = tokens
        print(f"tokenized {total} items", file=sys.stderr)

    def fmt(x):
        return f"{x:.4f}"

    # Total tokens per (source, lang)
    total_tokens = {}
    for per_lang in by_item.values():
        for lang, toks in per_lang.items():
            total_tokens[lang] = total_tokens.get(lang, 0) + toks
    total_tokens_by_source = {}
    for (source, _field, _rid), per_lang in by_item.items():
        for lang, toks in per_lang.items():
            total_tokens_by_source[(source, lang)] = \
                total_tokens_by_source.get((source, lang), 0) + toks

    # Per-item ratios
    item_ratios = {("es", "en"): [], ("zh", "en"): []}
    for per_lang in by_item.values():
        en = per_lang.get("en")
        if not en:
            continue
        for a in ("es", "zh"):
            if a in per_lang:
                item_ratios[(a, "en")].append(per_lang[a] / en)

    print("\n=== Summary ===")
    print("\nTotal tokens per language per source:")
    for source in SOURCES:
        parts = ", ".join(f"{lang}: {total_tokens_by_source.get((source, lang), 0)}"
                          for lang in LANGS)
        print(f"  {source}: {parts}")
    print("\nRatios (es/en and zh/en):")
    for a in ("es", "zh"):
        key = (a, "en")
        rs = item_ratios[key]
        total_a = total_tokens.get(a, 0)
        total_en = total_tokens.get("en", 0)
        print(f"  {a}/en total: {fmt(total_a / total_en)}   "
              f"median per item: {fmt(statistics.median(rs))} ({len(rs)} items)")
    for source in SOURCES:
        for a in ("es", "zh"):
            ta = total_tokens_by_source.get((source, a), 0)
            tb = total_tokens_by_source.get((source, "en"), 0)
            if tb:
                print(f"  {source} {a}/en total: {fmt(ta / tb)}")

    # Top 5 items by es/en token ratio, with Spanish text
    top = []
    for (source, field, rid), per_lang in by_item.items():
        en = per_lang.get("en")
        es = per_lang.get("es")
        if en and es:
            top.append((source, field, rid, es / en, es))
    top.sort(key=lambda t: t[3], reverse=True)

    print("\nTop 5 items by es/en token ratio:")
    for source, field, rid, ratio, es_toks in top[:5]:
        texts = load_texts(source, "es")
        print(f"  [{source}/{field}/{rid}] ratio={fmt(ratio)} es_tokens={es_toks}")
        print(f"    es: {texts.get(rid)}")

    print(f"\nWrote {out_csv}")


if __name__ == "__main__":
    main()
