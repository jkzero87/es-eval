#!/usr/bin/env python3
"""ProX-Lite sample report (results/proxlite_sample.md): complete triplets only.

Offline: reads the raw file, the subset ids and the token split
(mgsm_token_split.py --raw results/proxlite_raw.jsonl). Scoring is
score_proxlite.correct (capped/unparsed = wrong), McNemar score_mgsm's.

PRIMARY (as pre-registered): per-language accuracy over the complete triplets,
paired exact McNemar es vs en and zh vs en, mean reasoning tokens and the
es/en, zh/en ratios. Also: records that hit the token cap (finish=length) per
language, with ids.
SECONDARY (sensitivity, not part of the plan): the same accuracy and McNemar
excluding every triplet where any language hit the cap.

Usage:
  .venv/bin/python scripts/proxlite_sample_report.py [--subset FILE] [--split FILE]
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_mgsm import mcnemar_exact  # noqa: E402
from score_proxlite import correct  # noqa: E402

R = Path(__file__).resolve().parents[1] / "results"
LANGS = ("en", "es", "zh")


def load(path):
    out = {}
    for line in path.open(encoding="utf-8"):
        if line.strip():
            rec = json.loads(line)
            out[(rec["id"], rec["lang"])] = rec
    return out


def accuracy_block(ids, raw, title):
    print(f"\n{title} ({len(ids)} triplets)")
    ok = {l: [correct(raw[(q, l)]) for q in ids] for l in LANGS}
    for l in LANGS:
        print(f"  {l}: {sum(ok[l])}/{len(ids)} = {sum(ok[l]) / len(ids):.1%}" if ids else f"  {l}: -")
    for l in ("es", "zh"):
        en_only = sum(a and not b for a, b in zip(ok["en"], ok[l]))
        l_only = sum(b and not a for a, b in zip(ok["en"], ok[l]))
        print(f"  {l} vs en: {l} − en = {(sum(ok[l]) - sum(ok['en'])) / max(len(ids), 1) * 100:+.1f} pts; "
              f"en✓ {l}✗ {en_only}, {l}✓ en✗ {l_only}; exact McNemar p = {mcnemar_exact(en_only, l_only):.3g}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw", type=Path, default=R / "proxlite_raw.jsonl")
    ap.add_argument("--subset", type=Path, default=R / "proxlite_subset_60_strat.txt")
    ap.add_argument("--split", type=Path, default=R / "proxlite_token_split.jsonl")
    args = ap.parse_args()

    raw = load(args.raw)
    subset = [int(x) for x in args.subset.read_text().split()]
    ids = [q for q in subset if all((q, l) in raw for l in LANGS)]
    print(f"ProX-Lite sample: {len(ids)}/{len(subset)} ids complete in en, es, zh "
          f"(incomplete, not scored: {[q for q in subset if q not in ids] or 'none'})")

    print("\nToken cap (finish=length, counted wrong in the primary score)")
    capped = {l: [q for q in ids if raw[(q, l)].get("finish_reason") == "length"] for l in LANGS}
    for l in LANGS:
        print(f"  {l}: {len(capped[l])}" + (f" (ids {capped[l]})" if capped[l] else ""))

    accuracy_block(ids, raw, "PRIMARY: accuracy, capped = wrong, as pre-registered")

    if args.split.exists():
        split = {k: r["reasoning_tokens"] for k, r in load(args.split).items()}
        have = [q for q in ids if all((q, l) in split for l in LANGS)]
        mean = {l: statistics.mean(split[(q, l)] for q in have) for l in LANGS}
        print(f"\nPRIMARY: reasoning tokens (exact, /tokenize), {len(have)} triplets")
        print("  mean: " + ", ".join(f"{l} {mean[l]:.1f}" for l in LANGS))
        print(f"  es/en ratio {mean['es'] / mean['en']:.3f}; zh/en ratio {mean['zh'] / mean['en']:.3f}")
    else:
        print(f"\n(no {args.split.name}: reasoning ratios not computed)")

    uncapped = [q for q in ids if not any(q in capped[l] for l in LANGS)]
    accuracy_block(uncapped, raw, "SECONDARY (sensitivity only, not pre-registered): excluding triplets "
                                  "where any language hit the cap")


if __name__ == "__main__":
    main()
