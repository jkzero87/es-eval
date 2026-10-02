#!/usr/bin/env python3
"""Belebele generalization decision (results/after_lever1.md, branch 1).

Offline: reads the Belebele baseline and treatment raw files plus the
treatment token split. Thresholds are the exact numbers in after_lever1.md:
  (a) mean per-id (es - en) reasoning tokens under the prompt <= 56
      (half of the baseline +113.5, rounded down)
  (b) es: paired exact McNemar baseline vs treatment p > 0.05 AND
      es accuracy >= 467/488 (baseline 471/488 minus 1 point)
  (c) en: fails only if accuracy < 479/488 (baseline) AND McNemar p <= 0.05
  (d) mean es / mean en reasoning tokens under the prompt <= 1.25
  (e) every branch: no language drops with McNemar p <= 0.05
SUCCESS needs all five. Scoring is score_belebele.py's, McNemar score_mgsm.py's.
Exit 0 with a verdict; exit 2 (no verdict) if any file lacks a paired record or
the baseline does not reproduce 479/488 en and 471/488 es.

Usage:
  .venv/bin/python scripts/belebele_decision.py --raw results/belebele_raw.plain.jsonl \
      --split results/belebele_token_split.plain.jsonl
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_belebele import correct  # noqa: E402
from score_mgsm import mcnemar_exact  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
N_IDS = 488
BASE_CORRECT = {"en": 479, "es": 471}  # results/belebele_audit.md
GAP_MAX = 56            # (a): half of the baseline +113.5, rounded down
ES_MIN = 467            # (b): >= 95.52% of 488 (96.52% - 1 point)
ALPHA = 0.05            # (b), (c), (e)
RATIO_MAX = 1.25        # (d): baseline 1.49


def load(path, key):
    out = {}
    for line in path.open(encoding="utf-8"):
        if line.strip():
            rec = json.loads(line)
            out[(rec["id"], rec["lang"])] = rec if key is None else rec[key]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--baseline", type=Path, default=R / "belebele_raw.jsonl")
    ap.add_argument("--raw", type=Path, default=R / "belebele_raw.plain.jsonl")
    ap.add_argument("--split", type=Path, default=R / "belebele_token_split.plain.jsonl")
    args = ap.parse_args()

    base, treat = load(args.baseline, None), load(args.raw, None)
    reas = load(args.split, "reasoning_tokens")
    ids = sorted({i for i, l in base if l == "en"})
    need = [(i, l) for i in ids for l in ("en", "es")]
    missing = {name: sum(k not in d for k in need)
               for name, d in (("baseline", base), ("treatment", treat), ("split", reas))}
    if len(ids) != N_IDS or any(missing.values()):
        print(f"NO VERDICT: {len(ids)} ids (expected {N_IDS}); missing paired records: {missing}")
        sys.exit(2)
    got_base = {lang: sum(correct(base[(i, lang)]) for i in ids) for lang in ("en", "es")}
    if got_base != BASE_CORRECT:
        print(f"NO VERDICT: baseline scores {got_base}, expected {BASE_CORRECT} (wrong baseline file?)")
        sys.exit(2)

    rows = []
    # (a) and (d): reasoning tokens under the prompt.
    en = [reas[(i, "en")] for i in ids]
    es = [reas[(i, "es")] for i in ids]
    gap = statistics.mean(b - a for a, b in zip(en, es))
    ratio = statistics.mean(es) / statistics.mean(en)
    rows.append(("a", f"es−en reasoning gap ≤ {GAP_MAX}", f"{gap:+.1f} tokens (baseline +113.5)", gap <= GAP_MAX))

    acc = {}
    for lang in ("en", "es"):
        b_ok = [correct(base[(i, lang)]) for i in ids]
        t_ok = [correct(treat[(i, lang)]) for i in ids]
        lost = sum(x and not y for x, y in zip(b_ok, t_ok))
        won = sum(y and not x for x, y in zip(b_ok, t_ok))
        acc[lang] = (sum(b_ok), sum(t_ok), lost, won, mcnemar_exact(lost, won))

    bk, tk, lost, won, p = acc["es"]
    rows.append(("b", f"es: McNemar p > {ALPHA} and ≥ {ES_MIN}/{N_IDS}",
                 f"{bk} → {tk}/{N_IDS} (lost {lost}, gained {won}, p = {p:.3g})", p > ALPHA and tk >= ES_MIN))

    bk, tk, lost, won, p = acc["en"]
    rows.append(("c", "en: not significantly lower",
                 f"{bk} → {tk}/{N_IDS} (lost {lost}, gained {won}, p = {p:.3g})", not (tk < bk and p <= ALPHA)))

    rows.append(("d", f"es/en reasoning ratio ≤ {RATIO_MAX}",
                 f"{ratio:.3f} (mean es {statistics.mean(es):.1f} / en {statistics.mean(en):.1f}; baseline 1.49)",
                 ratio <= RATIO_MAX))

    drops = [f"{lang} p = {a[4]:.3g}" for lang, a in acc.items() if a[1] < a[0] and a[4] <= ALPHA]
    rows.append(("e", "no significant accuracy drop (any lang)", "; ".join(drops) or "none", not drops))

    print("Belebele generalization decision (rule fixed in results/after_lever1.md)\n")
    print(f"{'':3} {'criterion':<40} {'result':<58} pass")
    for k, crit, res, ok in rows:
        print(f"({k}) {crit:<40} {res:<58} {'PASS' if ok else 'FAIL'}")
    failed = [k for k, *_, ok in rows if not ok]
    print("\nVERDICT: " + ("SUCCESS (a)-(e) all pass: the prompt generalizes to Belebele" if not failed
                          else f"FAIL on ({', '.join(failed)})"))


if __name__ == "__main__":
    main()
