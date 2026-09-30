#!/usr/bin/env python3
"""Audit MGSM disagreements across en/es/zh (run on the complete file).

- For every id where at least one language is wrong: the en/es/zh questions
  (from the local HF cache, offline), gold, each language's parsed answer and
  correct flag, and the last 400 chars of each wrong content.
- Paired table on ids present in both languages: en right & es wrong,
  es right & en wrong, en right & zh wrong, zh right & en wrong, with the
  exact (binomial) McNemar p-value for es vs en and zh vs en.
- Writes results/mgsm_audit.md with a blank "cause" column
  (translation / model / ambiguous gold) per wrong (id, lang).

Uses the same correct() / last_number() as score_mgsm.py. No server calls.
"""
import argparse
import json
import os
import sys
import time
from math import comb
from pathlib import Path

os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from datasets import load_dataset

from score_mgsm import LANGS, correct, last_number

ROOT = Path(__file__).resolve().parents[1]
RAW_IN = ROOT / "results" / "mgsm_raw.jsonl"
MD_OUT = ROOT / "results" / "mgsm_audit.md"
EXPECTED = 750
TAIL = 400


def load_questions():
    # Same id scheme as run_mgsm.py: 1-based row index per language.
    return {lang: {i: row["question"] for i, row in
                   enumerate(load_dataset("juletxara/mgsm", lang, split="test"), start=1)}
            for lang in LANGS}


def mcnemar_exact(b, c):
    """Two-sided exact McNemar: binomial test of min(b, c) with n=b+c, p=0.5."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def fmt_num(x):
    if x is None:
        return "—"
    return str(int(x)) if float(x).is_integer() else str(x)


def md_cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=RAW_IN)
    ap.add_argument("--out", type=Path, default=MD_OUT)
    args = ap.parse_args()

    recs = {}
    with args.raw.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                recs[(r["id"], r["lang"])] = r
    n_rec = len(recs)
    partial = n_rec < EXPECTED
    status = f"PARTIAL ({n_rec}/{EXPECTED} records)" if partial else f"complete ({n_rec} records)"
    print(f"{args.raw.name}: {status}")
    if partial:
        print("WARNING: partial data; do not treat this audit as a final result.")

    questions = load_questions()
    ids = sorted({i for i, _ in recs})
    ok = {k: correct(r) for k, r in recs.items()}

    # --- side-by-side detail for ids with at least one wrong language
    wrong_ids = [i for i in ids if any((i, l) in recs and not ok[(i, l)] for l in LANGS)]
    detail_md = []
    for i in wrong_ids:
        gold = next(recs[(i, l)]["gold"] for l in LANGS if (i, l) in recs)
        print(f"\n{'=' * 100}\nid={i}  gold={fmt_num(gold)}")
        detail_md.append(f"### id={i} (gold {fmt_num(gold)})\n")
        detail_md.append("| lang | parsed | correct | question |\n|---|---|---|---|")
        for l in LANGS:
            if (i, l) not in recs:
                print(f"  [{l}] (not run yet)")
                detail_md.append(f"| {l} | — | not run | {md_cell(questions[l][i])} |")
                continue
            pred = last_number(recs[(i, l)].get("content") or "")
            flag = "✓" if ok[(i, l)] else "✗"
            print(f"  [{l}] parsed={fmt_num(pred)} correct={flag}  Q: {questions[l][i]}")
            detail_md.append(f"| {l} | {fmt_num(pred)} | {flag} | {md_cell(questions[l][i])} |")
        detail_md.append("")
        for l in LANGS:
            if (i, l) in recs and not ok[(i, l)]:
                r = recs[(i, l)]
                tail = (r.get("content") or "")[-TAIL:]
                print(f"  --- [{l}] finish={r.get('finish_reason')} last {TAIL} chars of content:\n{tail}")
                detail_md.append(f"**{l}** — finish_reason={r.get('finish_reason')}, last {TAIL} chars:\n")
                detail_md.append(f"~~~~\n{tail}\n~~~~\n")

    # --- paired table
    pairs = []
    print(f"\n{'=' * 100}\nPaired comparison vs en (ids run in both languages)")
    print(f"{'pair':<9} {'n':>4} {'both✓':>6} {'both✗':>6} {'en✓ x✗':>7} {'x✓ en✗':>7} {'McNemar p':>10}   ids(en✓ x✗) | ids(x✓ en✗)")
    for other in ("es", "zh"):
        common = [i for i in ids if (i, "en") in recs and (i, other) in recs]
        en_only = [i for i in common if ok[(i, "en")] and not ok[(i, other)]]
        other_only = [i for i in common if ok[(i, other)] and not ok[(i, "en")]]
        both_ok = sum(1 for i in common if ok[(i, "en")] and ok[(i, other)])
        both_bad = len(common) - both_ok - len(en_only) - len(other_only)
        p = mcnemar_exact(len(en_only), len(other_only))
        pairs.append((other, len(common), both_ok, both_bad, en_only, other_only, p))
        print(f"{other + ' vs en':<9} {len(common):>4} {both_ok:>6} {both_bad:>6} {len(en_only):>7} "
              f"{len(other_only):>7} {p:>10.4g}   {en_only} | {other_only}")

    # --- markdown
    md = [f"# MGSM audit — {status}", "",
          f"Generated {time.strftime('%Y-%m-%d %H:%M')} from `{args.raw.name}` by `scripts/audit_mgsm.py`.", ""]
    if partial:
        md += ["> **Partial data — not a final result.**", ""]
    md += ["## Paired comparison vs en", "",
           "| pair | n | both ✓ | both ✗ | en ✓ / other ✗ | other ✓ / en ✗ | exact McNemar p | ids en ✓ / other ✗ | ids other ✓ / en ✗ |",
           "|---|---|---|---|---|---|---|---|---|"]
    for other, n, both_ok, both_bad, en_only, other_only, p in pairs:
        md.append(f"| {other} vs en | {n} | {both_ok} | {both_bad} | {len(en_only)} | {len(other_only)} | "
                  f"{p:.4g} | {', '.join(map(str, en_only)) or '—'} | {', '.join(map(str, other_only)) or '—'} |")
    md += ["", "## Wrong answers — fill in `cause`", "",
           "cause: `translation` / `model` / `ambiguous gold`", "",
           "| id | lang | gold | parsed | en | es | zh | cause |",
           "|---|---|---|---|---|---|---|---|"]
    for i in wrong_ids:
        flags = {l: ("✓" if ok[(i, l)] else "✗") if (i, l) in recs else "—" for l in LANGS}
        for l in LANGS:
            if (i, l) in recs and not ok[(i, l)]:
                r = recs[(i, l)]
                md.append(f"| {i} | {l} | {fmt_num(r['gold'])} | {fmt_num(last_number(r.get('content') or ''))} | "
                          f"{flags['en']} | {flags['es']} | {flags['zh']} |  |")
    md += ["", "## Details", ""] + detail_md
    args.out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
