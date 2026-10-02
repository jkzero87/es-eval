# es-eval: Spanish vs English vs Chinese on a local 27B model

**Status: CLOSED (2026-10-02).**

## Conclusion

1. Accuracy is close across languages, with Spanish and Chinese slightly behind English: MGSM en 97.6% / es 95.2% / zh 93.6% (250 items), Belebele en 98.2% / es 96.5% / zh 96.1% (488), ProX-Lite en 81.7% / es 83.3% / zh 80.0% (60-question sample, too small to detect a gap under ~14 points). Only zh vs en is significant (exact McNemar p = 0.04 MGSM, 0.01 Belebele); es vs en is not (p = 0.15, 0.06, 1).
2. The clear difference is reasoning length: in Spanish the model thinks about 50% longer than in English (es/en reasoning tokens 1.50 MGSM, 1.49 Belebele, 1.29 ProX-Lite; zh/en 1.37, 1.20, 1.15).
3. Cause: reading the 20 largest MGSM gaps, the extra Spanish reasoning is mostly the model second-guessing wording it had read correctly and weighing alternative readings (main cost in 13 of 20). Belebele, with professional translations, shows the same gap, so it is the language, not poor translation.
4. Running out of tokens (16k/8k cap) is almost only a Spanish problem: 5 of 6 capped answers were Spanish (MGSM 120, 215; ProX-Lite 80, 636, 651), one Chinese (ProX-Lite 651, also capped in Spanish), none in English.
5. Lever 1, a "read words in their plain meaning" system prompt, cut the es−en reasoning gap by 28% (+114.4 → +82.5 tokens; ratio 1.50 → 1.34) without hurting accuracy, but missed the pre-registered targets (gap ≤ 57, ratio ≤ 1.25): **FAIL**, and the lever is closed.

## Future work

- Quantization comparison (current IQ3_S vs IQ4_XS, `scripts/run_quant_compare.sh`, MGSM first, ≈ 2–2.5 h): does the Spanish/Chinese reasoning excess or accuracy deficit shrink at higher precision? Plan in `results/after_lever1.md`, branch 3; not scheduled.

## Where things are

- Audits: `results/mgsm_audit.md`, `results/belebele_audit.md`, `results/reasoning_gap_audit.md`, `results/latency_breakdown.md`
- Lever 1: `results/lever1_plan.md` (pre-registered), `results/lever1_result.md`, `results/after_lever1.md` (decision tree, pushed before the verdict)
- ProX-Lite sample: `results/proxlite_sample.md` (design and power limit), `results/proxlite_sample_score.txt`
