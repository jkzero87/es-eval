# MGSM reasoning-gap audit: what the extra es reasoning does

The 20 ids with the largest es − en reasoning-token gap (exact counts from
`results/mgsm_token_split.jsonl`). For each, the en and es `reasoning_content`
were read side by side; the two traces that hit max_tokens (215, 120) were
read at the start, middle and end. Audit status is from `results/mgsm_audit.md`.
Done offline; no server requests.

Labels (more than one per id allowed; **bold** = what accounts for most of the
extra tokens):

- **a**: translating or restating the problem
- **b**: deliberating about which language to answer in, or how to phrase the Spanish answer
- **c**: re-checking or redoing arithmetic the en run did once
- **d**: misreading the Spanish wording, then correcting it
- **e**: other. The one that comes up most is labelled **e1**: doubting the
  meaning of a Spanish phrase the model had read correctly, and weighing
  alternative readings (no actual misreading). Other e cases are described
  in the table.

Reasoning tokens are en → es. es result: ✓ = correct, ✗ = wrong,
— = no answer (hit max_tokens).

| id | reasoning tokens | gap | es | labels | evidence (es reasoning) | audit (es) |
|---|---|---:|:-:|---|---|---|
| 215 | 420 → 8192 | 7772 | — | a, c, **e: problem unsolvable as translated; keeps searching for a reading that works until max_tokens** | "If both leak at the same rate, the difference is constant." | translation |
| 120 | 5248 → 8192 | 2944 | — | a, c, **e1** ("a la par", what "su" refers to) | "What if "a la par" means they increased to the same amount (parity)?" | ambiguous gold (notes "a la par") |
| 88 | 545 → 2780 | 2235 | ✓ | a, **c** (redoes the raise-timing table ~4×), e1 | ""para aquellos que han estado en la empresa durante cinco años" - for those who HAVE BEEN (present perfect)" | not audited |
| 39 | 169 → 1553 | 1384 | ✗ | a, c, **e1** (inverted relation; picks the reading that gives a whole number) | "Wait, maybe "la mitad de lo que corre los otros dos días" means "half of what he runs on each of the other two days"" | translation |
| 158 | 478 → 1573 | 1095 | ✗ | a, c, **e1** → keeps a wrong reading | "In Spanish, "de un lado a otro" literally means "from one side to the other" which is a one-way trip." | model |
| 71 | 315 → 1335 | 1020 | ✗ | a, c, **e1** → keeps a wrong reading | ""todos los días de la semana" means "all days of the week" = 7 days." | translation |
| 177 | 179 → 1107 | 928 | ✓ | a, **d** (niños read as "children", corrected to "boys") | "Could "niños" be interpreted as "children" (both boys and girls) in some contexts?" | not audited |
| 17 | 200 → 904 | 704 | ✗ | a, c, **e1** → keeps a wrong reading (displacement) | "But wait, I think the problem is actually asking for the straight-line distance" | model |
| 236 | 135 → 773 | 638 | ✗ | a, c, **e1** → keeps a wrong reading (adds John) | "This suggests 20 friends + John = 21 people total." | model |
| 235 | 113 → 650 | 537 | ✓ | a, **e1** ("dos veces más", who the subject is) | ""come dos veces más que su novia" in Spanish can mean "he eats twice as much as his girlfriend"" | not audited |
| 199 | 210 → 724 | 514 | ✓ | a, c, **e1** ("tenía" / "tiene ahora en total") | "this could just mean how many she has now (at the end), which would be 200." | not audited |
| 111 | 148 → 631 | 483 | ✓ | a, c, **e: real typo in the es text ("ancho" twice); notices it and works around it** | "Marcel: 3 wide × 14 wide (this is likely a typo for "long" = 14 largo)" | not audited |
| 79 | 260 → 741 | 481 | ✓ | a, e1, **e: tries mixed bundle combinations that en never considered** | "Option 3: Mix of both" | not audited |
| 202 | 337 → 793 | 456 | ✓ | a, c, **e1** | "this could be interpreted as his salary IS $2000 per week for all weeks of the year" | not audited |
| 94 | 1174 → 1619 | 445 | ✗ | a, c, **e1** (the translated question asks something else; speed vs time) | "maybe "mejoró un 10% su velocidad" means his time was reduced by 10%?" | translation |
| 237 | 252 → 678 | 426 | ✓ | a, c, **e1** | "Wait, the question asks "¿cuántos bolígrafos termina teniendo en total?"" | not audited |
| 13 | 845 → 1257 | 412 | ✗ | **c**, e: longer deliberation over the same break-even ambiguity en had (en also ✗) | "Some might interpret "comenzar a ganar dinero" as the year when he recovers his initial investment" | ambiguous gold |
| 187 | 248 → 633 | 385 | ✓ | a, c, **e1** | "Are rabbits "small rodents"?" | not audited |
| 250 | 187 → 497 | 310 | ✓ | a, c, **e1** | ""4 veces más" in Spanish can be ambiguous." | not audited |
| 210 | 195 → 481 | 286 | ✗ | a, **c** (re-reads the question and re-checks), e: misreads "media docena" as 3 and **never corrects it** | "Half a dozen plates = 6/2 = 3 plates" | model |

A scan of all 20 es traces for answer-language talk ("in Spanish", "respond
in", "Respuesta:" …) found only discussion of what the problem wording means.
No trace deliberates about the answer language (b = 0).

## Label counts (n = 20)

| label | ids with the label | main driver |
|---|---:|---:|
| a: translate / restate | 19 | 0 |
| b: answer-language deliberation | 0 | 0 |
| c: re-check / redo arithmetic | 17 | 3 |
| d: misread, then corrected | 1 | 1 |
| e1: doubts the meaning of correctly read Spanish | 15 | 13 |
| e (other): unsolvable-problem search, typo workaround, extra solution search, longer gold-ambiguity deliberation, uncorrected misreading | 5 | 3 |

Restating (a) is nearly universal but cheap: a few lines that quote the
Spanish and gloss it in English (all 20 es traces reason in English).
Re-checking (c) is also common, but in most traces it follows a doubt about
the wording rather than standing alone.

**Known translation problems** (audit cause `translation`): **4 of 20**
(39, 71, 94, 215). The audit also flags the "a la par" wording for 120 but
files it as ambiguous gold. The audit only covers wrong answers. This reading
turned up more wording issues among the ids es answered correctly, not
verified and not added to the audit:
- 111: "ancho" written twice in the es text.
- 199: "collected" became "tenía" (had).
- 235 and 250: "veces más" is ambiguous in Spanish.

Among the wrong answers, 158's "de un lado a otro" for "back and forth" may
also be a translation issue; the audit calls it faithful.

## Conclusion

- The extra es reasoning is mostly the model **doubting what the Spanish wording means**. 15 of 20 traces weigh alternative readings of a phrase they read correctly, and that is the main cost in 13. Re-checking arithmetic is the main cost in 3, a corrected misreading in 1, and no trace deliberates about the answer language.
- The doubt is costly and does not protect accuracy: es is wrong or gives no answer in 10 of the 20. These ids include 8 of the 9 where en is right and es wrong. Three (17, 158, 236) settle on a wrong reading of a faithful translation; three (39, 71, 94) correctly follow a mistranslated text.
- 4 of the 20 have a known translation problem in the audit (39, 71, 94, 215). The other wording issues listed above (111, 199, 235/250, 158) suggest part of the remaining doubt comes from the translation too, and are worth a review pass.
