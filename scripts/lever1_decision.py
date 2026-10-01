#!/usr/bin/env python3
"""Lever 1 decision (results/lever1_plan.md): pass/fail for (a)-(d) and verdict.

Offline: reads the baseline and plain raw files plus the plain token split.
  (a) mean per-id (es - en) reasoning tokens under the prompt <= 57
  (b) es: paired exact McNemar baseline vs plain p > 0.05 AND
      es accuracy >= baseline - 1 point (>= 236/250)
  (c) en: fails only if plain accuracy < baseline AND McNemar p <= 0.05
  (d) mean es / mean en reasoning tokens under the prompt <= 1.25
SUCCESS needs all four. Scoring and McNemar are score_mgsm.py's.
Exit 0 with a verdict; exit 2 (no verdict) if any file lacks a paired record.
"""
import argparse
import json
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_mgsm import correct, mcnemar_exact  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
N_IDS = 250
GAP_MAX = 57            # (a): half of the baseline 114.4, rounded down as specified
ES_DROP_MAX_PT = 1.0    # (b): at most 1 accuracy point lower
ALPHA = 0.05            # (b), (c)
RATIO_MAX = 1.25        # (d): baseline 1.50


def load(path, key):
    out = {}
    for line in path.open(encoding="utf-8"):
        if line.strip():
            rec = json.loads(line)
            out[(rec["id"], rec["lang"])] = rec if key is None else rec[key]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--baseline", type=Path, default=R / "mgsm_raw.jsonl")
    ap.add_argument("--raw", type=Path, default=R / "mgsm_raw.plain.jsonl")
    ap.add_argument("--split", type=Path, default=R / "mgsm_token_split.plain.jsonl")
    args = ap.parse_args()

    base, plain = load(args.baseline, None), load(args.raw, None)
    reas = load(args.split, "reasoning_tokens")
    ids = sorted({i for i, l in base if l == "en"})
    need = [(i, l) for i in ids for l in ("en", "es")]
    missing = {name: sum(k not in d for k in need)
               for name, d in (("baseline", base), ("plain", plain), ("split", reas))}
    if len(ids) != N_IDS or any(missing.values()):
        print(f"NO VERDICT: {len(ids)} ids (expected {N_IDS}); missing paired records: {missing}")
        sys.exit(2)

    rows = []
    # (a) and (d): reasoning tokens under the prompt.
    en = [reas[(i, "en")] for i in ids]
    es = [reas[(i, "es")] for i in ids]
    gap = statistics.mean(b - a for a, b in zip(en, es))
    ratio = statistics.mean(es) / statistics.mean(en)
    rows.append(("a", "es−en reasoning gap ≤ 57", f"{gap:+.1f} tokens (baseline +114.4)", gap <= GAP_MAX))

    acc = {}
    for lang in ("en", "es"):
        b_ok = [correct(base[(i, lang)]) for i in ids]
        p_ok = [correct(plain[(i, lang)]) for i in ids]
        lost = sum(x and not y for x, y in zip(b_ok, p_ok))
        won = sum(y and not x for x, y in zip(b_ok, p_ok))
        acc[lang] = (sum(b_ok), sum(p_ok), lost, won, mcnemar_exact(lost, won))

    bk, pk, lost, won, p = acc["es"]
    min_es = math.ceil((100 * bk / N_IDS - ES_DROP_MAX_PT) / 100 * N_IDS - 1e-9)
    ok_b = p > ALPHA and pk >= min_es
    rows.append(("b", f"es: McNemar p > {ALPHA} and ≥ {min_es}/{N_IDS}",
                 f"{bk} → {pk}/{N_IDS} (lost {lost}, gained {won}, p = {p:.3g})", ok_b))

    bk, pk, lost, won, p = acc["en"]
    ok_c = not (pk < bk and p <= ALPHA)
    rows.append(("c", "en: not significantly lower",
                 f"{bk} → {pk}/{N_IDS} (lost {lost}, gained {won}, p = {p:.3g})", ok_c))

    rows.append(("d", "es/en reasoning ratio ≤ 1.25",
                 f"{ratio:.3f} (mean es {statistics.mean(es):.1f} / en {statistics.mean(en):.1f}; baseline 1.50)",
                 ratio <= RATIO_MAX))

    print("Lever 1 decision (rule fixed in results/lever1_plan.md)\n")
    print(f"{'':3} {'criterion':<34} {'result':<58} pass")
    for k, crit, res, ok in rows:
        print(f"({k}) {crit:<34} {res:<58} {'PASS' if ok else 'FAIL'}")
    failed = [k for k, *_, ok in rows if not ok]
    print("\nVERDICT: " + ("SUCCESS (a)-(d) all pass" if not failed
                          else f"FAIL: lever 1 fails on ({', '.join(failed)}); no prompt-tuning loops"))


if __name__ == "__main__":
    main()
