# Translation floor: can any translate-based lever pass (T)?

Written 2026-10-07 16:21, while the lever-2 run was in progress (30 of 250
ids done). Offline, no model calls. **This is a lower bound, not a
measurement:** no "translate in, answer directly in Spanish" run exists.

## Question

The cheapest translation-based lever is: translate the Spanish question to
English (lever 2's step 1), then answer directly in Spanish, with no
translate-out call. Could it meet lever 2's (T) bar, mean total ≤ 543.3
tokens per question (1.10 × the en baseline 493.9)?

## Floor

Per id: **floor = translate-in tokens (step 1 of the lever-2 record,
prompt + completion) + en baseline total for that id** (`mgsm_raw.jsonl`,
prompt + completion). The en baseline total stands in for the answer call:
it is the cheapest answer this model gave to that question in the
measurement phase. A Spanish-language answer has so far cost more, not less
(es baseline 659.6 vs en 493.9 over 250 ids), so a real run would very
likely land above this floor.

| ids 1–30 (lever-2 records so far) | mean tokens |
|---|---:|
| translate in (step 1): prompt 97.6 + completion 59.9 | 157.5 |
| en baseline total, same ids | 468.9 |
| **floor** | **626.4** |
| (T) bar | 543.3 |
| es baseline total, same ids (no lever) | 588.2 |

The floor is **above 543.3, by 83 tokens**. 12 of 30 ids are individually
under the bar, but not the mean. With the all-250 en mean (493.9) in place
of the 30-id mean, the floor is 651.4. Translate-in ranged from 89 to 262
tokens per id.

## Reading

(T) leaves 49.4 tokens per question above the English baseline. One
translate-in call already costs 157.5 on average, about 3× that allowance.
Even a trivial input is not cheap: the plumbing check (instruction + chat
template + a 6-word sentence) used 39 prompt tokens. So any lever that spends a separate translation call cannot pass
(T) on this bar, whatever the answer step costs, unless the answer comes in
well *below* the English baseline. The floor is also above the es baseline
on the same ids (626.4 vs 588.2), so this variant would cost a Spanish
speaker more than no lever at all.

Caveat: 30 ids, the first 30 in id order, not a random sample; the en
baseline over these ids (468.9) is below its 250-id mean (493.9). The
conclusion does not depend on that: the gap to the bar (83 tokens) is
larger than the difference.
