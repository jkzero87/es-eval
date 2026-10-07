# es-eval: Spanish vs English vs Chinese on a local 27B model

**Status: closed (2026-10-07).** Measurement phase and fix phase are both closed. Fix-phase goal was that a Spanish speaker should not pay more tokens than an English speaker; the prompt lever (lever 1) and the translation lever (lever 2) are ruled out (points 5–6). Next step is fine-tuning, in a new repo: [jkzero87/es-reasoning-finetune](https://github.com/jkzero87/es-reasoning-finetune).

## Conclusion

1. Accuracy is close across languages, with Spanish and Chinese slightly behind English: MGSM en 97.6% / es 95.2% / zh 93.6% (250 items), Belebele en 98.2% / es 96.5% / zh 96.1% (488), ProX-Lite en 81.7% / es 83.3% / zh 80.0% (60-question sample, too small to detect a gap under ~14 points). Only zh vs en is significant (exact McNemar p = 0.04 MGSM, 0.01 Belebele); es vs en is not (p = 0.15, 0.06, 1).
2. The clear difference is reasoning length: in Spanish the model thinks about 50% longer than in English (es/en reasoning tokens 1.50 MGSM, 1.49 Belebele, 1.29 ProX-Lite; zh/en 1.37, 1.20, 1.15).
3. Cause: reading the 20 largest MGSM gaps, the extra Spanish reasoning is mostly the model second-guessing wording it had read correctly and weighing alternative readings (main cost in 13 of 20). Belebele, with professional translations, shows the same gap, so it is the language, not poor translation.
4. Running out of tokens (max_tokens cap) happened in Spanish and Chinese but never in English, so it is not Spanish-only. ProX-Lite sample: es 2 (ids 636, 651), zh 1 (id 651), en 0. Outside the sample: MGSM es 120, 215 and ProX-Lite id 80 (es), all Spanish.
5. Lever 1, a "read words in their plain meaning" system prompt, cut the es−en reasoning gap by 28% (+114.4 → +82.5 tokens; ratio 1.50 → 1.34) without hurting accuracy, but missed the pre-registered targets (gap ≤ 57, ratio ≤ 1.25): **FAIL**, and the lever is closed.
6. Lever 2, translate-then-answer (es→en, answer in English, en→es; `results/lever2_plan.md`), was **stopped early by decision at 130/250 ids; this is not the pre-registered verdict.** On those 130 ids it cost 1086.8 tokens per question, 2.15 × the English baseline (bar: ≤ 543.3 = 1.10 ×) and 1.64 × the plain Spanish baseline, with accuracy intact (124/130 vs es baseline 122/130, McNemar p = 0.63; no number changed in either translation beyond formatting). `results/translation_floor.md` shows why no translation lever can pass: the translate-in call alone (≈ 158 tokens) is about 3× the 49-token allowance, so even translate-in plus the English baseline answer (626) is above the bar. Partial report: `results/lever2_partial.txt`.

## Future work

- Fine-tuning (Qwen3-14B, QLoRA) continues in [jkzero87/es-reasoning-finetune](https://github.com/jkzero87/es-reasoning-finetune).
- Quantization comparison (current IQ3_S vs IQ4_XS, `scripts/run_quant_compare.sh`): not scheduled; the IQ4_XS file was deleted from disk on 2026-10-05 (~14.3 GB to re-download), and that config (UD-IQ4_XS + MTP) hung in an earlier Xid 8 test (local-llm-lab notes, 2026-09-25).

## Where things are

- Audits: `results/mgsm_audit.md`, `results/belebele_audit.md`, `results/reasoning_gap_audit.md`, `results/latency_breakdown.md`
- Lever 1: `results/lever1_plan.md` (pre-registered), `results/lever1_result.md`, `results/after_lever1.md` (decision tree, pushed before the verdict)
- Lever 2: `results/lever2_plan.md` (pre-registered, with addendum), `scripts/run_lever2.py`, `scripts/lever2_decision.py` (`--partial`), `results/mgsm_raw.lever2.jsonl` (130 ids), `results/lever2_partial.txt`, `results/translation_floor.md`
- ProX-Lite sample: `results/proxlite_sample.md` (design and power limit), `results/proxlite_sample_score.txt`

## License

Code (`scripts/`, `prompts/`) is under the **MIT License** (`LICENSE`,
copyright 2026 Juan Camilo Bejarano Triana). The audit excerpts of benchmark
items in `results/mgsm_audit.md`, `results/belebele_audit.md` and
`results/reasoning_gap_audit.md`, and the tracked raw run files about MGSM and
Belebele (`results/mgsm_raw*.jsonl`, `results/belebele_raw.jsonl`), are under
**CC BY-SA 4.0**, as required by the datasets (see DATA_LICENSES below).

## DATA_LICENSES

This repository contains short excerpts of benchmark items (questions, passages,
options) and model outputs about them in `results/mgsm_audit.md`,
`results/belebele_audit.md` and `results/reasoning_gap_audit.md`. The raw run
files are tracked as evidence: `results/mgsm_raw.jsonl`,
`results/mgsm_raw.plain.jsonl`, `results/belebele_raw.jsonl` and
`results/proxlite_raw.jsonl` hold the model's full outputs (answers and
reasoning, which often restate the item), not the item text itself;
`results/mgsm_raw.lever2.jsonl` also holds the full MGSM Spanish question and
its English translation. `data/` is not tracked. The tracked
`results/*_token_split*.jsonl` and `results/fertility.csv` hold ids and counts
only.

| dataset | used via | license | redistribution |
|---|---|---|---|
| MGSM (Shi et al., 2022), built on GSM8K (Cobbe et al., 2021) | Hugging Face `juletxara/mgsm` | CC BY-SA 4.0 (dataset card); GSM8K: MIT | allowed with attribution; adaptations under CC BY-SA 4.0 |
| Belebele (Bandarkar et al., 2024), passages from FLORES-200 | Hugging Face `facebook/belebele` | CC BY-SA 4.0 | allowed with attribution; adaptations under CC BY-SA 4.0 |
| MMLU-ProX-Lite (Xuan et al., 2025), from MMLU-Pro / MMLU | Hugging Face `li-lab/MMLU-ProX-Lite` (rev. e82aafb) | MIT | allowed with the copyright and license notice |

Because of the ShareAlike terms, the files above with MGSM or Belebele
content (the three audit files, `results/mgsm_raw*.jsonl`,
`results/belebele_raw.jsonl`) are shared under **CC BY-SA 4.0**, with the
attribution below. No ProX-Lite item text is tracked; `results/proxlite_raw.jsonl`
holds only model outputs about ProX-Lite items (MIT dataset).

Attribution:
- Freda Shi, Mirac Suzgun, Markus Freitag, Xuezhi Wang, Suraj Srivats, Soroush
  Vosoughi, Hyung Won Chung, Yi Tay, Sebastian Ruder, Denny Zhou, Dipanjan Das,
  Jason Wei. *Language Models are Multilingual Chain-of-Thought Reasoners.*
  arXiv:2210.03057, 2022.
- Karl Cobbe et al. *Training Verifiers to Solve Math Word Problems.*
  arXiv:2110.14168, 2021.
- Lucas Bandarkar, Davis Liang, Benjamin Muller, Mikel Artetxe, Satya Narayan
  Shukla, Donald Husa, Naman Goyal, Abhinandan Krishnan, Luke Zettlemoyer,
  Madian Khabsa. *The Belebele Benchmark: a Parallel Reading Comprehension
  Dataset in 122 Language Variants.* ACL 2024, pp. 749–775.
- Weihao Xuan, Rui Yang, Heli Qi, Qingcheng Zeng, Yunze Xiao, Aosong Feng,
  Dairui Liu, Yun Xing, Junjue Wang, Fan Gao, et al. *MMLU-ProX: A
  Multilingual Benchmark for Advanced Large Language Model Evaluation.*
  arXiv:2503.10497, 2025.
