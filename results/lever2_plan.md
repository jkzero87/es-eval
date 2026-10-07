# Lever 2: translate-then-answer (pre-registered plan)

Written 2026-10-02 ~18:56, **before any lever-2 data** (no runner exists yet;
the run is tomorrow's first GPU job). Fix phase goal: a Spanish speaker should
not pay more tokens than an English speaker. The rule below is not changed
after results come in.

## Run (MGSM es, the 250 baseline ids, 27B on :8092, same server config)

For each id, three calls; total cost counts all three:
1. **Translate es → en**, thinking OFF (`chat_template_kwargs: {enable_thinking: false}`),
   temperature 0, max_tokens 1024. Prompt (user message, verbatim):
   `Translate the following math problem from Spanish to English. Output only the translation, nothing else.\n\n<question>`
2. **Answer in English** exactly like the en baseline: the en prompt of
   `run_mgsm.py` + the translated question; temperature 1.0, top_p 0.95,
   top_k 20, seed 42, max_tokens 8192, thinking as in the baseline.
3. **Translate the answer en → es**, thinking OFF, temperature 0,
   max_tokens 2048. Prompt (verbatim):
   `Translate the following answer from English to Spanish. Keep every number exactly as it is. Output only the translation, nothing else.\n\n<step-2 content>`

A runner (`scripts/run_lever2.py`, tag `lever2`, resumable, one JSON line per
id with the three calls' usage, contents and timings) must be written and
committed before the run. Before the 250 ids, one plumbing check on a
non-MGSM sentence confirms that thinking OFF returns no `reasoning_content`;
it is not part of the data.

## Metric

**Total tokens per question** = Σ over the calls of (prompt_tokens +
completion_tokens) from the server's `usage` (completion includes reasoning
and answer). Mean over the 250 ids. Baselines (one call each, computed
2026-10-02 from committed raw files, before any lever-2 data):

| | prompt | completion | **total** |
|---|---:|---:|---:|
| en baseline (`mgsm_raw.jsonl`) | 89.1 | 404.8 | **493.9** |
| es baseline (`mgsm_raw.jsonl`) | 100.8 | 558.8 | **659.6** (1.34 × en) |
| lever 1 en (`mgsm_raw.plain.jsonl`) | 147.1 | 413.7 | 560.8 |
| lever 1 es (`mgsm_raw.plain.jsonl`) | 158.8 | 522.5 | **681.3** (1.38 × en baseline) |

## Decision rule (fixed)

**PASS only if both hold:**
- **(T) Tokens:** mean total es-with-lever-2 ≤ **1.10 × 493.9 = 543.3**
  tokens per question (English baseline).
- **(A) Accuracy:** lever-2 es accuracy is **not significantly below** the es
  baseline (238/250): fails only if lower **and** paired exact McNemar
  p ≤ 0.05. Scored on the **final Spanish answer (step 3)** with the MGSM
  scorer (last number = gold; unparsed or capped = wrong). The step-2
  English answer is scored too, reported alongside, not decisive.

Otherwise FAIL; record which condition failed and by how much. No
prompt-tuning loops: the translation prompts above are the only ones.

**Lever 1 for comparison, same metric (from existing data):** es total 681.3
= 1.38 × English baseline (> 1.10: **would FAIL (T)**; the system prompt adds
~58 prompt tokens per call); es accuracy 239/250 vs 238/250, p = 1 (passes
(A)).

Reported alongside: mean tokens per call (translate in, answer, translate
out), ratio to the es baseline total, wall time per question, number of
answers whose numbers changed in translation (step-2 last number ≠ step-3
last number).

## Addendum 2026-10-07 16:21 (during the run, before the verdict; rule above unchanged)

Written while the lever-2 run was in progress (16 of 250 ids done, no
scoring run). The plan says "unparsed or capped = wrong" but does not say
which call's cap counts. `scripts/lever2_decision.py` applies: **a token-cap
hit (`finish_reason == "length"`) in step 2 (answer) or step 3 (translate
out) = wrong** for the decisive Spanish score; the step-2 English score
counts only a step-2 cap. Step 1 is not checked for a cap (a capped
translation would show up as a wrong answer anyway). This is the one rule
not in the original text. It does not move the baseline: the es baseline's
two capped answers (ids 120, 215) are already wrong under the last-number
rule, so 238/250 is unchanged.

Extra, reported only (not decisive): besides the plan's "step-2 last number
≠ step-3 last number", the script also lists ids whose multiset of digit
numbers changed in either translation (es→en question, en→es answer).
