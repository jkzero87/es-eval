# Belebele audit: en right, es or zh wrong

Generated from `belebele_raw.jsonl` by `scripts/audit_belebele.py` (offline). Correct = last standalone A–D letter in `content` (`score_belebele.py`); *marker* = letter after the last 'Answer:' / 'Respuesta:' / '答案：'.

## Summary

```
1464 records, 488 ids with all three languages

lang     n     acc  %unparsed  mean_compl  mean_wall_s  %reas_en  parse_disagree
en     488  0.9816        0.0         345         6.99     100.0               0
es     488  0.9652        0.0         467         9.51      80.3               0
zh     488  0.9611        0.0         369         7.77      30.9               0

pair         n  both✓  both✗  en✓ x✗  x✓ en✗  McNemar p
es vs en   488    468      6      11       3    0.05737
zh vs en   488    467      7      12       2    0.01294
```

## Causes (en ✓, other ✗)

| cause | es | zh |
|---|---:|---:|
| translation | 9 | 4 |
| model | 1 | 5 |
| ambiguous gold | 1 | 3 |
| parser | 0 | 0 |

es causes are pending Juan's review; one es 'translation' (343) is weak. No parser errors: the marker parse agrees with the scorer on every record and nothing is unparsed.

## Reasoning-token gap (lever-1 follow-up): Belebele vs MGSM

Exact token counts via `/tokenize` (`mgsm_token_split.py`). Ids present in en, es and zh.

| | MGSM (n=250) | Belebele (n=488) |
|---|---:|---:|
| mean reasoning tokens, en | 228.1 | 231.6 |
| mean reasoning tokens, es | 342.4 | 345.2 |
| mean reasoning tokens, zh | 313.0 | 277.3 |
| **es − en reasoning gap (mean of per-id)** | **+114.4** | **+113.5** |
| es / en reasoning ratio | 1.50 | 1.49 |
| median per-id es − en gap | +23.5 | +62.0 |
| Wilcoxon exact p (es vs en) | 1.4e-15 | 3.2e-61 |
| **zh − en reasoning gap (mean of per-id)** | **+85.0** | **+45.7** |
| zh / en reasoning ratio | 1.37 | 1.20 |
| median per-id zh − en gap | +12.0 | +24.5 |
| Wilcoxon exact p (zh vs en) | 4.4e-07 | 2.7e-13 |

### Final-answer part

| | MGSM | Belebele |
|---|---:|---:|
| mean answer tokens / characters, en | 174 / 477 | 110 / 502 |
| answer tokens per character, en | 0.364 | 0.220 |
| mean answer tokens / characters, es | 213 / 537 | 119 / 474 |
| answer tokens per character, es | 0.397 | 0.251 |
| mean answer tokens / characters, zh | 174 / 256 | 88 / 146 |
| answer tokens per character, zh | 0.680 | 0.608 |
| es − en answer tokens | +39.5 | +8.8 |
| … says more (es − en characters × mean tok/char) | +22.7 (+60 chars) | -6.5 (-28 chars) |
| … costs more per character | +16.8 | +15.3 |
| zh − en answer tokens | +0.2 | -22.0 |
| … says more (zh − en characters × mean tok/char) | -115.5 (-221 chars) | -147.5 (-356 chars) |
| … costs more per character | +115.7 | +125.5 |

The two answer sub-rows add up to the answer gap exactly (midpoint rule). zh characters are not comparable with Latin-script characters, so for zh that split is arithmetic only.

**Reading:** the es reasoning excess is essentially the same on Belebele as on MGSM (+113.5 vs +114.4 tokens, ratio 1.49 vs 1.50), and on Belebele it is broad (median per-id gap +62.0 vs +23.5 on MGSM). Belebele's passages are professional FLORES translations, so the gap is not explained by MGSM's translation quality alone. Caveat: the es translation is not clean on Belebele either (most es failures above are translation shifts), and both tasks reason mostly in English (Belebele es: 80% of reasoning detected as English).

## Items (en ✓, other language ✗)

cause: `translation` / `model` / `ambiguous gold` / `parser`

| id | lang | gold | parsed | marker | question (en) | question (lang) | cause |
|---|---|---|---|---|---|---|---|
| 47 | es | C | B | B | According to the passage, which statement about tornadoes is not true? | De acuerdo con el texto, ¿qué afirmación acerca de los tornados no es cierta? | **translation**: option C 'more than three hours' became 'menos de tres horas' (less), which makes C true in es; model's B follows the es options *(pending Juan's review)* |
| 114 | es | B | A | A | According to the passage, which part of a cycad plant might a Triceratops be likely to eat? | De acuerdo con el texto, ¿qué parte de una planta cícada podría comer un Tricerátops? | **translation**: 'strip off the leaves before eating the trunk' became 'arrancado las hojas … en lugar de comerse el tronco' (instead of eating the trunk); model's A (leaves) follows the es text *(pending Juan's review)* |
| 131 | es | A | B | B | Which of the following is not an accurate fact about the Hangeul alphabet? | ¿Cuál de los siguientes no es un hecho preciso del alfabeto coreano? | **ambiguous gold**: option B 'Hunan Jeongeum' misspells the passage's 'Hunmin Jeongeum' in both languages, so B is also 'not accurate'; model chose B, gold A *(pending Juan's review)* |
| 186 | es | C | D | D | Who suggested that revisions be made to the ‘Clean Air Act’? | "¿Quién sugirió que se revisara la ""Ley de Aire Limpio""?" | **translation**: 'suggested that revisions be made' became '¿quién sugirió que se revisara…?' (be reviewed), which matches Harper's 'enviar … para su revisión'; model's D (Harper) follows that *(pending Juan's review)* |
| 321 | es | B | A | A | Based on the passage, which of the following statements about Franciszek Kowal’s experience is true? | Según el fragmento, ¿cuál de las siguientes afirmaciones sobre la experiencia de Franciszek Kowal es cierta? | **translation**: es splits the quote, so 'Por suerte, estoy bien' is no longer attributed to Kowal; model explicitly says 'estoy bien lo dice el narrador' and rejects B *(pending Juan's review)* |
| 331 | es | D | A | A | Who delivered the statement regarding the US troops? | ¿Quién hizo la declaración sobre las tropas estadounidenses? | **translation**: 'Who delivered the statement' became '¿Quién hizo la declaración?' (made); Trump made it via the press secretary, so model's A fits the es question *(pending Juan's review)* |
| 343 | es | A | D | D | Based on the passage, when choosing a Frequent Flyer airline in an alliance, which of the following should you prioritize? | Basándose en el fragmento, a la hora de elegir una compañía aérea de vuelos frecuentes en una alianza, ¿cuál de las siguientes se debería priorizar? | **translation (weak)**: 'frequent flyer points may be more generous' became 'los puntos … pueden otorgarle más beneficios' (more benefits), which points at D (privileges) rather than A (most points) *(pending Juan's review)* |
| 374 | es | C | B | B | According to the passage, what kind of skiing is done in steeper terrain? | Según el fragmento, ¿qué tipo de esquí se practica en terrenos más escarpados? | **translation**: 'alpine style ski touring or mountaineering' split into 'esquí de travesía o el montañismo de estilo alpino', so 'esquí de travesía' (option B) is what the es text places on steep terrain *(pending Juan's review)* |
| 458 | es | B | D | D | According to the passage, who is most likely to have at least a limited understanding of the English language? | Según el fragmento, ¿quién es más probable que posea un conocimiento limitado de la lengua inglesa? | **translation**: 'at least a limited understanding' became 'un conocimiento limitado' (a limited, i.e. poor, knowledge); model's D (older people) answers the es question *(pending Juan's review)* |
| 463 | es | D | A | A | According to the passage, from where should a traveler obtain advice regarding the political situation in their destination city? | Según el fragmento, ¿dónde debería asesorarse un viajero sobre la situación política de su ciudad de destino? | **model**: faithful translation; the passage says other governments' advice is for their own citizens, model still picked the destination's government (A) *(pending Juan's review)* |
| 483 | es | A | D | D | According to the passage, which of the following would not be a recommended tip for women traveling in the area? | Según el fragmento, ¿cuál de los siguientes no sería un consejo recomendable para las mujeres que viajan por la zona? | **translation**: 'Use toughness when necessary' became 'Utilizar la fuerza' (use force), which the passage does not recommend; model's D follows the es option *(pending Juan's review)* |
| 68 | zh | A | B | B | Which of the following is not an object of the rule of thirds? | 以下哪项不是三分法的对象？ | **model**: faithful (动态 = dynamism; 活力和能量 = 'life and energy' as in en); model rejected B on a wording nuance instead of spotting that A is not stated |
| 106 | zh | B | A | A | Which of the following would not be considered a tiger’s greatest strength? | 以下哪项不被认为是老虎的最大优势？ | **ambiguous gold**: passage keeps 'though not well' for climbing (攀爬能力不是很强), but it never presents roaring as a strength either (tiger's roar is weaker than a lion's); A and B are both defensible |
| 179 | zh | B | D | D | According to the passage, what information is known following the bombing? | 根据这段文字，爆炸事件之后已知的信息是什么？ | **model**: faithful ('some reports put the official death toll at eight' = 一些报道称…8 人, i.e. unconfirmed); model took it as known and picked D |
| 219 | zh | B | A | A | Following the explosion, who was treated for serious injuries? | 爆炸发生后，谁因为严重的伤势接受了治疗？ | **model**: faithful ('no major casualties', 5 treated for shock); model considered B (no one) and then chose A |
| 230 | zh | A | C | C | According to Armand Versace’s account, what occurred directly before the crowd began to react to the weather? | 根据阿尔芒·范思哲的描述，在人群开始对天气做出反应之前，发生了什么？ | **translation**: 'directly before the crowd began to react' lost 'directly' (在人群开始对天气做出反应之前); without it the wind (C), the first weather event, is a valid answer |
| 268 | zh | A | C | C | As stated in the passage, which nation is affected by the signing of the Kyoto climate accord? | 根据这段文字，哪个国家受到了《京都气候议定书》签署的影响？ | **ambiguous gold**: gold A (US becomes the only developed nation not to sign) but the passage also says the deal would affect Australia's economy; C (Australia, the signer) is at least as defensible |
| 331 | zh | D | A | A | Who delivered the statement regarding the US troops? | 谁发表了关于美军的声明？ | **translation**: 特朗普通过新闻秘书发表声明 makes Trump the subject of 发表 (issued), and the question asks 谁发表了…声明; model's A follows the zh text |
| 335 | zh | D | A | A | Which of the following people is not a lawyer? | 以下哪位不是律师？ | **translation**: zh moves 'member of Parliament and lawyer' from Petros Mantouvalos to the journalist Makis (议员兼律师马基斯…), so Mantouvalos is not a lawyer in zh; model's A follows the zh text |
| 376 | zh | C | B | B | Which of the following should people avoid doing with moose? | 人们应该避免对驼鹿做以下哪种事情？ | **translation**: 'Minimizing their potential threat level' (underestimating) became 减少它们的潜在威胁程度 (actually reducing the threat), which is not something to avoid; model rejects C for that reason |
| 389 | zh | C | B | B | Which of the following might not be understood by French-speaking Belgians and Swiss? | 哪项可能不为说法语的比利时人和瑞士人所理解？ | **model**: faithful except 数字系统/度量系统 (numbering vs measurement) in the last sentence, which does not affect the choice; model picked B (peculiar words, not mentioned) over C (pronunciation, stated as different) |
| 471 | zh | C | A | A | Which of the following is an advantage of traveling within the Schengen zone? | 在申根区内旅行的好处是什么？ | **ambiguous gold**: the passage (all languages) states both 'no passport control checkpoints' (C, gold) and 'no separate visa applications' (A); model chose A |
| 479 | zh | C | A | A | According to the passage, which of the following issues is most likely to not be covered in a professional training class or in publications? | 根据这段文字，以下哪个问题最可能没有涵盖在专业培训课程或出版物中？ | **model**: faithful; passage says courses cover everything and wilderness books are common but war-zone publications are few (C); model picked A |

## Item details

### id=47 es (gold C; parsed B; marker B; qid `https://en.wikibooks.org/wiki/High_School_Earth_Science/Storms:1`)

- **en passage (start):** Tornadoes strike a small area compared to other violent storms, but they can destroy everything in their path. Tornadoes uproot trees, rip boards from buildings, and fling cars up into the sky. The most violent two percent of tornadoes last more than three hours. These monster storms have winds up to 480 km/h (133 m/s; 300 mph).
- **es passage (start):** Si bien las superficies que azotan los tornados son pequeñas, comparadas con otras tormentas agresivas, pueden destruir todo en su camino. Los tornados desarraigan árboles, arrancan paneles de los edificios y lanzan vehículos al cielo. El 2 % más agresivo de los tornados dura más de tres horas. Estas colosales tormentas traen ráfagas de hasta 480 km/h (133m/s; 300 mph).
- **en question:** According to the passage, which statement about tornadoes is not true?
- **es question:** De acuerdo con el texto, ¿qué afirmación acerca de los tornados no es cierta?
- **options en / es:** A) Tornadoes are capable of destroying everything in their vicinity / Los tornados son capaces de destruir todo en su camino; B) Tornadoes strike smaller areas than other storms / Los tornados azotan áreas más pequeñas que otras tormentas; C) The majority of tornadoes last more than three hours / La mayoría de los tornados duran menos de tres horas; D) Some tornadoes can have winds up to 300 miles per hour / Algunos tornados pueden traer ráfagas de hasta 300 millas por hora
- **es answer (last 400 chars):** mayoría dura menos. ✔️ Cierto. **D)** "Algunos tornados pueden traer ráfagas de hasta 300 millas por hora" → El texto menciona "ráfagas de hasta 480 km/h (... 300 mph)" para el 2 % más agresivo (es decir, *algunos* tornados). ✔️ Cierto. La afirmación que **no** es cierta de acuerdo con el texto es la **B**, porque distorsiona la comparación al eliminar el calificativo "agresivas". Respuesta: B
- **es reasoning (last 600 chars):** reas compared to aggressive storms (like hurricanes, severe thunderstorms), they would also hit small areas compared to regular storms. So B could still be considered true. Hmm, let me think about this differently. In a typical exam setting, which answer would be the "incorrect" one? Actually, I'll go with B. The text specifically says "comparadas con otras tormentas agresivas" (compared to other aggressive storms), and option B says "que otras tormentas" (than other storms) without the qualifier "agresivas." This is a distortion of the original text's meaning. I'll go with B as my answer.

