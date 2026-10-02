# ProX-Lite sample for 2026-10-02 (written before the run)

Replaces earlier ProX-Lite orders (full run; `--limit N --keep-done`).

## The 60 ids (`results/proxlite_subset_60_strat.txt`), each in en, es and zh = 180 records

75 76 78 84 119 127 131 137 154 162 170 181 194 199 205 213 215 235 236 239 247 261 271 290 295 311 325 331 338 347 369 372 383 391 402 425 428 438 443 445 454 459 475 480 510 518 535 539 540 548 553 572 581 588 602 636 644 651 654 655 

## How they were chosen

- **Size:** the request was 100 questions. At the measured ProX-Lite rate
  (mean 34.2 s/record over the 98 records of 2026-10-01; median 15.8 s, heavy
  tail up to 303 s) about 190 records fit between ~17:05 and 18:50, and a
  properly stratified 100 would need ~279 new records (≈ 2.7 h). Juan chose
  **N = 60** (2026-10-02, ~16:55).
- **Stratified:** per-category allocation by `stratified_subset(items, 60)`
  in `run_proxlite.py` (proportional to category size, largest remainder, at
  least 1 each): biology 4, business 4, chemistry 6, computer science 2,
  economics 4, engineering 5, health 3, history 2, law 5, math 7, other 5,
  philosophy 2, physics 7, psychology 4.
- **Reuse:** the 32 finished triplets (ids 70–101) are all **business**, so
  `--keep-done` would have made business 32% of a 100 sample (proportional:
  7%). Instead, finished ids are reused only up to their category's quota:
  4 of the 32 business ids, drawn with `random.Random(42)` (75, 76, 78, 84);
  the partial id 102 (en, es) did not fit. The other categories are sampled
  with the same generator, in sorted category order. Reused: 12 records;
  new: **168 records**. Selection used only ids and categories, no results.
- **Run:** `run_proxlite.py --ids results/proxlite_subset_60_strat.txt`
  (new `--ids FILE` option) on the main file `results/proxlite_raw.jsonl`,
  same model, prompts and sampling as the baseline. Expected ≈ 1.6–1.8 h at
  35–38 s/record (8093 on CPU slows the 27B ~8% only while it is generating:
  61.3 → 56.3 tok/s, measured 17:01). `stop_at.sh 18:55` as backstop.
- **Scoring:** complete triplets only; accuracy per language with exact
  McNemar vs en; es/en and zh/en reasoning-token ratios.

## Honest limit: what n = 60 can show

Exact McNemar (two-sided, α = 0.05) needs at least 6 discordant pairs all in
one direction, so **no observed es−en gap under 10 points (6/60) can be
significant**. Power depends on the es−en discordance rate; the only ProX-Lite
baseline is 2/32 = 6.25% discordant (es vs en; both en-only), and Belebele's
is 14/488 = 2.9%:

| discordance rate | largest possible gap | min gap with 80% power at n = 60 |
|---:|---:|---:|
| 6.25% (ProX-Lite, 32 triplets) | 6.2 pts | none reachable |
| 10% | 10 pts | none reachable |
| 15% | 15 pts | 14 pts |
| 20% | 20 pts | 17 pts |

So at the discordance seen so far, **no gap that could occur is reliably
detectable**: only a gap of ≥ 14 points with high discordance would show up.
A non-significant result means "no large gap", not "no gap". This run
estimates per-language accuracy and reasoning ratios on a category-balanced
sample; it is not a test of a small es−en accuracy difference.
