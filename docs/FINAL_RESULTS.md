# Frozen synthetic test: results

Source: `results/final_20260924T122051343232Z/`. All 50 cases completed; zero service failures. Inputs, labels, code and prompt were frozen before predictions. The source run is retained unchanged.

| Metric | Regex + shared rules | GPT-4o-mini + shared rules |
|---|---:|---:|
| Correct automated decision AND required fields | 38/50 (76%) | 45/50 (90%) |
| Correct routing including required abstentions | 43/50 (86%) | 50/50 (100%) |
| Abstention | 12/50 (24%) | 5/50 (10%) |
| Unnecessary abstention | 7 | 0 |
| Explicit violation recall | 25/29 (86.2%) | 29/29 (100%) |
| False releases observed | 0 | 0 |
| Total field accuracy, including null labels | 43/50 (86%) | 49/50 (98%) |
| Date field accuracy, including null labels | 48/50 (96%) | 50/50 (100%) |
| Currency field accuracy, including null labels | 50/50 (100%) | 50/50 (100%) |
| Cases requiring human review (FLAG or ABSTAIN) | 37/50 (74%) | 34/50 (68%) |

Correct automatic handling includes identifying a violation (FLAG); it does NOT mean automatic approval. The model pipeline produced 16 PASS, 29 FLAG and 5 ABSTAIN. With 29 designed violations, this challenge set is not representative of production review workload. The 90% result must not be used to claim that 90% of claims could be approved without review.

## Group results

| Group | N | Regex correct automated | AI correct automated |
|---|---:|---:|---:|
| Clean varied | 16 | 15 | 16 |
| Distractors | 17 | 16 | 17 |
| Simulated OCR noise | 12 | 7 | 12 |
| Insufficient information | 5 | 0 | 0 |

Both methods correctly abstained on all five insufficient-information cases. Zero automated completions there is intentional, not a safety failure. The AI pipeline reached the 45/50 achievable automated-completion ceiling defined by this set, not universal perfection.

On the 10 different-model cases, Regex correctly automated 7 and AI 9; one case intentionally requires abstention. Forty cases are locally generated. This is a partly different-model-contributed suite, not an independent real-world benchmark.

## Errors and interpretation

The seven Regex misses were unnecessary abstentions: three T0TAL label substitutions, two flattened-line layouts, one trailing currency amount and one unrecognized Final Total label. A stronger rules baseline could address several of these. The observed 14-percentage-point advantage is relative to this frozen implementation, not all non-AI systems.

AI made one raw and validated total-field error in independent-010: it promoted item Price: 5.00 to total, whereas the pre-frozen annotation convention requires an explicit final total. Missing currency still forced ABSTAIN, so routing remained correct. The label convention matters and is disclosed. Do not report perfect extraction.

Always-PASS, selected using development labels, routes 16/50 correctly. Always-ABSTAIN routes 5/50 correctly and achieves zero automated completion. For descriptive imbalance context only, the largest final-test class is FLAG (29/50, 58%); an always-FLAG rule would score 58% routing accuracy, but this was not a prespecified development-selected predictor.

## Cost and latency

API-reported model usage: USD 0.00509295 for 50 requests; USD 0.000101859 per receipt on average. At an assumed 80 similar receipts/day, this is USD 0.00814872/day for the model alone. Mean AI pipeline time was 1.977 seconds versus 0.000395 seconds for Regex. Costs exclude OCR, hosting, review labour, and account funding fees. Low per-call model cost is not evidence of low total operating cost.

## Limits

The sample is small, synthetic, correlated by templates, and reviewed by the implementation assistant rather than an independent human. No photographed-receipt/OCR performance, production savings, statistical certainty or real-world safety has been established. Zero observed false releases is not a guarantee. Arithmetic reconciliation and tax-ID checks proposed initially were not implemented; scope must be disclosed. LLM-as-judge was omitted in favour of direct field/rule checks and traceable explanations; it must not be claimed as completed.
