# Lever 1: plain-reading system prompt (pre-registered plan)

Written 2026-10-01, **before any data**. The decision rule below is fixed and
is not changed after results come in.

## Hypothesis

`results/reasoning_gap_audit.md` found that the extra es reasoning on MGSM is
mostly the model doubting the meaning of correctly read Spanish wording and
weighing alternative readings (the main cost in 13 of the top 20 gaps). A
system prompt telling it to take words in their most common meaning
(`prompts/plain_reading.txt`) should shrink the es − en reasoning gap without
hurting accuracy. The prompt says nothing about answer language or length.

## Run

`scripts/run_lever1.sh` (guarded: refuses while any `run_*.py`, `chain_*.sh`
or `proxlite_gate.sh` is alive; `--dry-run` available):

1. `run_mgsm.py --langs en,es --system prompts/plain_reading.txt --tag plain`
   → `results/mgsm_raw.plain.jsonl`: 250 ids × en, es = 500 records. Same
   sampling as the baseline (temperature 1.0, top_p 0.95, top_k 20, seed 42,
   max_tokens 8192).
2. `score_mgsm.py --raw results/mgsm_raw.plain.jsonl --baseline results/mgsm_raw.jsonl --no-tokenize`
   → `results/lever1_score.txt`: accuracy, and paired baseline-vs-plain
   exact McNemar per language.
3. `mgsm_token_split.py --raw results/mgsm_raw.plain.jsonl`
   → `results/mgsm_token_split.plain.jsonl`: exact reasoning tokens via
   `/tokenize` (0.2 s apart, stops if a call takes over 1 s).

**en is the control:** the prompt must reduce the es-specific excess, not
just shorten reasoning everywhere.

## Baseline (from committed results)

| | en | es |
|---|---:|---:|
| accuracy (`mgsm_audit.md`, 250 ids) | 244/250 = 97.6% | 238/250 = 95.2% |
| mean reasoning tokens (`latency_breakdown.md`) | 228.1 | 342.4 |
| es − en reasoning gap (mean of per-id differences) | | **+114.4** |
| es / en reasoning ratio (diagnostic only) | | 1.50 |

## Decision rule (fixed)

**SUCCESS only if all three hold:**

- **(a) Gap halves.** The mean over the 250 ids of (es − en) reasoning tokens
  under the prompt, from `mgsm_token_split.plain.jsonl`, is **≤ 57** (half of
  the baseline 114.4, rounded down as specified).
- **(b) es accuracy holds.** On the 250 es ids, paired exact McNemar
  baseline vs plain gives **p > 0.05**, **and** es accuracy drops by at most
  1 point: **≥ 94.2%, i.e. ≥ 236/250 correct**.
- **(c) en accuracy holds.** en accuracy under the prompt is **not
  significantly lower** than the en baseline. This fails only if plain en
  accuracy < 97.6% **and** paired exact McNemar p ≤ 0.05.

Scoring as in `score_mgsm.py`: last number in `content` equals gold;
unparsed or truncated output counts as wrong. McNemar is the two-sided exact
test already used there.

**Otherwise lever 1 fails.** Record which criterion failed and by how much.
**No prompt-tuning loops:** no second prompt wording under lever 1.

Reported alongside, not part of the decision:
- mean en and es reasoning tokens, and the es/en ratio (the baseline is 1.50;
  shows whether the prompt mainly shortened both languages)
- median per-id gap
- paired Wilcoxon on per-id es − en differences
- finish_reason=length counts

### Known limitations

- Sampling is at temperature 1.0. Part of any baseline-vs-plain difference is
  run-to-run noise, and there is no repeat baseline to measure that noise
  floor. McNemar covers it for accuracy; criterion (a) does not.
- Criterion (a) uses an absolute token gap. A prompt that shortened all
  reasoning in proportion would also shrink it. The es/en ratio above is
  reported to show whether that happened, but it is not part of the rule.

## Timing

The guard keeps lever 1 from starting until Belebele, ProX-Lite (and its
gate) have all finished, so no earlier than the morning of 2026-10-02.

## Follow-up: does the reasoning gap appear with good translations?

After Belebele finishes (1464/1464; `run_belebele.py` exited), run the same
es − en reasoning-token comparison on `results/belebele_raw.jsonl`. Belebele's
passages are professional FLORES translations, unlike the MGSM translations
audited above.

- `mgsm_token_split.py --raw results/belebele_raw.jsonl` →
  `results/belebele_token_split.jsonl` (via `/tokenize`, 0.2 s apart, same
  1 s safeguard; about 2,900 calls, ~10 min). This may overlap the ProX-Lite
  generation run: `/tokenize` answered in 0.46 ms during a generation in the
  probe, and the slowest of 1,500 MGSM calls was 20.6 ms.
- Report the mean and median per-id es − en reasoning gap over the 488
  paired ids, the es/en ratio, and a paired Wilcoxon, next to MGSM's +114.4 /
  1.50.
- Interpretation:
  - A clearly smaller relative gap on Belebele points to translation quality
    as a driver of MGSM's gap.
  - A similar gap points to the language itself.
  - Belebele is multiple choice over a given passage, not arithmetic, so the
    task difference is a caveat for either reading.
