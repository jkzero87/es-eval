# Lever 1 result (2026-10-02)

Run 15:30–16:48 as pre-registered (`results/lever1_plan.md`, unchanged):
MGSM en + es, 250 ids each, `prompts/plain_reading.txt`, tag `plain`.
Decision computed by `scripts/lever1_decision.py` (`results/lever1_decision.txt`).

| | criterion | result | |
|---|---|---|---|
| (a) | es−en reasoning gap ≤ 57 | +82.5 tokens (baseline +114.4) | **FAIL** |
| (b) | es: McNemar p > 0.05 and ≥ 236/250 | 238 → 239/250 (lost 3, gained 4, p = 1) | PASS |
| (c) | en: not significantly lower | 244 → 245/250 (lost 1, gained 2, p = 1) | PASS |
| (d) | es/en reasoning ratio ≤ 1.25 | 1.338 (es 326.5 / en 244.0; baseline 1.50) | **FAIL** |
| all branches (`after_lever1.md`) | no language drops with p ≤ 0.05 | none (en +1, es +1; p = 1 both) | PASS |

**VERDICT: FAIL on (a) and (d). Lever 1 is closed.**

Branch of `results/after_lever1.md` (pushed 15:52:48, before this result):
**branch 3**, since (a) failed as well as (d) (branch 2 requires (d) to be the
only failure). No prompt variant is run. Next lever: quantization comparison
(`run_quant_compare.sh`, IQ3_S vs IQ4_XS, MGSM first), to be pre-registered in
its own plan before it runs.

Reported alongside (not part of the decision): median per-id es − en gap
+27.5 tokens (baseline +23.5); finish_reason=length 0/500. Paired Wilcoxon
not computed (scipy is not installed in the venv). The prompt shrank the gap by
28% and the ratio from 1.50 to 1.34 without hurting accuracy, but by less than
the pre-registered thresholds.
