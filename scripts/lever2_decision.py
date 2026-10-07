#!/usr/bin/env python3
"""Lever 2 decision (results/lever2_plan.md): PASS/FAIL on (T) and (A).

Offline: reads the baseline (mgsm_raw.jsonl), lever 1 (mgsm_raw.plain.jsonl)
and lever 2 (mgsm_raw.lever2.jsonl) raw files.
  (T) mean total tokens per question (sum of prompt + completion over the
      three calls) <= 1.10 x en baseline mean total
  (A) lever-2 es accuracy (step-3 Spanish answer) not significantly below the
      es baseline: fails only if lower AND paired exact McNemar p <= 0.05
Scoring: score_mgsm.py's last-number rule; unparsed or capped
(finish_reason == "length" in step 2 or 3) = wrong. The step-2 English
answer is scored too (reported, not decisive).
Also reported: mean tokens per call, ratio to the es baseline, wall time per
question, ids whose last number changed in translation (step 2 vs step 3),
and ids whose multiset of digit numbers changed in either translation.
Exit 0 with a verdict; exit 2 (no verdict) if any of the 250 ids is missing.

--partial: report on the ids done so far (baselines restricted to the same
ids; the (T) bar stays 1.10 x the 250-id en baseline). Prints no verdict:
a partial run is not the pre-registered decision.
"""
import argparse
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_mgsm import correct, last_number, mcnemar_exact  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
N_IDS = 250
T_FACTOR = 1.10
ALPHA = 0.05
STEPS = ("translate_in", "answer", "translate_out")


def load(path):
    return [json.loads(l) for l in path.open(encoding="utf-8") if l.strip()]


def tot(rec):
    u = rec.get("usage") or {}
    return u.get("prompt_tokens", 0) + u.get("completion_tokens", 0)


