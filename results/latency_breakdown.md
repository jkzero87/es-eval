# MGSM latency breakdown (en / es / zh)

Source: `results/mgsm_raw.jsonl`, 750 records; 250 ids present in all three languages (all comparisons below are on these). Generated offline by `scripts/latency_breakdown.py`; no server requests.

## 1. Fields present

- top level: `id`, `lang`, `gold`, `content`, `reasoning_content`, `finish_reason`, `usage`, `timings`, `wall`
- `usage`: `completion_tokens`, `prompt_tokens`, `total_tokens`, `prompt_tokens_details` (`prompt_tokens_details.cached_tokens`)
- `timings`: `cache_n`, `prompt_n`, `prompt_ms`, `prompt_per_token_ms`, `prompt_per_second`, `predicted_n`, `predicted_ms`, `predicted_per_token_ms`, `predicted_per_second`, `draft_n`, `draft_n_accepted`
- every field above is present in all 750 records; `predicted_n == completion_tokens` in 750/750, `prompt_n + cache_n == prompt_tokens` in 750/750.
- **missing:** `usage.completion_tokens_details`, so the records carry no reasoning/answer token split. Exact counts were obtained separately: `scripts/mgsm_token_split.py` sent `reasoning_content` and `content` of every record to the server's `/tokenize` (no special tokens) → `results/mgsm_token_split.jsonl`. *Other* = completion − reasoning − answer (think tags, EOS, and any token-boundary effects).
- `prompt_ms` covers only the `prompt_n` tokens actually prefilled; the rest (`cache_n`) came from the prompt cache. `wall` (client-side) also includes HTTP/JSON and sampling time outside `prompt_ms + predicted_ms`, reported as *overhead*.
- `finish_reason=length` (hit max_tokens): id=120 es, id=215 es; kept in all numbers.

## 2. Per language (n = 250 paired ids; mean / median)

| metric | en | es | zh |
|---|---:|---:|---:|
| prompt tokens (total) | 89 / 85 | 101 / 97 | 81 / 78 |
| prompt tokens prefilled (not cached) | 88.5 / 85.0 | 100.4 / 96.5 | 80.6 / 77.5 |
| completion tokens | 405 / 352 | 559 / 419 | 490 / 366 |
|   reasoning (exact, /tokenize) | 228 / 166 | 342 / 199 | 313 / 182 |
|   final answer (exact, /tokenize) | 174 / 171 | 213 / 202 | 174 / 162 |
|   other (think tags, EOS) | 3.0 / 3.0 | 3.1 / 3.0 | 3.0 / 3.0 |
| final answer characters | 477 / 456 | 537 / 511 | 256 / 234 |
| prefill ms | 265 / 260 | 277 / 269 | 258 / 253 |
| generation ms | 6,821 / 5,757 | 9,799 / 7,122 | 8,515 / 6,018 |
| generation tokens/s (per record) | 59.92 / 60.19 | 58.23 / 58.32 | 58.51 / 58.67 |
| MTP acceptance (per record) | 0.852 / 0.859 | 0.818 / 0.822 | 0.823 / 0.825 |
| wall ms | 7,444 / 6,260 | 10,428 / 7,620 | 9,309 / 6,524 |
| overhead ms (wall − prefill − gen) | 358 / 207 | 352 / 206 | 536 / 208 |
| generation tokens/s (aggregate Σtokens/Σms) | 59.35 | 57.03 | 57.54 |
| MTP acceptance (Σaccepted/Σdrafted) | 0.839 | 0.794 | 0.802 |

## 3. Wall-time gap vs en, decomposed (means per item)

| component | es − en: ms | zh − en: ms | es: % of gap | zh: % of gap |
|---|---:|---:|---:|---:|
| (a) more completion tokens | 2,647 | 1,457 | 88.7 | 78.1 |
| (b) slower tokens/s | 331 | 237 | 11.1 | 12.7 |
| (c) prefill | 12 | -7 | 0.4 | -0.4 |
| (d) overhead (residual) | -6 | 178 | -0.2 | 9.6 |
| **total wall gap** | 2,984 | 1,865 | 100.0 | 100.0 |

(a) and (b) split the generation-time gap with the midpoint rule (see script docstring), so (a)+(b)+(c)+(d) equals the total exactly. A negative share means that component *reduces* the gap.

## 4. Paired Wilcoxon signed-rank on per-id generation tokens/s

| pair | n (non-zero) | median Δ tok/s (x − en) | W+ | W− | rank-biserial r | exact p | normal p |
|---|---:|---:|---:|---:|---:|---:|---:|
| es vs en | 250 | -1.81 | 4,975.0 | 26,400.0 | -0.683 | 2.23e-23 | 8.02e-21 |
| zh vs en | 250 | -1.22 | 7,902.0 | 23,473.0 | -0.496 | 2.57e-12 | 1.03e-11 |

Exact p computed by enumeration of the signed-rank distribution (doubled ranks, conditional on ties); the implementation reproduces the textbook n=15 example (W+=96, p=0.0413).

## 5. Completion-token gap vs en: reasoning vs final answer (means per item)

| | en | es | zh |
|---|---:|---:|---:|
| final answer tokens per character (Σ/Σ) | 0.3643 | 0.3974 | 0.6799 |

| component | es − en: tokens | zh − en: tokens | es: % of gap | zh: % of gap |
|---|---:|---:|---:|---:|
| reasoning | +114.4 | +85.0 | 74.3 | 99.8 |
| final answer | +39.5 | +0.2 | 25.7 | 0.2 |
|   … says more (more characters) | +22.7 | -115.5 | 14.7 | -135.7 |
|   … costs more per character (tokenizer) | +16.8 | +115.7 | 10.9 | 135.9 |
| other (think tags, EOS) | +0.1 | +0.0 | 0.0 | 0.0 |
| **total completion gap** | +153.9 | +85.1 | 100.0 | 100.0 |

The two answer sub-rows split the answer row with the midpoint rule on mean answer tokens = mean answer characters × aggregate tokens per character, so they add up exactly. For zh, characters are not comparable with Latin-script characters (one Hanzi carries roughly a word), so for zh the says-more / costs-more split is arithmetic, not a like-for-like verbosity measure.

## 6. Paired Wilcoxon signed-rank on per-id reasoning tokens

| pair | n (non-zero) | mean Δ | median Δ (x − en) | W+ | W− | rank-biserial r | exact p | normal p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| es vs en | 247 | +114.4 | +23.5 | 23,944.5 | 6,683.5 | +0.564 | 1.45e-15 | 1.61e-14 |
| zh vs en | 246 | +85.0 | +12.0 | 20,754.0 | 9,627.0 | +0.366 | 4.42e-07 | 6.37e-07 |

## Conclusion

- **Wall gap = longer outputs:** es is 2.98 s and zh 1.87 s slower per item than en; 89% / 78% of that is extra completion tokens, 11% / 13% slower decoding (lower MTP acceptance; per-id tok/s Wilcoxon p = 2.2e-23 / 2.6e-12); prefill ~0%.
- **The extra tokens are mostly reasoning:** of es's +154 completion tokens, 74% are reasoning (+114; per-id Wilcoxon exact p = 1.4e-15, r = +0.56) and 26% final answer (+40); for zh (+85) it is 100% reasoning (+85, p = 4.4e-07) and 0% answer (+0).
- **Answer part:** es says more (+60 characters, +23 tokens) and pays 0.397 vs 0.364 tokens per character (+17 tokens); zh's answers are -221 characters at 0.680 tokens/char (-116 / +116 tokens), not a like-for-like comparison.
