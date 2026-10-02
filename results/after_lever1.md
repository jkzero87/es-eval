# After lever 1: pre-registered decision tree

Written 2026-10-02 while lever 1 (`results/lever1_plan.md`) was still
generating (run started 15:30; at 15:43 it had 91/500 records), **before any
lever-1 score or verdict existed**. Nothing here was written from lever-1
results: no scoring, token split or decision had run, and only the raw file's
line count was checked (for progress). The commit hash and time are recorded in the commit that adds this file
and in the session report; `git log --format='%H %cI' -- results/after_lever1.md`
shows them against the later commit of `results/lever1_decision.txt`.

The branch is chosen mechanically from `results/lever1_decision.txt`
(criteria (a)–(d) as in `lever1_plan.md`). No branch is chosen on any other
ground.

## Rule that holds in every branch

**Accuracy must not drop.** In every follow-up run below, each language is
compared with its own baseline by paired exact McNemar (two-sided, as in the
scorers). A drop with **p ≤ 0.05** in **any** language is a **FAIL** of that
follow-up, whatever the reasoning-token numbers say. This is in addition to
the follow-up's own criteria.

## Branch 1: lever 1 PASSES (all of (a)–(d))

**Next: does it generalize?** Re-run the same prompt, unchanged
(`prompts/plain_reading.txt`), on **Belebele en + es**, the same 488 aligned
ids as the baseline (`results/belebele_raw.jsonl`), same sampling (temperature
1.0, top_p 0.95, top_k 20, seed 42, max_tokens 8192):

```sh
.venv/bin/python scripts/run_belebele.py --langs en,es --system prompts/plain_reading.txt --tag plain
.venv/bin/python scripts/score_belebele.py --raw results/belebele_raw.plain.jsonl --baseline results/belebele_raw.jsonl --no-tokenize
.venv/bin/python scripts/mgsm_token_split.py --raw results/belebele_raw.plain.jsonl --out results/belebele_token_split.plain.jsonl
```

Same four criteria, with Belebele's own baseline (`results/belebele_audit.md`):

| | baseline | criterion |
|---|---|---|
| (a) mean per-id es − en reasoning tokens | +113.5 | **≤ 56** (half, rounded down) |
| (b) es accuracy | 471/488 = 96.52% | McNemar p > 0.05 **and** ≥ 95.52%, i.e. **≥ 467/488** |
| (c) en accuracy | 479/488 = 98.16% | fails only if < 479/488 **and** McNemar p ≤ 0.05 |
| (d) es / en mean reasoning tokens | 1.49 | **≤ 1.25** |

SUCCESS (generalizes) only if all four hold. `lever1_decision.py` is
MGSM-specific (250 ids, MGSM scorer); a Belebele version (488 ids,
`score_belebele.correct`, the thresholds above) must be written and committed
**before** the Belebele run starts.

**Time**, from today's measured rates: lever 1 ran at ~8.4 s/record on MGSM
en+es, 0.94× the MGSM baseline's 8.9 s (en 7.4, es 10.4). Belebele's baseline
took 7.0 s (en) and 9.5 s (es) per record = 2.24 h for the 976 en+es records;
at 0.94× that is **≈ 2.1 h**, plus ~4 min token split (976 `/tokenize`
calls at 0.2 s spacing) and scoring: **≈ 2.2 h, up to ~2.5 h** if es
reasoning does not shorten. **It fits in one daytime session** (start by
~16:15 to end by 18:55). It does **not** fit after lever 1 today (lever 1
ends ~16:45; 16:45 + 2.2 h ≈ 19:00 > 18:55), so it would be the first run of
the next session.

## Branch 2: FAILS on (d) only ((a), (b), (c) pass; es/en > 1.25)

The gap shrank but in proportion to en: the prompt shortened reasoning in
general, not the Spanish-specific excess. **One** variant is allowed, written
here verbatim before any result, aimed at the Spanish-specific doubt
(translated wording read as a puzzle):

`prompts/plain_reading_v2.txt` (one line, exactly):

```
The question may be a translation, so some wording can sound unusual. Read it the way a fluent speaker would understand it on first reading, and take each word and phrase in its most common, everyday meaning. Do not stop to examine the wording, compare alternative readings or wonder what the original said. If something is truly ambiguous, pick the most common reading once and continue with it.
```

Like the first prompt, it says nothing about answer language or length.
It is run exactly as lever 1 (`run_mgsm.py --langs en,es --system
prompts/plain_reading_v2.txt --tag plain2`, same scoring, token split and
decision script with `--raw`/`--split` pointing at the `plain2` files) under
**the same rule (a)–(d)** against the same MGSM baseline, plus the
every-branch accuracy rule. Time ≈ 1.3 h (as lever 1).

**No further variants.** If v2 fails any criterion, lever 1 is closed and
Branch 3 applies.

## Branch 3: FAILS otherwise ((a), (b) or (c) fails, alone or with (d))

**Lever 1 is closed.** Next lever: **quantization comparison**,
`scripts/run_quant_compare.sh`, current production model
(Qwen3.8-27B-GSQ-RCO-IQ3_S, ~3.5 bits/weight, 12.1 GB) vs
**Qwen3.8-27B-UD-IQ4_XS** (~4.25 bits/weight, 14.3 GB), tag `q4`, all three
languages.

**What it measures:** whether the Spanish (and Chinese) deficit is partly a
quantization artifact. Per language: accuracy vs the IQ3_S baseline (paired
exact McNemar) and the es − en / zh − en reasoning-token gap and ratio. If
the es gap or the es accuracy deficit shrinks clearly at IQ4_XS while en
stays flat, lower-bit quantization hurts the non-English languages more; if
both quantizations show the same gap, the cause is upstream (model or
translations) and quantization is ruled out as a lever.

**Cost:** the script stops the :8092 server, starts IQ4_XS, runs the
benchmark in the foreground, then restores :8092 (~5–10 min of swaps).
Run **MGSM first** (750 records, all three languages): the IQ3_S baseline
took 1.89 h. IQ4_XS is 18% larger and has not been timed on this machine;
expect 1.0–1.3× the baseline time, so **≈ 2–2.5 h including swaps**: one
daytime window started by ~16:15. Belebele (1,464 records, baseline 3.29 h)
would be ≈ 3.5–4.5 h, a separate morning-to-afternoon window. ProX-Lite in
full is out of reach (≈ 8–11 h already at IQ3_S). The order and the decision
rule for the quantization comparison are to be pre-registered in their own
plan file before it runs.

## Not decided here

- ProX-Lite resumes in the remaining windows independently of the branch.
- Juan's review of the es audit causes is independent of the branch.