### id=114 es (gold B; parsed A; marker A; qid `https://en.wikibooks.org/wiki/Wikijunior:Dinosaurs/Triceratops:1`)

- **en passage (start):** A triceratops' teeth would have been able to crush not only leaves but even very tough branches and roots. Some scientists think Triceratops ate cycads, which are a type of plant that was common in the Cretaceous. These plants look like a small palm tree with a crown of sharp, spiky leaves. A Triceratops could have used its strong beak to strip off the leaves before eating the trunk. Other scientists argue that these plants are very poisonous so it is unlikely that any dinosaur ate them, even though today the sloth and other animals like the parrot (a descendant of the dinosaurs) can eat poiso…
- **es passage (start):** Con su dentadura, un triceraptops hubiese podido triturar no solo hojas, sino además ramas y raíces muy duras. Según creen algunos científicos, la alimentación del Tricerátops era a base de cícadas, un tipo de planta común en el período Cretácico. Estas plantas se asemejan a una pequeña palmera con una corona de hojas filosas y puntiagudas. El Triceráptors podría haber arrancado las hojas con su robusto cuerno en lugar de comerse el tronco. Otros científicos sostienen que son pocas las probabilidades de que algún dinosaurio se alimentara con estas plantas, dado que son altamente venenosas; no …
- **en question:** According to the passage, which part of a cycad plant might a Triceratops be likely to eat?
- **es question:** De acuerdo con el texto, ¿qué parte de una planta cícada podría comer un Tricerátops?
- **options en / es:** A) The spiky leaves / Las hojas puntiagudas; B) The trunk / El tronco; C) The root / La raíz; D) The fruit / Los frutos
- **es answer (last 400 chars):** Según el texto, el Tricerátops "podría haber arrancado las hojas con su robusto cuerno en lugar de comerse el tronco." Además, se describe que las cícadas tienen "una corona de hojas filosas y puntiagudas." Por lo tanto, la parte de la planta que el Tricerátops podría comer eran las hojas puntiagudas, no el tronco. Respuesta: A
- **es reasoning (last 600 chars):** orn INSTEAD OF eating the trunk. So the Triceratops could eat the leaves (hojas), not the trunk. The text says "arrancado las hojas" (torn off the leaves) "en lugar de comerse el tronco" (instead of eating the trunk). Looking at the options: A) Las hojas puntiagudas - The pointed leaves B) El tronco - The trunk C) La raíz - The root D) Los frutos - The fruits The text mentions the cycad has "una corona de hojas filosas y puntiagudas" (a crown of sharp and pointed leaves). The Triceratops could have torn off the leaves instead of eating the trunk. So the answer is A) Las hojas puntiagudas.

### id=131 es (gold A; parsed B; marker B; qid `https://en.wikibooks.org/wiki/Wikijunior:Languages/Korean:1`)

- **en passage (start):** "Hangeul is the only purposely invented alphabet in popular daily use. The alphabet was invented in 1444 during the reign of King Sejong (1418 – 1450). King Sejong was the fourth king of the Joseon Dynasty and is one of the most highly regarded. He originally named the Hangeul alphabet Hunmin Jeongeum, which means ""the correct sounds for the instruction of the people""."
- **es passage (start):** El alfabeto coreano es el único diseñado en forma deliberada que aún se utiliza a diario popularmente. Se inventó en 1444, durante el reinado de Sejong (1418 a 1450). Sejong fue el monarca número cuatro de la dinastía Joseon y uno de los que ganó mayor respeto. El nombre original que se le dio al alfabeto Hangeul fue Hunmin Jeongeum, que significa «los sonidos adecuados para instruir al pueblo».
- **en question:** Which of the following is not an accurate fact about the Hangeul alphabet?
- **es question:** ¿Cuál de los siguientes no es un hecho preciso del alfabeto coreano?
- **options en / es:** A) It was invented at the beginning of King Sejong’s reign / Fue inventado a principios del reinado del monarca Sejong; B) The alphabet’s original name was Hunan Jeongeum / El nombre original del alfabeto fue Hunan Jeongeum; C) It was invented by Joseon Dynasty’s fourth king / Fue inventado por el cuarto monarca de la dinastía Joseon; D) It was purposely invented / Fue diseñado en forma deliberada
- **es answer (last 400 chars):** ngeum"**, lo cual es un error factual directo en el nombre. - **C)** El texto confirma que Sejong fue el monarca número cuatro de la dinastía Joseon y que el alfabeto se inventó durante su reinado. ✓ - **D)** El texto afirma explícitamente que es "el único diseñado en forma deliberada". ✓ La opción B contiene un dato inexacto: altera el nombre original del alfabeto (Hunmin → Hunan). Respuesta: B
- **es reasoning (last 600 chars):** "Hunmin Jeongeum" and option B says "Hunan Jeongeum." This is a deliberate alteration of the name to make it incorrect. Actually, I think B is the intended answer because it's a clear, unambiguous error - the name is wrong. The name "Hunmin Jeongeum" is a proper noun and changing it to "Hunan Jeongeum" is a factual error. Option A could be debatable - some might argue 1444 is relatively early in a long reign, but objectively it's not "a principios." However, in the context of this test, I think B is the clear answer because it's a direct misstatement of a fact (the name). Let me go with B.

