#!/usr/bin/env python3
"""Audit Belebele results (results/belebele_raw.jsonl, complete file). Offline.

Prints per language: accuracy, % unparsed, mean completion tokens, mean wall
time, and the share of reasoning_content detected as English; and paired
en-vs-es / en-vs-zh counts with exact McNemar p. Correctness is
score_belebele.py's (last standalone A-D letter in content). As a parser
check, it also takes the letter right after the last 'Answer:' /
'Respuesta:' / '答案：' marker and flags items where the two disagree.

Writes results/belebele_audit.md: every (id, lang) with en right and es or zh
wrong, with the passage start, question and options in en and that language,
gold, both parses, the tail of the wrong answer, and a blank cause column
(translation / model / ambiguous gold / parser) to fill in by hand.
"""
import argparse
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_belebele import load_items  # noqa: E402  (offline: data/ + HF cache)
from score_belebele import correct, last_letter  # noqa: E402
from score_mgsm import detect, mcnemar_exact  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW_IN = ROOT / "results" / "belebele_raw.jsonl"
MD_OUT = ROOT / "results" / "belebele_audit.md"
LANGS = ["en", "es", "zh"]
MARKER_RE = re.compile(r"(?:(?i:answer|respuesta)|答案)\s*(?:\*\*|__)?\s*[:：]\s*(?:\*\*|__)?\s*\(?([A-D])(?![A-Za-z])")


def marker_letter(text):
    m = MARKER_RE.findall(text or "")
    return m[-1] if m else None


def cell(text, n=None):
    text = " ".join((text or "").split())
    if n and len(text) > n:
        text = text[:n] + "…"
    return text.replace("|", "\\|")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw", type=Path, default=RAW_IN)
    ap.add_argument("--out", type=Path, default=MD_OUT)
    args = ap.parse_args()

    recs = {}
    for line in args.raw.open(encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            recs[(r["id"], r["lang"])] = r
    ids = sorted({i for i, _ in recs if all((i, l) in recs for l in LANGS)})
    ok = {k: correct(r) for k, r in recs.items()}

    lines = [f"{len(recs)} records, {len(ids)} ids with all three languages\n",
             f"{'lang':<5} {'n':>4} {'acc':>7} {'%unparsed':>10} {'mean_compl':>11} {'mean_wall_s':>12} "
             f"{'%reas_en':>9} {'parse_disagree':>15}"]
    stats = {}
    for l in LANGS:
        rs = [recs[(i, l)] for i in ids]
        n = len(rs)
        acc = sum(ok[(i, l)] for i in ids) / n
        unparsed = sum(last_letter(r.get("content")) is None for r in rs)
        compl = statistics.mean((r.get("usage") or {}).get("completion_tokens", 0) for r in rs)
        wall = statistics.mean(r["wall"] for r in rs)
        reas_en = sum(detect(r.get("reasoning_content")) == "en" for r in rs)
        disagree = [r["id"] for r in rs if marker_letter(r.get("content")) not in (None, last_letter(r.get("content")))]
        stats[l] = dict(n=n, acc=acc, unparsed=unparsed, compl=compl, wall=wall, reas_en=reas_en, disagree=disagree)
        lines.append(f"{l:<5} {n:>4} {acc:>7.4f} {100 * unparsed / n:>10.1f} {compl:>11.0f} {wall:>12.2f} "
                     f"{100 * reas_en / n:>9.1f} {len(disagree):>15}")
    lines.append("")
    lines.append(f"{'pair':<9} {'n':>4} {'both✓':>6} {'both✗':>6} {'en✓ x✗':>7} {'x✓ en✗':>7} {'McNemar p':>10}")
    pairs = {}
    for x in ("es", "zh"):
        en_only = [i for i in ids if ok[(i, "en")] and not ok[(i, x)]]
        x_only = [i for i in ids if ok[(i, x)] and not ok[(i, "en")]]
        both = sum(ok[(i, "en")] and ok[(i, x)] for i in ids)
        p = mcnemar_exact(len(en_only), len(x_only))
        pairs[x] = (en_only, x_only, p)
        lines.append(f"{x + ' vs en':<9} {len(ids):>4} {both:>6} {len(ids) - both - len(en_only) - len(x_only):>6} "
                     f"{len(en_only):>7} {len(x_only):>7} {p:>10.4g}")
    report = "\n".join(lines)
    print(report)

    items = load_items()
    md = ["# Belebele audit: en right, es or zh wrong", "",
          f"Generated from `{args.raw.name}` by `scripts/audit_belebele.py` (offline). Correct = "
          "last standalone A–D letter in `content` (`score_belebele.py`); *marker* = letter after the "
          "last 'Answer:' / 'Respuesta:' / '答案：'.", "",
          "## Summary", "", "```", report, "```", "",
          "## Items (en ✓, other language ✗)", "",
          "cause: `translation` / `model` / `ambiguous gold` / `parser`", "",
          "| id | lang | gold | parsed | marker | question (en) | question (lang) | cause |",
          "|---|---|---|---|---|---|---|---|"]
    detail = ["", "## Item details", ""]
    for x in ("es", "zh"):
        for i in pairs[x][0]:
            r = recs[(i, x)]
            it_en, it_x = items["en"][i], items[x][i]
            md.append(f"| {i} | {x} | {r['gold']} | {last_letter(r.get('content')) or '—'} | "
                      f"{marker_letter(r.get('content')) or '—'} | {cell(it_en['question'])} | "
                      f"{cell(it_x['question'])} |  |")
            detail += [f"### id={i} {x} (gold {r['gold']}; parsed {last_letter(r.get('content')) or '—'}; "
                       f"marker {marker_letter(r.get('content')) or '—'}; qid `{it_en['qid']}`)", "",
                       f"- **en passage (start):** {cell(it_en['passage'], 600)}",
                       f"- **{x} passage (start):** {cell(it_x['passage'], 600)}",
                       f"- **en question:** {cell(it_en['question'])}",
                       f"- **{x} question:** {cell(it_x['question'])}",
                       "- **options en / " + x + ":** " + "; ".join(
                           f"{L}) {cell(a)} / {cell(b)}" for L, a, b in zip("ABCD", it_en["options"], it_x["options"])),
                       f"- **{x} answer (last 400 chars):** {cell((r.get('content') or '')[-400:])}",
                       f"- **{x} reasoning (last 600 chars):** {cell((r.get('reasoning_content') or '')[-600:])}",
                       ""]
    args.out.write_text("\n".join(md + detail) + "\n", encoding="utf-8")
    print(f"\nwrote {args.out.relative_to(ROOT)}: "
          + ", ".join(f"{len(pairs[x][0])} en✓/{x}✗" for x in ("es", "zh")))


if __name__ == "__main__":
    main()
