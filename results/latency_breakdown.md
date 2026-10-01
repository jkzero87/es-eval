# MGSM latency breakdown (en / es / zh)

Source: `results/mgsm_raw.jsonl`, 750 records; 250 ids present in all three languages (all comparisons below are on these). Generated offline by `scripts/latency_breakdown.py`; no server requests.

## 1. Fields present

- top level: `id`, `lang`, `gold`, `content`, `reasoning_content`, `finish_reason`, `usage`, `timings`, `wall`
- `usage`: `completion_tokens`, `prompt_tokens`, `total_tokens`, `prompt_tokens_details` (`prompt_tokens_details.cached_tokens`)
- `timings`: `cache_n`, `prompt_n`, `prompt_ms`, `prompt_per_token_ms`, `prompt_per_second`, `predicted_n`, `predicted_ms`, `predicted_per_token_ms`, `predicted_per_second`, `draft_n`, `draft_n_accepted`
- every field above is present in all 750 records; `predicted_n == completion_tokens` in 750/750, `prompt_n + cache_n == prompt_tokens` in 750/750.
- **missing:** `usage.completion_tokens_details`. There is no reasoning/answer token split. Exact counts would need `/tokenize` (excluded: no server requests) or an offline tokenizer (the local `llama-tokenize` build segfaults in vocab-only mode with the GPU hidden; no Python tokenizer is installed). The split below is an **estimate**: each record's completion tokens divided by the character share of `reasoning_content` vs `content`.
- `prompt_ms` covers only the `prompt_n` tokens actually prefilled; the rest (`cache_n`) came from the prompt cache. `wall` (client-side) also includes HTTP/JSON and sampling time outside `prompt_ms + predicted_ms`, reported as *overhead*.
- `finish_reason=length` (hit max_tokens): id=120 es, id=215 es; kept in all numbers.

## 2. Per language (n = 250 paired ids; mean / median)

| metric | en | es | zh |
|---|---:|---:|---:|
| prompt tokens (total) | 89 / 85 | 101 / 97 | 81 / 78 |
| prompt tokens prefilled (not cached) | 88.5 / 85.0 | 100.4 / 96.5 | 80.6 / 77.5 |
| completion tokens | 405 / 352 | 559 / 419 | 490 / 366 |
|   reasoning (est., char share) | 231 / 168 | 357 / 211 | 370 / 232 |
|   final answer (est., char share) | 174 / 171 | 202 / 196 | 120 / 110 |
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

## Conclusion

- **es vs en:** 2.98 s slower per item on average; 89% of it is 154 more completion tokens, 11% slower generation (57.0 vs 59.4 tok/s, alongside lower MTP acceptance 0.794 vs 0.839), prefill ~0%, overhead ~0%.
- **zh vs en:** 1.87 s slower; 78% tokens (85 more), 13% speed (57.5 vs 59.4 tok/s), prefill ~0%, overhead 10% (two warm-up outliers at the start of the run, ids 7–8 at 37–44 s; every language has two such outliers among ids 7–9, and the medians match). Prefill barely matters because prompts are short (~90 tokens, ~0.27 s), not because of caching.
- **Per-id tokens/s is lower in both** (es − en median -1.81 tok/s, Wilcoxon exact p = 2.2e-23, r = -0.68; zh − en -1.22, p = 2.6e-12), but it is the second-order effect: the gap is mostly longer outputs, not slower decoding.