### id=186 es (gold C; parsed D; marker D; qid `https://en.wikinews.org/wiki/Canadian_Prime_Minister_Harper_agrees_to_send_%27Clean_Air_Act%27_to_committee:1`)

- **en passage (start):** "Prime Minister Stephen Harper has agreed to send the government's 'Clean Air Act' to an all-party committee for review, before its second reading, after Tuesday's 25 minute meeting with NDP leader Jack Layton at the PMO. Layton had asked for changes to the conservatives' environmental bill during the meeting with the PM, asking for a ""thorough and complete rewriting"" of the Conservative party's environmental bill. Ever since the Federal Government stepped in to take over funding of the Mersey hospital in Devonport, Tasmania, the state government and some federal MPs have criticised this act…
- **es passage (start):** Stephen Harper, primer ministro, acordó enviar la Ley de Aire Limpio del gobierno para su revisión a un comité donde participan todos los partidos antes de la segunda lectura, y después de la reunión de 25 minutos en la PMO del martes con Jack Layton, líder del NDP. Durante la reunión llevada a cabo con el primer ministro, Layton había solicitado que se introdujeran cambios en la ley ambiental de los conservadores, apelando a una «modificación exhaustiva y completa de su redacción». Desde que el gobierno federal intervino y asumió la financiación del hospital Mersey, en Davenport, Tasmania, la…
- **en question:** Who suggested that revisions be made to the ‘Clean Air Act’?
- **es question:** "¿Quién sugirió que se revisara la ""Ley de Aire Limpio""?"
- **options en / es:** A) John Howard / John Howard; B) The Conservative party / El partido conservador; C) Jack Layton / Jack Layton; D) Stephen Harper / Stephen Harper
- **es answer (last 400 chars):** Analizando el texto, se indica que **Stephen Harper, primer ministro, acordó enviar la Ley de Aire Limpio del gobierno para su revisión a un comité** donde participan todos los partidos antes de la segunda lectura. Aunque la reunión con Jack Layton fue el contexto en el que se tomaría esta decisión, es Harper quien acuerda y propone formalmente el envío a revisión. Respuesta: D
- **es reasoning (last 600 chars):** quested changes to the environmental law 3. Stephen Harper agreed to send the Clean Air Act for review to a committee The "acordó" (agreed) suggests that someone proposed it and Harper agreed. But the text doesn't explicitly say who proposed the review to a committee specifically. Layton requested "changes" and a "thorough and complete modification of its wording." I think the most direct answer based on the text is D) Stephen Harper, as he is the one who "acordó enviar... para su revisión." He's the one who made the decision to send it for review. Actually, I'll go with D) Stephen Harper.

### id=321 es (gold B; parsed A; marker A; qid `https://en.wikinews.org/wiki/Trade_hall_roof_collapses_in_Poland:1`)