def numbers(text):
    """Multiset of numbers as score_mgsm normalises them (digits only)."""
    cleaned = re.sub(r"(?<=\d)[,.](?=\d{3}(?!\d))", "", text or "")
    cleaned = re.sub(r"(?<=\d),(?=\d)", ".", cleaned)
    return Counter(float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", cleaned))


def ok_step(rec, step_rec):
    return correct({"content": step_rec.get("content"), "gold": rec["gold"]})


def main():
    base = load(R / "mgsm_raw.jsonl")
    plain = load(R / "mgsm_raw.plain.jsonl")
    lv2 = {r["id"]: r for r in load(R / "mgsm_raw.lever2.jsonl")}
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--partial", action="store_true",
                    help="report on the ids done so far; no verdict")
    partial = ap.parse_args().partial
    all_ids = list(range(1, N_IDS + 1))
    ids = [i for i in all_ids if i in lv2] if partial else all_ids
    missing = [i for i in all_ids if i not in lv2]
    if missing and not partial:
        print(f"NO VERDICT: {len(lv2)}/{N_IDS} ids present; missing {len(missing)} "
              f"(first: {missing[:10]})")
        sys.exit(2)

    b = {(r["id"], r["lang"]): r for r in base}
    p = {(r["id"], r["lang"]): r for r in plain}

    def mean_tot(d, lang):
        return statistics.mean(tot(d[(i, lang)]) for i in ids)

    def acc(d, lang):
        return sum(correct(d[(i, lang)]) for i in ids)

    en_base_tot = mean_tot(b, "en")
    t_max = T_FACTOR * statistics.mean(tot(b[(i, "en")]) for i in all_ids)

    # Lever 2 per id.
    l2_tot = [lv2[i]["total_tokens"] for i in ids]
    per_call = {s: statistics.mean(tot(lv2[i][s]) for i in ids) for s in STEPS}
    capped = {i for i in ids
              if "length" in (lv2[i]["answer"]["finish_reason"], lv2[i]["translate_out"]["finish_reason"])}
    l2_ok = [ok_step(lv2[i], lv2[i]["translate_out"]) and i not in capped for i in ids]
    l2_en_ok = [ok_step(lv2[i], lv2[i]["answer"]) and lv2[i]["answer"]["finish_reason"] != "length"
                for i in ids]
    es_b_ok = [correct(b[(i, "es")]) for i in ids]
    lost = sum(x and not y for x, y in zip(es_b_ok, l2_ok))
    gained = sum(y and not x for x, y in zip(es_b_ok, l2_ok))
    pval = mcnemar_exact(lost, gained)

    mean_l2 = statistics.mean(l2_tot)
    T_pass = mean_l2 <= t_max
    A_fail = sum(l2_ok) < sum(es_b_ok) and pval <= ALPHA

    n = len(ids)
    if partial:
        print(f"Lever 2 PARTIAL: stopped early by decision at {n}/{N_IDS} (ids {ids[0]}-{ids[-1]}); "
              f"NOT the pre-registered verdict.\nBaselines below are restricted to the same {n} ids.\n")
    else:
        print("Lever 2 decision (rule fixed in results/lever2_plan.md)\n")
    print(f"{'':28}{'total tok/q':>12}{'× en base':>11}{'es acc':>10}")
    rows = [
        ("en baseline", en_base_tot, f"{acc(b, 'en')}/{n} (en)"),
        ("es baseline", mean_tot(b, "es"), f"{acc(b, 'es')}/{n}"),
        ("lever 1 es (plain prompt)", mean_tot(p, "es"), f"{acc(p, 'es')}/{n}"),
        ("lever 2 es (translate)", mean_l2, f"{sum(l2_ok)}/{n}"),
    ]
    for name, t, a in rows:
        print(f"{name:28}{t:12.1f}{t / en_base_tot:11.2f}{a:>14}")
    print(f"\nlever 2 per call (mean prompt+completion): "
          + ", ".join(f"{s} {per_call[s]:.1f}" for s in STEPS))
    print(f"lever 2 ratio to es baseline total: {mean_l2 / mean_tot(b, 'es'):.2f}")
    print(f"lever 2 step-2 English answer accuracy (not decisive): {sum(l2_en_ok)}/{n}")
    print(f"lever 2 capped (length in step 2 or 3): {len(capped)} {sorted(capped)}")
    print(f"lever 2 wall per question: mean {statistics.mean(lv2[i]['wall'] for i in ids):.1f}s, "
          f"median {statistics.median(lv2[i]['wall'] for i in ids):.1f}s")

    changed_last = [i for i in ids
                    if last_number(lv2[i]["answer"]["content"]) != last_number(lv2[i]["translate_out"]["content"])]
    changed_out = [i for i in ids
                   if numbers(lv2[i]["answer"]["content"]) != numbers(lv2[i]["translate_out"]["content"])]
    changed_in = [i for i in ids
                  if numbers(lv2[i]["question"]) != numbers(lv2[i]["translate_in"]["content"])]
    print(f"\nlast number changed in en→es translation (step 2 ≠ step 3): {len(changed_last)} {changed_last}")
    print(f"any digit number changed in en→es translation (multiset): {len(changed_out)} {changed_out}")
    print(f"any digit number changed in es→en translation (multiset): {len(changed_in)} {changed_in}")

    print(f"\n(T) mean total ≤ {t_max:.1f}: {mean_l2:.1f} "
          f"({mean_l2 / en_base_tot:.2f} × en baseline) → {'PASS' if T_pass else 'FAIL'}"
          + ("" if T_pass else f" (over by {mean_l2 - t_max:.1f} tokens, {mean_l2 / t_max - 1:+.0%})"))
    print(f"(A) es accuracy vs baseline: {sum(es_b_ok)} → {sum(l2_ok)}/{n} "
          f"(lost {lost}, gained {gained}, McNemar p = {pval:.3g}) → {'FAIL' if A_fail else 'PASS'}")
    if partial:
        print(f"\nNo verdict (partial). See results/translation_floor.md: even translate-in + "
              f"the en baseline answer is above {t_max:.1f}.")
        return
    failed = [c for c, f in (("T", not T_pass), ("A", A_fail)) if f]
    print(f"\nVERDICT: {'PASS' if not failed else 'FAIL on (' + ', '.join(failed) + ')'}")


if __name__ == "__main__":
    main()