- **en passage (start):** """Luckily nothing happened to me, but I saw a macabre scene, as people tried to break windows in order to get out. People were hitting the panes with chairs, but the windows were unbreakable. One of the panes finally broke, and they started to get out by the window,"" said survivor Franciszek Kowal."
- **es passage (start):** Por suerte, estoy bien, pero presencié una escena tétrica cuando la gente trataba de romper las ventanas para escapar. A pesar de que las personas usaban sillas para golpear los vidrios, las ventanas eran imposibles de romper. Un sobreviviente, Franciszek Kowal, «contó que uno de los paneles de vidrio finalmente se rompió y comenzaron a escapar por la ventana».
- **en question:** Based on the passage, which of the following statements about Franciszek Kowal’s experience is true?
- **es question:** Según el fragmento, ¿cuál de las siguientes afirmaciones sobre la experiencia de Franciszek Kowal es cierta?
- **options en / es:** A) He managed to break a window / Consiguió romper una ventana; B) He was ultimately unharmed / Al final resultó ileso; C) He broke a chair while trying to get out / Rompió una silla cuando intentaba salir; D) He was injured while attempting to break a window / Resultó herido al intentar romper una ventana
- **es answer (last 400 chars):** indica que la ventana fue rota y las personas lograron escapar por ella. - **A)** Se alinea directamente con lo que Kowal relató: el panel de vidrio se rompió y escaparon por la ventana. - **B)** El texto no confirma que Kowal resultara ileso; "estoy bien" lo dice el narrador. - **C)** No se menciona que una silla se rompiera. - **D)** No hay referencia a que Kowal resultara herido. Respuesta: A
- **es reasoning (last 600 chars):** rrator, not specifically to Kowal. We can't definitively say he was unharmed. C) Rompió una silla cuando intentaba salir (He broke a chair when trying to get out) - The text says people used chairs to hit the glass, but doesn't say a chair was broken. D) Resultó herido al intentar romper una ventana (He was injured while trying to break a window) - There's no mention of him being injured. The correct answer is A) - The text states that one of the glass panels finally broke and they began to escape through the window. This indicates that the window was broken (consiguió romper una ventana).

### id=331 es (gold D; parsed A; marker A; qid `https://en.wikinews.org/wiki/US_President_Trump_announces_troop_withdrawal_from_Syria:1`)

- **en passage (start):** Late on Sunday, the United States President Donald Trump, in a statement delivered via the press secretary, announced US troops would be leaving Syria. The announcement was made after Trump had a phone conversation with Turkish President Recep Tayyip Erdoğan. Turkey would also take over guarding captured ISIS fighters which, the statement said, European nations have refused to repatriate.
- **es passage (start):** El domingo por la noche, en un anuncio realizado mediante el secretario de prensa, el presidente de los Estados Unidos de América, Donald Trump, comunicó que las tropas estadounidenses se retirarían de Siria. El anuncio se hizo tras la conversación telefónica que Trump mantuvo con con el presidente de Turquía, Recep Tayyip Erdoğan. Turquía asumiría, además, la vigilancia de los militantes del ISIS que fueron capturados, a quienes las naciones europeas, conforme indica el comunicado, les denegó su repatriación.
- **en question:** Who delivered the statement regarding the US troops?
- **es question:** ¿Quién hizo la declaración sobre las tropas estadounidenses?
- **options en / es:** A) Donald Trump / Donald Trump; B) Tayyip Erdoğan / Tayyip Erdoğan; C) ISIS fighters / Militantes del ISIS; D) The press secretary / El secretario de prensa
- **es answer (last 400 chars):** Según el texto, aunque el anuncio se realizó "mediante el secretario de prensa", fue **el presidente de los Estados Unidos, Donald Trump**, quien "comunicó que las tropas estadounidenses se retirarían de Siria". El secretario de prensa fue solo el medio a través del cual se transmitió el mensaje, pero la declaración corresponde a Trump. Respuesta: A
- **es reasoning (last 600 chars):** irarían de Siria." The text says that the announcement was made "mediante el secretario de prensa" (through the press secretary), but the one who "comunicó" (communicated/made the declaration) was Donald Trump, the president of the United States. The question asks "¿Quién hizo la declaración sobre las tropas estadounidenses?" - Who made the declaration about US troops? The declaration was made by Donald Trump (through the press secretary). The press secretary was the medium/channel through which it was made, but the person who made the declaration was Trump. The answer is A) Donald Trump.

### id=343 es (gold A; parsed D; marker D; qid `https://en.wikivoyage.org/wiki/Airline_alliances:1`)

- **en passage (start):** You should choose your Frequent Flyer airline in an alliance carefully. Although you may think it is intuitive to join the airline you fly most, you should be aware that privileges offered are often different and frequent flyer points may be more generous under a different airline in the same alliance.
- **es passage (start):** Debe elegir cuidadosamente su alianza aérea de viajero frecuente. Aun cuando podría pensar que lo más lógico es unirse a la compañía aérea con la que más viaja, debe saber que los beneficios ofrecidos suelen ser diferentes y que, a veces, los puntos de viajero pueden otorgarle más beneficios en otra aerolínea de la misma alianza.
- **en question:** Based on the passage, when choosing a Frequent Flyer airline in an alliance, which of the following should you prioritize?
- **es question:** Basándose en el fragmento, a la hora de elegir una compañía aérea de vuelos frecuentes en una alianza, ¿cuál de las siguientes se debería priorizar?
- **options en / es:** A) The airline that offers the most points / La aerolínea que ofrece más puntos; B) The airline in the biggest alliance / La aerolínea de la mayor alianza; C) The airline you travel most often / La aerolínea con la que viaja más a menudo; D) The airline that might be adding additional privileges / La aerolínea que podría añadir privilegios adicionales
- **es answer (last 400 chars):** , aunque lo más lógico parezca unirse a la aerolínea con la que más se viaja (opción C), en realidad los beneficios suelen ser diferentes y los puntos de viajero pueden otorgar **más beneficios** en otra aerolínea de la misma alianza. Por lo tanto, lo que se debe priorizar es la aerolínea que podría añadir privilegios adicionales, no simplemente la más usada o la de la mayor alianza. Respuesta: D
- **es reasoning (last 600 chars):** The text is arguing that you shouldn't just pick the airline you fly with most (option C), but rather consider the benefits and privileges that could be offered, possibly even in another airline within the same alliance. This points to option D - the airline that could add additional privileges/benefits. The key phrase is "los puntos de viajero pueden otorgarle más beneficios en otra aerolínea de la misma alianza" - traveler points can grant you more benefits in another airline of the same alliance. This suggests prioritizing the one that could add additional privileges. So the answer is D.

### id=374 es (gold C; parsed B; marker B; qid `https://en.wikivoyage.org/wiki/Cross_country_skiing:1`)

- **en passage (start):** Backpacking by ski: This activity is also called backcountry ski, ski touring or ski hiking. It is related to but usually not involving alpine style ski touring or mountaineering, the latter ones done in steep terrain and requiring much stiffer skis and boots. Think of the skiing route as of a similar hiking route. In good conditions you will be able to cover somewhat greater distances than walking – but only very seldom you will get the speeds of cross country skiing without a heavy backpack in groomed tracks.
- **es passage (start):** Mochilero en esquí: también conocido como esquí de zona rural, de travesía o senderismo en esquí. Si bien vinculan, en general no conlleva practicar el esquí de travesía o el montañismo de estilo alpino, desarrollados en suelos de pendiente pronunciada y con esquís y calzado mucho más rígidos. Imagínese la pista de esquí como una ruta de senderismo. En condiciones satisfactorias, logrará recorrer distancias un poco más largas que si lo hace a pie, pero muy rara vez alcanzará la velocidad del esquí a campo traviesa sin una mochila de buen peso en pistas acondicionadas.
- **en question:** According to the passage, what kind of skiing is done in steeper terrain?
- **es question:** Según el fragmento, ¿qué tipo de esquí se practica en terrenos más escarpados?
- **options en / es:** A) Ski hiking / Esquí de senderismo; B) Backcountry skiing / Esquí de travesía; C) Alpine style / Estilo alpino; D) Backpacking by ski / Esquiar como mochilero
- **es answer (last 400 chars):** ente pronunciada" con "esquís y calzado mucho más rígidos." Esto contrasta con el esquí de mochilero/senderismo, que se practica en condiciones menos escarpadas. La pregunta específicamente busca un "tipo de esquí" practicado en terrenos más escarpados. El texto identifica claramente al **esquí de travesía** como la actividad de esquí desarrollada en suelos de pendiente pronunciada. Respuesta: B
- **es reasoning (last 600 chars):** of skiing). "Montañismo de estilo alpino" is mountaineering, not specifically a type of skiing. "Esquí de travesía" is explicitly a type of skiing. So the answer should be B) Esquí de travesía. Wait, but actually "estilo alpino" could refer to "esquí alpino" (alpine skiing). In Spanish, "esquí alpino" is a well-known type of skiing done on steep slopes. The text says "montañismo de estilo alpino" which is alpine-style mountaineering, not necessarily "esquí alpino." I'll go with B) Esquí de travesía, as it's the most directly mentioned type of skiing practiced on steep terrain in the text.

### id=458 es (gold B; parsed D; marker D; qid `https://en.wikivoyage.org/wiki/Talk:1`)

- **en passage (start):** The world has over 5,000 different languages, including more than twenty with 50 million or more speakers. Written words are often easier to understand than spoken words, also. This is especially true of addresses, which are often difficult to pronounce intelligibly. Many entire nations are completely fluent in English, and in even more you can expect a limited knowledge - especially among younger people. Imagine, if you will, a Mancunian, Bostonian, Jamaican and Sydneysider sitting around a table having dinner at a restaurant in Toronto. They're regaling each other with stories from their hom…
- **es passage (start):** En todo el planeta, existen más de 5000 idiomas distintos, entre los cuales más de veinte son hablados por 50 millones de personas, o más. En general, aquello que se comunica por escrito es más sencillo de comprender que lo que se dice de forma oral. Claro ejemplo de ello es el caso de las direcciones, que muchas veces son difíciles de pronunciar de manera que se entienda. Un alto número de países enteros hablan con total fluidez el inglés y en aún muchos más puede esperarse encontrar cierto conocimiento del idioma, en particular entre los más jóvenes. Imagínese, por dar un ejemplo, a un mancu…
- **en question:** According to the passage, who is most likely to have at least a limited understanding of the English language?
- **es question:** Según el fragmento, ¿quién es más probable que posea un conocimiento limitado de la lengua inglesa?
- **options en / es:** A) People who speak at least two other languages / Personas que hablan al menos otras dos lenguas; B) People younger in age / Personas más jóvenes; C) People traveling to Toronto / Personas que viajan a Toronto; D) People older in age / Personas mayores
- **es answer (last 400 chars):** uede esperarse encontrar cierto conocimiento del idioma, **en particular entre los más jóvenes**". Esto implica que las personas más jóvenes son las que tienen mayor probabilidad de poseer ese conocimiento. Por lo tanto, quienes tendrían un conocimiento más limitado del inglés serían las personas mayores, ya que no se menciona que tengan ese mismo nivel de familiaridad con el idioma. Respuesta: D
- **es reasoning (last 600 chars):** e, not limited knowledge C) People who travel to Toronto - not relevant to language knowledge D) Older people (Personas mayores) - since the text says knowledge is found "in particular among the youngest," it implies that older people would have less/limited knowledge The answer is D) Personas mayores. The logic is: the text specifically mentions that knowledge of English is found "in particular among the youngest" (en particular entre los más jóvenes). This implies that older people (personas mayores) are less likely to have that knowledge, meaning they would have a more limited knowledge.

### id=463 es (gold D; parsed A; marker A; qid `https://en.wikivoyage.org/wiki/Travel_advisories:1`)

- **en passage (start):** If the country you will be visiting becomes subject to a travel advisory, your travel health insurance or your trip cancellation insurance may be affected. You may also wish to consult the advice of governments other than your own, but their advice is designed for their citizens. As one example, American citizens in the Middle East might face different situations from Europeans or Arabs. Advisories are merely a brief summary of the political situation in one country. The views presented are often cursory, general and oversimplified compared to the more detailed information available elsewhere.
- **es passage (start):** Si su país de destino queda sujeto a una alerta de viaje, ello podría afectar su seguro de asistencia médica o el de cancelación de viaje. Es posible que quiera consultar las recomendaciones de otros gobiernos, pero están pensadas para sus propios ciudadanos. Por ejemplo, un visitante norteamericano en Medio Oriente podría enfrentar situaciones distintas a las de un europeo o un árabe. Las advertencias de viaje son tan solo un resumen conciso de la situación política en otro país. Los puntos de vista que se presentan suelen ser superficiales, genéricos y demasiado simplificados en comparación …
- **en question:** According to the passage, from where should a traveler obtain advice regarding the political situation in their destination city?
- **es question:** Según el fragmento, ¿dónde debería asesorarse un viajero sobre la situación política de su ciudad de destino?
- **options en / es:** A) From the government of the country they’ll be visiting / Del gobierno del país que van a visitar; B) From the views presented within the travel advisory / A partir de las opiniones incluidas en la recomendación de viaje; C) From citizens of the country they’ll be visiting / De los ciudadanos del país que van a visitar; D) From their own government / De su propio gobierno
- **es answer (last 400 chars):** luidas en las recomendaciones de viaje por ser superficiales. - **C** no se menciona en el texto. - **D** se descarta porque el texto señala que las advertencias de su propio gobierno son demasiado simplificadas. - **A** es la opción más coherente con el texto, ya que el gobierno del país de destino tendría la información más detallada y específica sobre su propia situación política. Respuesta: A
- **es reasoning (last 600 chars):** warnings are too simplified - Other governments' recommendations are for their own citizens (so not ideal for you) - More detailed info is available "en otros sitios" Given the four options, I think A is the best answer because: - B is explicitly criticized (superficial opinions in travel recommendations) - C is not mentioned - D is what the text is criticizing (your own government's warnings are too simplified) - A represents seeking information from the destination country's government, which would be "otros gobiernos" and would provide more detailed, specific information I'll go with A.

### id=483 es (gold A; parsed D; marker D; qid `https://en.wikivoyage.org/wiki/West_Africa:1`)

- **en passage (start):** In the north the region is bounded by the Sahel, and in the south and west by the Atlantic Ocean. Women: It is recommended that any women travellers say that they are married, regardless of actual marital status. It is helpful to also wear a ring (just not one that looks too expensive. Women should realize that cultural differences may result in what they would consider harassment and it is not uncommon to be followed, grabbed by the arm, etc. Be firm in turning down men, and don't be afraid to stand your ground (cultural differences or not, it doesn't make it ok!).
- **es passage (start):** La región limita con el Sahel al norte, y con el Océano Atlántico al sur y al oeste. Mujeres: Se aconseja que todas las visitantes femeninas digan estar casadas, sin importar cuál sea su estado civil real. Será también de utilidad usar un anillo (solo procure que no luzca demasiado costoso). Las mujeres deben darse cuenta de que las diferencias culturales pueden provocar lo que ellas consideran acoso, y que no es poco común que sean seguidas, tomadas por el brazo, etc. Sea rotunda al rechazar a los hombres y no tema defender su postura (existan diferencias culturales o no, ¡eso no es correcto!…
- **en question:** According to the passage, which of the following would not be a recommended tip for women traveling in the area?
- **es question:** Según el fragmento, ¿cuál de los siguientes no sería un consejo recomendable para las mujeres que viajan por la zona?
- **options en / es:** A) Refrain from discussing martial status / Abstenerse de discutir el estado civil; B) Be aware that cultural differences may instigate forceful behavior from locals / Tener en cuenta que las diferencias culturales pueden instigar un comportamiento agresivo por parte de la población local; C) Avoid wearing flashy jewelry / Evitar llevar joyas llamativas; D) Use toughness when necessary / Utilizar la fuerza cuando sea necesario
- **es answer (last 400 chars):** toso" al referirse al anillo. Esto SÍ es un consejo del texto. - **D)** El texto aconseja ser "rotunda al rechazar a los hombres y no tema defender su postura". No menciona en ningún momento el uso de la fuerza física. Defender la postura es verbal/actitudinal, no implica recurrir a la violencia física. Por lo tanto, utilizar la fuerza NO es un consejo que aparezca en el fragmento. Respuesta: D
- **es reasoning (last 600 chars):** ar la fuerza cuando sea necesario" (Use force when necessary) The text says: "Sea rotunda al rechazar a los hombres y no tema defender su postura (existan diferencias culturales o no, ¡eso no es correcto!)." The advice is to be firm/definitive in rejecting men and not be afraid to defend one's position. It does NOT say to use force. "Defender su postura" (defend your position) is verbal/firm, not physical force. So "using force" is NOT a recommendable advice in the text. Therefore, the answer is D) "Utilizar la fuerza cuando sea necesario" is NOT a recommendable advice according to the text.

### id=68 zh (gold A; parsed B; marker B; qid `https://en.wikibooks.org/wiki/Modern_Photography/Composition:1`)

- **en passage (start):** The much-abused and often-ridiculed rule of thirds is a simple guideline creating dynamism while keeping a measure of order in an image. It states that the most effective place for the main subject is at the intersection of lines dividing the image into thirds vertically and horizontally (see example).
- **zh passage (start):** 经常被滥用和嘲笑的三分法，在创造动态时不失为一种简单的指导方法，还能让图像保持有序。 它指出，对主体来说最有效的位置是将图像垂直和水平分为三部分的线的交叉点（见示例）。
- **en question:** Which of the following is not an object of the rule of thirds?
- **zh question:** 以下哪项不是三分法的对象？
- **options en / zh:** A) Creating a baseline for where the subject might be placed / 创建一个基准，确定主体可能被放置的位置; B) Creating life and energy within a photo / 在照片中营造活力和能量; C) Keeping the subject in a specific and effective place / 将主体保持在特定且有效的位置; D) Establishing order within a photo / 在照片中建立秩序
- **zh answer (last 400 chars):** 根据短文内容，三分法的功能包括： 1. **创造动态**（dynamism） 2. **让图像保持有序** 3. **指出主体最有效的位置**（即九宫格交叉点） 逐项分析： - **A** "创建一个基准，确定主体可能被放置的位置" → 对应"指出主体最有效的位置是交叉点" ✓ - **B** "在照片中营造活力和能量" → 短文说的是"创造**动态**（dynamism）"，而"活力和能量"（vitality and energy）并非短文中表述的含义，"动态"侧重于构图的运动感和节奏，而非"活力与能量" ✗ - **C** "将主体保持在特定且有效的位置" → 对应"对主体来说最有效的位置" ✓ - **D** "在照片中建立秩序" → 对应"让图像保持有序" ✓ 因此，**B** 不是三分法在短文中所描述的对象/功能。 答案：B
- **zh reasoning (last 600 chars):** 是"创造动态"（creating dynamism），而不是"营造活力和能量"。但这似乎太牵强了。 或者，也许答案是A？"创建一个基准"（creating a reference/standard）- 三分法确实提供了交叉点作为参考，但"基准"这个词是否准确？ 再想想，"三分法的对象"可能指的是三分法所针对的东西，即它的目的。 我认为答案是B。因为短文提到的是"创造动态"（dynamism），而选项B说的是"营造活力和能量"（vitality and energy）。虽然相关，但"动态"更侧重于运动和变化的感觉，而"活力和能量"更侧重于生命力和力量。 不过，让我再考虑一下。在摄影构图中，"dynamism"通常就被翻译为"动感"或"动态"，它确实包含活力和能量的含义。 我倾向于选B，因为短文中的用词是"动态"（dynamism），而选项B用的是"活力和能量"，这可能有细微区别。 实际上，让我重新考虑。也许这道题更简单： 短文提到的三分法的功能： 1. 创造动态 2. 让图像保持有序 3. 指出主体最有效的位置（交叉点） A) 确定主体位置 - 对应第3点 ✓ B) 营造活力和能量 - 对应第1点？"动态"≈"活力和能量"？ C) 将主体保持在有效位置 - 对应第3点 ✓ D) 建立秩序 - 对应第2点 ✓ 如果B不完全对应"创造动态"，那B就是答案。 我选B。

### id=106 zh (gold B; parsed A; marker A; qid `https://en.wikibooks.org/wiki/Wikijunior:Big_Cats/Tiger:1`)

- **en passage (start):** A well rounded athlete, the tiger can climb (though not well), swim, leap great distances and pull with five times the force of a strong human. The tiger is in the same group (Genus Panthera) as lions, leopards, and jaguars. These four cats are the only ones who can roar. The tiger's roar is not like the full-voiced roar of a lion, but more like a sentence of snarly, shouted words.
- **zh passage (start):** 老虎是全能运动员，它会攀爬（虽然攀爬能力不是很强）、游泳、跳远，拉力能达到人类大力士的五倍。 老虎与狮、豹和美洲虎属于同一类型（豹属）。这四种大猫是仅有的会吼叫的猫科动物。 老虎的咆哮不像狮子的咆哮那样深沉，而更像一句生气嘶吼的话语。
- **en question:** Which of the following would not be considered a tiger’s greatest strength?
- **zh question:** 以下哪项不被认为是老虎的最大优势？
- **options en / zh:** A) Roaring / 咆哮; B) Climbing / 攀爬; C) Leaping / 跳远; D) Pulling / 拉力
- **zh answer (last 400 chars):** 根据短文，老虎作为"全能运动员"的优势包括：攀爬、游泳、跳远和拉力（达人类大力士的五倍）。 而"咆哮"是在介绍猫科属（豹属）的共性时提到的——四种大猫是唯一会吼叫的猫科动物。文中还特别指出老虎的咆哮"不像狮子的咆哮那样深沉"，只是"更像一句生气嘶吼的话语"，并未将其列为老虎的优势。 因此，咆哮不被认为是老虎的最大优势。 答案：A
- **zh reasoning (last 600 chars):** ned but it's in the context of the cat genus - these four big cats are the only ones that can roar. The passage doesn't describe roaring as a tiger's "advantage" or "strength" - it's more of a characteristic of the genus. Moreover, the passage actually notes that the tiger's roar is NOT as impressive as a lion's roar ("不像狮子的咆哮那样深沉"), suggesting it's not really a strength. The physical advantages listed are: climbing, swimming, jumping, and pulling force. Roaring is not listed among these athletic abilities. So the answer is A) 咆哮 (Roaring) - it's not considered a tiger's greatest advantage.

### id=179 zh (gold B; parsed D; marker D; qid `https://en.wikinews.org/wiki/Bomb_blasts_kill_several_in_Iran:1`)

- **en passage (start):** One bomb exploded outside the governor general's office. Three more bombs exploded near government buildings in a period of two hours. Some reports put the official death toll at eight, and official reports confirm that up to 30 were injured; but final numbers are not yet known.
- **zh passage (start):** 一枚炸弹在总督办公室外爆炸。 两小时内，政府大楼附近又发生了三起炸弹爆炸事件。 一些报道称官方宣布的死亡人数为 8 人，而据官方报道证实，有多达 30 人受伤；但是最终的数字尚未确定。
- **en question:** According to the passage, what information is known following the bombing?
- **zh question:** 根据这段文字，爆炸事件之后已知的信息是什么？
- **options en / zh:** A) The final injury count / 最终的受伤人数; B) Which buildings the bombs exploded near / 炸弹爆炸附近的建筑物; C) If additional bombs were to be detonated / 是否有其他炸弹被引爆; D) The official death toll / 官方死亡人数
- **zh answer (last 400 chars):** 根据短文内容进行分析： - **A) 最终的受伤人数**：文明确指出"最终的数字尚未确定"，因此最终受伤人数**未知**。 - **B) 炸弹爆炸附近的建筑物**：文中仅提到总督办公室和政府大楼作为事发地点，并非爆炸后"已知"的额外信息。 - **C) 是否有其他炸弹被引爆**：文中确实提到又发生了三起爆炸，但这更多是事件经过的描述。 - **D) 官方死亡人数**：文明确指出"官方宣布的死亡人数为 8 人"，这是爆炸事件之后已知的官方信息。 答案：D
- **zh reasoning (last 600 chars):** s 8 in the text. This is the most direct "information" that is reported. Actually, I'll reconsider one more time. Let me look at this from a test-taking perspective. A) Final injured number - explicitly NOT known B) Buildings near explosion - not really the focus of "information after the event" C) Whether other bombs were detonated - YES, clearly stated D) Official death toll - YES, stated as 8 I think D is the intended answer because it's a specific piece of numerical information that was officially announced. The passage's main "information" content is about casualties. I'll go with D.

### id=219 zh (gold B; parsed A; marker A; qid `https://en.wikinews.org/wiki/Gas_explosion_reported_in_Hammersmith,_London:1`)

- **en passage (start):** According to reports, an apartment on Macbeth Street exploded due to a gas leak. An official with the gas company was reporting to the scene after a neighbor called about a gas leak. When the official arrived, the apartment exploded. No major injuries were reported, but at least five people on scene at the time of the explosion were treated for symptoms of shock. No one was inside the apartment. At the time, nearly 100 residents were evacuated from the area.
- **zh passage (start):** 据报道，麦克白大街（Macbeth Street）的一间公寓因煤气泄漏而发生爆炸。 在一位邻居打电话称发生煤气泄漏之后，煤气公司的一名高级职员在现场进行汇报。 官员到达后，公寓发生了爆炸。 据报告并没有发生重大伤亡，但至少有5 人因身处爆炸现场而出现休克症状，接受了治疗。 公寓里没有人。 当时，该地区有近 100 名居民被疏散。
- **en question:** Following the explosion, who was treated for serious injuries?
- **zh question:** 爆炸发生后，谁因为严重的伤势接受了治疗？
- **options en / zh:** A) At least five people / 至少五个人; B) No one / 没有人; C) A gas company official / 一名煤气公司职员; D) A neighbor / 一位邻居
- **zh answer (last 400 chars):** 根据短文内容："据报告并没有发生重大伤亡，但至少有5人因身处爆炸现场而出现休克症状，接受了治疗。" 明确提到至少有5人接受了治疗（因休克症状）。 答案：A
- **zh reasoning (last 600 chars):** 没有人"。如果严格按照"严重伤势"来说，可能答案是B，因为没有重大伤亡，只是休克。 但再想想，问题是"谁因为严重的伤势接受了治疗？"，而短文明确说"至少有5人...接受了治疗"。虽然伤势是休克而非"重大伤亡"，但他们确实接受了治疗。 实际上，仔细再看问题："谁因为严重的伤势接受了治疗？" 短文说："据报告并没有发生重大伤亡，但至少有5人因身处爆炸现场而出现休克症状，接受了治疗。" 这里的关键是：5人接受了治疗，但原因是"休克症状"，不是"严重伤势"。而且明确说"没有发生重大伤亡"。 所以如果问题问的是"严重的伤势"，答案可能是B（没有人），因为没有重大伤亡。 但等等，让我重新考虑。这道题可能是中文阅读理解题，考察的是对短文信息的理解。问题可能用"严重的伤势"来指代那些需要治疗的情况。 再看一遍：问题是"谁因为严重的伤势接受了治疗？" 选项A说"至少五个人"接受了治疗 - 这与短文一致，5人接受了治疗。 选项B说"没有人" - 这与短文矛盾，因为5人确实接受了治疗。 虽然短文说"没有发生重大伤亡"，但5人确实"接受了治疗"。问题中的"严重的伤势"可能只是对"休克症状"的一种描述，或者问题本身在问谁接受了治疗。 我认为答案是A，因为短文明确指出"至少有5人...接受了治疗"。问题可能用"严重的伤势"来概括"休克症状"（休克确实是一种严重的状况）。 答案应该是A。

### id=230 zh (gold A; parsed C; marker C; qid `https://en.wikinews.org/wiki/Hungary%27s_St_Stephen%27s_Day_hit_by_storm:_3_left_dead:1`)

- **en passage (start):** "Five minutes into the display a wind starts rolling in, about a minute later, the wind is reaching 70km/h... then the rain comes, but so hard and so large that it slaps your skin like a needle, then hail fell from the sky, people panicking and screaming and running over each other. I lost my sister and her friend, and on my way there were two disabled people in wheelchairs, people just jumping over and pushing them,"" Armand Versace said."
- **zh passage (start):** 表演开始五分钟后，刮起了风，约一分钟后，风速达到了 70 公里/小时……紧接着又下起了雨，雨势如此之大，像针扎一样拍打在皮肤上，随后天上下起了冰雹，惊慌失措的人群尖叫着四散奔逃。 “我姐姐和她的朋友不见了，路上有两个残疾人坐着轮椅，有人跳过去帮他们推轮椅”，阿尔芒·范思哲说道。
- **en question:** According to Armand Versace’s account, what occurred directly before the crowd began to react to the weather?
- **zh question:** 根据阿尔芒·范思哲的描述，在人群开始对天气做出反应之前，发生了什么？
- **options en / zh:** A) It started to hail / 下起了冰雹; B) The display was running five minutes behind / 表演晚了五分钟; C) There were heavy winds / 刮起了大风; D) He lost track of a family member / 他的一个家人不见了
- **zh answer (last 400 chars):** 根据短文的描述，事件顺序为： 1. 表演开始五分钟后，**刮起了风** 2. 约一分钟后，风速达到70公里/小时 3. 紧接着下起了大雨 4. 随后下起了冰雹 5. 惊慌失措的人群尖叫着四散奔逃（人群对天气做出反应） 在人群开始恐慌奔逃之前，最先发生的天气事件是刮起了大风，它是整个恶劣天气的起点。 选项B"表演晚了五分钟"文中未提及；选项D"家人不见了"是混乱中发生的事情，而非之前；选项A冰雹虽然也在人群反应前，但它是后续事件，而"刮起了大风"是最先触发整系列事件的原因。 答案：C
- **zh reasoning (last 600 chars):** the wind. I'll go with C) 刮起了大风. Wait, actually I need to think about this differently. The question might be testing whether the student understands the sequence. The wind started 5 minutes after the performance began. The crowd's reaction happened after all the weather events. So "before the crowd started reacting," the wind had already been blowing (and rain and hail). I think the answer is C because the wind was the first and primary weather event that triggered everything. The crowd was reacting to the overall weather situation, and the wind was the initial event. Let me go with C.

### id=268 zh (gold A; parsed C; marker C; qid `https://en.wikinews.org/wiki/New_Australian_Prime_Minister_signs_Kyoto:1`)

- **en passage (start):** Mr. Rudd's decision to sign the Kyoto climate accord isolates the United States, which will now be the only developed nation not to ratify the agreement. Australia's former conservative government refused to ratify Kyoto, saying it would damage the economy with its heavy reliance on coal exports, while countries like India and China were not bound by emissions targets.
- **zh passage (start):** 陆克文先生决定签署《京都气候议定书》，这使得美国成为唯一没有签署该协议的发达国家。 澳大利亚前保守党政府拒绝签署《京都议定书》，声称由于澳大利亚严重依赖煤炭出口，该协议会削弱澳大利亚的经济，而印度和中国等国却未受排放目标的约束。
- **en question:** As stated in the passage, which nation is affected by the signing of the Kyoto climate accord?
- **zh question:** 根据这段文字，哪个国家受到了《京都气候议定书》签署的影响？
- **options en / zh:** A) United States / 美国; B) India / 印度; C) Australia / 澳大利亚; D) China / 中国
- **zh answer (last 400 chars):** 根据短文分析： - **澳大利亚**：陆克文决定签署《京都气候议定书》，前政府也声称该协议会"削弱澳大利亚的经济"。澳大利亚作为签署国，直接受到该协议的约束和影响。 - **美国**：成为"唯一没有签署该协议的发达国家"，是未签署方。 - **印度和中国**：文中明确指出它们"未受排放目标的约束"。 因此，直接受到《京都气候议定书》签署影响的国家是澳大利亚。 答案：C
- **zh reasoning (last 600 chars):** 经济——澳大利亚直接受到影响（签署了协议，需要执行）。 - 美国：因为澳大利亚签署了，美国成为"唯一没有签署的发达国家"——这也是一种影响。 - 印度和中国：未受排放目标约束——这是说它们没有受到影响。 但问题问的是"受到签署的影响"。从文中来看，澳大利亚是签署该协议的国家，直接受到影响。美国则是因为澳大利亚的签署行为而成为"唯一没有签署的发达国家"，这也算是一种影响。 但再仔细看，问题问的是"哪个国家受到了《京都气候议定书》签署的影响"。 实际上，澳大利亚签署了该协议，所以澳大利亚受到了影响（需要执行减排目标）。美国因为没有签署而不受约束。印度和中国也没有受到排放目标的约束。 所以答案应该是C) 澳大利亚，因为它是签署该协议的国家，直接受到了协议的影响。 等等，让我再想想。文中说"这使得美国成为唯一没有签署该协议的发达国家"——这意味着美国受到了影响（被凸显出来）。 但从整体来看，澳大利亚是主动签署的国家，直接受到协议约束和影响。前政府也声称协议会"削弱澳大利亚的经济"。 我认为答案是C) 澳大利亚。 实际上再想想，问题可能更侧重于"签署"这个行为带来的影响。陆克文签署后，美国成为唯一未签署的发达国家。所以美国受到了"影响"（被孤立/凸显）。 但澳大利亚本身签署了协议，直接受到协议的约束和影响。 我倾向于选C) 澳大利亚，因为它是直接签署并受协议约束的国家。

### id=331 zh (gold D; parsed A; marker A; qid `https://en.wikinews.org/wiki/US_President_Trump_announces_troop_withdrawal_from_Syria:1`)

- **en passage (start):** Late on Sunday, the United States President Donald Trump, in a statement delivered via the press secretary, announced US troops would be leaving Syria. The announcement was made after Trump had a phone conversation with Turkish President Recep Tayyip Erdoğan. Turkey would also take over guarding captured ISIS fighters which, the statement said, European nations have refused to repatriate.
- **zh passage (start):** 周日晚些时候，美国总统唐纳德·特朗普通过新闻秘书发表声明，宣布美军将撤离叙利亚。 特朗普与土耳其总统雷杰普·塔伊普·埃尔多安（Recep Tayyip Erdoğan）通话后发表了声明。 该声明称，土耳其还将接管对被捕的伊斯兰国武装分子的看守任务；欧洲国家拒绝将他们遣送回国。
- **en question:** Who delivered the statement regarding the US troops?
- **zh question:** 谁发表了关于美军的声明？
- **options en / zh:** A) Donald Trump / 唐纳德·特朗普; B) Tayyip Erdoğan / 塔伊普·埃尔多安; C) ISIS fighters / 伊斯兰国武装分子; D) The press secretary / 新闻秘书
- **zh answer (last 400 chars):** 根据短文，"美国总统唐纳德·特朗普**通过**新闻秘书**发表**声明，宣布美军将撤离叙利亚。"这句话的主语是特朗普，新闻秘书只是代为发布的渠道。因此，发表声明的人是唐纳德·特朗普。 答案：A
- **zh reasoning (last 600 chars):** 用户问的是"谁发表了关于美军的声明？" 让我仔细阅读原文： "周日晚些时候，美国总统唐纳德·特朗普通过新闻秘书发表声明，宣布美军将撤离叙利亚。" 这句话的主语是"美国总统唐纳德·特朗普"，他"通过新闻秘书发表声明"。所以声明是特朗普发表的，新闻秘书只是代为发布的渠道。 问题问的是"谁发表了关于美军的声明？" A) 唐纳德·特朗普 - 他是声明的发布者（通过新闻秘书） B) 塔伊普·埃尔多安 - 他只是通话对象 C) 伊斯兰国武装分子 - 无关 D) 新闻秘书 - 是代为发表的渠道 从原文来看，"特朗普通过新闻秘书发表声明"，主语是特朗普，新闻秘书是工具/渠道。所以答案应该是A) 唐纳德·特朗普。 但等等，让我再仔细看看。"通过新闻秘书发表声明"——这句话的结构是"特朗普（主语）通过新闻秘书（方式）发表声明（谓语）"。所以声明者是特朗普。 答案是A。

### id=335 zh (gold D; parsed A; marker A; qid `https://en.wikinews.org/wiki/War_between_top_lawyers_in_Greece:1`)

- **en passage (start):** "The famous Greek lawyers, Sakis Kechagioglou and George Nikolakopoulos have been imprisoned in the Athens' jail of Korydallus, as they were found guilty of graft and corruption. As a result of this, a big scandal within the Greek legal community has been raised through the exposure of illegal actions that judges, lawyers, solicitors and attorneys have done during the previous years. A few weeks ago, after the information published by the journalist Makis Triantafylopoulos in his popular Television show ""Zoungla"" in Alpha TV, the member of Parliament and lawyer, Petros Mantouvalos was abdica…
- **zh passage (start):** 希腊著名律师萨基斯·科查吉欧格鲁 (Sakis Kechagioglou) 和乔治·尼可拉考普洛斯 (George Nikolakopoulos) 因被判贪污和腐败被关押在雅典的 Korydallus 监狱。 因此，随着法官、律师、法务官和检察官前几年的非法勾当曝光于世，在希腊法律界引发了一场大丑闻。 几周前，议员兼律师马基斯·特里安塔菲洛普洛斯在阿尔法电视台的热门电视节目《Zoungla》中公布了这一消息，随后彼得罗斯·曼图瓦洛斯因其办公室成员涉嫌非法贪污受贿而被革职。 此外，最高法官埃万杰洛斯·卡卢西斯因腐败和堕落行为被判入狱。
- **en question:** Which of the following people is not a lawyer?
- **zh question:** 以下哪位不是律师？
- **options en / zh:** A) Petros Mantouvalos / 彼得罗斯·曼图瓦洛斯; B) Sakis Kechagioglou / 萨基斯·科查吉欧格鲁; C) George Nikolakopoulos / 乔治·尼可拉考普洛斯; D) Makis Triantafylopoulos / 马基斯·特里安塔菲洛普洛斯
- **zh answer (last 400 chars):** 根据短文逐一分析各选项： - **B) 萨基斯·科查吉欧格鲁**：文中明确称其为"希腊著名律师"。✓ 是律师 - **C) 乔治·尼可拉考普洛斯**：与萨基斯并列，同被描述为律师。✓ 是律师 - **D) 马基斯·特里安塔菲洛普洛斯**：文中称其为"议员兼律师"。✓ 是律师 - **A) 彼得罗斯·曼图瓦洛斯**：文中仅提到他"因其办公室成员涉嫌非法贪污受贿而被革职"，并未称其为律师。✗ 不是律师 答案：A
- **zh reasoning (last 600 chars):** 室成员涉嫌非法贪污受贿而被革职" - Petros Mantouvalos was dismissed because his office members were suspected of illegal corruption. He is not described as a lawyer. Wait, but the passage mentions "法官、律师、法务官和检察官" (judges, lawyers, legal officers, and prosecutors) in the context of the scandal. Petros Mantouvalos is not specifically identified as a lawyer in the text. He seems to be someone whose office members were involved in corruption. He could be a judge, prosecutor, or other legal official, but not explicitly a lawyer. So the answer is A) 彼得罗斯·曼图瓦洛斯, as he is not identified as a lawyer in the passage.

### id=376 zh (gold C; parsed B; marker B; qid `https://en.wikivoyage.org/wiki/Dangerous_animals:1`)

- **en passage (start):** Moose (also known as elk) aren't inherently aggressive, but will defend themselves if they perceive a threat. When people don't see moose as potentially dangerous, they may approach too closely and put themselves at risk.
- **zh passage (start):** 驼鹿（也被称为麋鹿）天生不具攻击性，但如果感觉到威胁它们也会自卫。 有些人不把驼鹿当成潜在的危险，可能会靠得太近，将自己置于危险之中。
- **en question:** Which of the following should people avoid doing with moose?
- **zh question:** 人们应该避免对驼鹿做以下哪种事情？
- **options en / zh:** A) Ignoring their presence / 忽略它们的存在; B) Approaching too slowly / 慢慢地接近它们; C) Minimizing their potential threat level / 减少它们的潜在威胁程度; D) Observing them from a distance / 在远处观察它们
- **zh answer (last 400 chars):** 根据短文，驼鹿虽然天生不具攻击性，但如果感到威胁会自卫。文中特别指出，有些人不把驼鹿当成潜在危险，可能会"靠得太近，将自己置于危险之中"。 因此，人们应该避免的事情是接近驼鹿（靠得太近）。 - A) 忽略它们的存在 —— 文中未强调这是核心危险行为。 - B) 慢慢地接近它们 —— 正对应文中"靠得太近"的危险。 - C) 减少它们的潜在威胁程度 —— 这不是需要避免的事。 - D) 在远处观察它们 —— 这是安全的做法。 答案：B
- **zh reasoning (last 600 chars):** - The passage says people "might get too close, putting themselves in danger." This directly relates to approaching moose too closely. C) 减少它们的潜在威胁程度 (Reduce their potential threat level) - This doesn't make sense as something to avoid. Reducing threat level would be a good thing. D) 在远处观察它们 (Observe them from a distance) - This is actually the safe thing to do, not something to avoid. The passage clearly states that people may "靠得太近" (get too close) and put themselves in danger. So the answer is B - people should avoid slowly approaching moose (getting too close to them). The answer is B.

### id=389 zh (gold C; parsed B; marker B; qid `https://en.wikivoyage.org/wiki/French_phrasebook:1`)

- **en passage (start):** The varieties of French which are spoken in Belgium and Switzerland differ slightly from the French spoken in France, though they are similar enough to be mutually intelligible. In particular, the numbering system in French-speaking Belgium and Switzerland has some slight peculiarities that are different from the French spoken in France, and the pronunciation of some words is slightly different. Nevertheless, all French-speaking Belgians and Swiss would have learned standard French in school, so they would be able to understand you even if you used the standard French numbering system.
- **zh passage (start):** 比利时和瑞士使用的法语语种与法国使用的法语尽管非常相似，可以互通，但还是稍有不同。 具体说来，比利时和瑞士讲的法语在数字系统上有一些细微的特殊性，与法国讲的法语不同，一些单词的发音也略有不同。 不过，所有说法语的比利时人和瑞士人都会在学校里学习标准法语，所以即使您使用标准的法国度量系统，他们也能听得懂。
- **en question:** Which of the following might not be understood by French-speaking Belgians and Swiss?
- **zh question:** 哪项可能不为说法语的比利时人和瑞士人所理解？
- **options en / zh:** A) The standard French numbering system / 标准的法国度量系统; B) Peculiar French words / 特殊的法语单词; C) Certain pronunciations of French words / 一些法语单词的发音; D) Most French spoken in France / 在法国讲的大部分法语
- **zh answer (last 400 chars):** 根据短文分析： - 短文明确指出"即使您使用标准的法国度量系统，他们也能听得懂"→ 排除A - 短文说两者法语"非常相似，可以互通"→ 大部分法语他们能理解 → 排除D - 短文说发音"略有不同"，但仍可互通 → 排除C - 短文提到比利时和瑞士的法语在数字系统上有"细微的特殊性"，说明各方都有自己独特的非标准表达。"特殊的法语单词"（即非标准、特有的表达）可能不被对方理解。 答案：B
- **zh reasoning (last 600 chars):** 。这道题问的是"可能不为...所理解"。 A) 标准法国度量系统 - 明确说能理解 B) 特殊的法语单词 - 短文没有直接提到这个 C) 一些法语单词的发音 - 发音不同，但"略有不同"意味着可能还是能理解 D) 在法国讲的大部分法语 - 能互通，能理解 实际上，我认为答案是B。因为短文提到比利时和瑞士的法语在数字系统上有"细微的特殊性"，这意味着他们使用一些特殊的表达方式。如果问题是"什么可能不被他们理解"，那么： 等等，我重新理解题目。问题是"哪项可能不为说法语的比利时人和瑞士人所理解？" 意思是：如果你说某样东西，比利时/瑞士的法语使用者可能听不懂。 A) 如果你用标准的法国度量系统跟他们说 - 他们能懂 B) 如果你用"特殊的法语单词"跟他们说 - 这里"特殊"可能指非标准的、特殊的表达 C) 如果你用"一些法语单词的发音" - 这个不太合理 D) 如果你用"在法国讲的大部分法语" - 他们能懂 我认为答案是B。因为短文说比利时和瑞士的法语有一些"细微的特殊性"，这意味着他们有一些自己独特的表达方式。反过来，如果法国人使用一些"特殊的法语单词"（即法国特有的非标准表达），比利时和瑞士人可能不太理解。 但等等，短文说"所有说法语的比利时人和瑞士人都会在学校里学习标准法语"，所以标准法语他们都能理解。"特殊的法语单词"如果不是标准的，他们可能不理解。 我选B。

### id=471 zh (gold C; parsed A; marker A; qid `https://en.wikivoyage.org/wiki/Travelling_around_the_Schengen_Area:1`)

- **en passage (start):** Europe is a continent that is relatively small but with many independent countries. Under normal circumstances, travelling through multiple countries would mean having to go through visa applications and passport control multiple times. The Schengen zone, however, works somewhat like one country in this respect. As long as you stay in this zone, you can generally cross borders without going through passport control checkpoints again. Similarly, by having a Schengen visa, you do not need to apply for visas to each of the Schengen member countries separately, hence saving time, money and paperwo…
- **zh passage (start):** 欧洲是片面积相对较小但有着许多独立国家的大陆。在通常情况下，穿越多个国家旅行意味着必须多次经历签证申请和护照检查。 然而在这方面，申根区有点像一个国家。 只要你在此区域居留，通常可以直接通过边境，无需再次接受护照检查点的检查。 同理，有了申根签证，你就不必分别向每个申根成员国申请签证，从而节省了时间、金钱和手续。
- **en question:** Which of the following is an advantage of traveling within the Schengen zone?
- **zh question:** 在申根区内旅行的好处是什么？
- **options en / zh:** A) Avoiding multiple visa applications / 避免多次签证申请; B) Saving money / 省钱; C) Avoiding multiple passport control checkpoints / 避免多个护照检查站; D) No passport requirement / 不需要护照
- **zh answer (last 400 chars):** 根据短文内容，申根区的主要好处包括： - 无需再次接受护照检查点的检查（避免多个护照检查站） - 不必分别向每个申根成员国申请签证（避免多次签证申请） - 节省了时间、金钱和手续 选项分析： - A) 避免多次签证申请 ✓ 文中明确提到 - B) 省钱 ✓ 是附带好处，但不是最核心的 - C) 避免多个护照检查站 ✓ 文中提到 - D) 不需要护照 ✗ 文中未说不需要护照，只是说无需再次接受检查 本题问的是"在申根区内旅行"的核心好处，短文重点强调的核心便利是：有了申根签证，不必分别向每个成员国申请签证。这是申根区最本质的优势。 答案：A
- **zh reasoning (last 600 chars):** 区允许你用一个签证通行所有成员国 - "不必分别向每个申根成员国申请签证"是最主要的简化 - C虽然也提到了，但"避免多个护照检查站"也是好处 等等，我再看看。如果这是阅读理解题，通常答案会涵盖文中主要提到的点。文中提到两个主要好处：1）无需护照检查；2）无需多次签证申请。 但选项是单选...让我看看哪个选项最准确。 A) 避免多次签证申请 - 准确 B) 省钱 - 是附带好处，不是主要好处 C) 避免多个护照检查站 - 准确 D) 不需要护照 - 不准确 我觉得这道题可能答案是A，因为"避免多次签证申请"是申根区最核心的好处，也是短文重点强调的（"同理"后面的总结）。 但实际上，C也是正确的。如果是单选，我倾向于选A，因为它是申根区最核心的概念。 等等，让我再想想。"在申根区内旅行"的好处...旅行过程中，你不需要在每个边境接受护照检查，这是旅行中直接的好处。而签证申请是旅行前的准备。 我最终倾向于选C，因为问题问的是"旅行"的好处，而C直接描述了旅行中的便利。 但再想想，A也是旅行相关的好处（虽然是在旅行前）。 我觉得这道题答案应该是A。因为短文的主旨是介绍申根区如何简化跨国旅行，而"避免多次签证申请"是最核心的简化。 实际上，我重新审视一下，这道题可能答案是A。因为： - 短文说"不必分别向每个申根成员国申请签证" - 这是申根区最核心的好处 我选A。

### id=479 zh (gold C; parsed A; marker A; qid `https://en.wikivoyage.org/wiki/War_zone_safety:1`)

- **en passage (start):** Anyone planning a visit to a country that could be considered a war zone should get professional training. A search of the Internet for 'Hostile environment course' will probably provide the address of a local company. A course will normally cover all the issues discussed here in far greater detail, usually with practical experience. A course will normally be from 2-5 days and will involve role play, a lot of first aid and sometimes weapons training. Books and magazines dealing with wilderness survival are common, but publications dealing with war zones are few.
- **zh passage (start):** 任何计划前往可能被认为战区国家之人，都应该接受专业训练。 在互联网上搜索“应对敌对环境课程”，也许能找到提供培训的当地公司的地址。 这门课程通常会涵盖在此讨论到的所有问题，经常会以实战经验的方式加以深入。 课程训练通常要持续 2-5 天，将涉及角色扮演、急救方式训练，有时也涉及武装训练。 关于野外生存的书籍和杂志很常见，但关于战区生存的出版物却很少。
- **en question:** According to the passage, which of the following issues is most likely to not be covered in a professional training class or in publications?
- **zh question:** 根据这段文字，以下哪个问题最可能没有涵盖在专业培训课程或出版物中？
- **options en / zh:** A) Wilderness survival / 野外生存; B) First aid preparedness / 急救准备; C) War zone readiness / 战区准备; D) Role playing / 角色扮演
- **zh answer (last 400 chars):** 根据短文分析： - **B) 急救准备**：课程中明确提到"急救方式训练"，有涵盖。 - **C) 战区准备**：课程核心主题就是"敌对环境"，且"涵盖在此讨论到的所有问题"，有涵盖。 - **D) 角色扮演**：课程中明确提到"将涉及角色扮演"，有涵盖。 - **A) 野外生存**：虽然"关于野外生存的书籍和杂志很常见"，但这些是通用出版物，而专业培训课程是针对"敌对环境"（战区）的，并不以野外生存为核心内容。在专业培训课程的语境中，野外生存最可能没有被涵盖。 答案：A
- **zh reasoning (last 600 chars):** 是关于敌对环境的，而野外生存是一个更广泛的主题，虽然出版物中有，但在"专业培训课程"的语境中，野外生存可能不是核心内容。而且问题问的是"最可能没有涵盖"，A是最弱的链接。 不，等等。让我重新考虑。 问题："以下哪个问题最可能没有涵盖在专业培训课程或出版物中？" 如果"或"表示两者中任何一个有就算有： - A) 野外生存：出版物有 → 有 - B) 急救准备：课程有 → 有 - C) 战区准备：课程有 → 有 - D) 角色扮演：课程有 → 有 所有都有？这不太对。 也许"或"在这里不是逻辑或，而是"和"的意思（中文中"或"有时表示列举）。即"专业培训课程和出版物"。 如果是"和"： - A) 野外生存：出版物有，课程不确定 - B) 急救准备：课程有，出版物不确定 - C) 战区准备：课程有，出版物很少 - D) 角色扮演：课程有，出版物不确定 这样A最可能"没有"在课程中涵盖（课程是关于敌对环境的），而C最可能"没有"在出版物中涵盖。 但问题问的是"最可能没有涵盖在专业培训课程或出版物中"，我理解为"在培训课程中或出版物中，最可能没有被涵盖的"。 我觉得答案是A。因为： 1. 专业培训课程是关于"敌对环境"的，不涉及野外生存 2. 虽然野外生存的书籍杂志常见，但那些不是"专业"出版物（它们是通用的） 3. B、C、D都在专业培训课程中明确被提及 最终我选A。

