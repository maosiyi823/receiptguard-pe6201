# Development experiment findings

Source: `results/development_20260924T120434935194Z/summary.json` and `cases.jsonl`.
Dataset: 14 synthetic development cases, used during implementation. Not an independent test set. No final generalization claim is supported.

## Observed results

| Metric | Regex + rules | AI + rules |
|---|---:|---:|
| Correct automated handling | 8/14 (57.14%) | 9/14 (64.29%) |
| Correct final routing, including abstention | 13/14 (92.86%) | 14/14 (100%) |
| Abstentions | 6/14 | 5/14 |
| Unnecessary abstentions | 1 | 0 |
| False releases | 0 | 0 |
| Date field correctness, including null | 14/14 | 14/14 |
| Currency field correctness, including null | 14/14 | 13/14 |
| Total field correctness, including null | 13/14 | 13/14 |

Five cases require abstention under the development labels. Nine are answerable. Both systems correctly classified all three explicit policy violations. An always-PASS routing reference scores 6/14; always-ABSTAIN scores 5/14 for routing and zero for automated completion. These figures describe a deliberately constructed small suite, not deployment prevalence.

## Case analysis

### dev12: AI recovers a noisy total label
Input contains `T0TAL: 12.50`. Regex returns a missing total and abstains. AI extracts 12.50 and correctly returns PASS. This is one observed robustness improvement, not proof that AI universally outperforms rules. A reasonable Regex implementation could also handle this particular substitution.

### dev07: unsupported currency guess
Input only contains `$10.00`. The expected currency is null. AI returns USD while also reporting currency ambiguity. Final ABSTAIN is correct, but the extracted currency is incorrect. A schema-valid response and a correct final status do not establish correct fields. Substring evidence alone also cannot validate a currency interpretation.

### dev08: conflicting totals
Input contains both `Total: 10.00` and `Total: 18.00`. The expected total is null. AI selects 18.00 but records `ambiguous_total`. The pipeline abstains, preventing automatic approval. The extracted total remains wrong and is counted as such.

## Cost and latency

All 14 calls completed without service failures. API-reported cost totals USD 0.0012084; mean USD 0.0000863143 per receipt. Mean measured AI attempt time is 1.866 seconds. Multiplying this observed model-only average by the assumed 80 receipts/day gives USD 0.00690514/day. This is a small-sample scenario estimate; it excludes OCR, hosting, human review, account funding fees and future pricing changes. It is not a production budget guarantee.

## Next actions before final evaluation

1. Strengthen missing/ambiguous-value instructions; explicitly prohibit pairing a guessed field with an ambiguity warning.
2. Consider deterministic evidence checks that prevent unsupported currency assertions, applying the same rule to both extractors.
3. Retain original results unchanged; any revised prompt/code must have a new version and new run record.
4. Review the reasonableness of the Regex baseline without using final candidate scores to tune it.
5. Obtain independently contributed cases and review labels before freezing the final evaluation set.

No prediction has been run on the 50 candidate test cases. No field labels have been changed in response to development predictions.

## Shared validation revision v0.2

After inspecting development failures, the common validator now clears unsupported/conflicting currencies and conflicting explicitly labelled final totals. The checks apply identically to both extractors. Original fields are preserved as `raw_fields`; the source experiment is unchanged. The currency check uses an explicitly limited list of supported currency markers. The total-conflict check covers explicit line-based labels; it is not a general semantic ambiguity detector.

Offline replay of the archived v1 outputs corrected the two normalized AI field errors without changing final routing (9/14 correctly automated, 14/14 routing correct). These are post-processing results on known development cases, NOT newly improved model predictions or final test performance. Raw AI field errors remain part of the original findings. The replay file records its source and validator hashes and reports zero API calls.

Prompt v2 adds explicit instructions to output null rather than a guessed value accompanied by a warning. It has NOT yet been tested in a new API run. A new development run must retain its own prompt hash and timestamp; do not overwrite the initial run. Final comparisons should report both raw and validated field results so guardrail improvements are not misattributed to the model.

## Live prompt v2 verification (2026-09-24)

Source: `results/development_20260924T121101736093Z/` (14/14 completed, no service failures).

V2 did not improve aggregate development field accuracy: date 14/14, currency 13/14, total 13/14, and automated completion 9/14. Routing remained 14/14 with no false releases. The error mechanism changed:

- dev07: the model stopped guessing USD, correctly leaving currency null, but unnecessarily discarded the visible total 10.00.
- dev08: the model stopped choosing a conflicting total, correctly leaving total null, but unnecessarily discarded the explicit SGD currency.
- dev12: the model continued to recover 12.50 from T0TAL.

Thus stronger abstention instructions reduced guessing in these cases but introduced excessive field omission. Do not describe the new prompt as more accurate. One run per prompt cannot separate prompt effects from generation variability; this is an observed development trade-off, not a causal or statistical conclusion.

V2 API-reported total cost was USD 0.001347 for 14 calls, with mean attempt time 1.899 seconds. The earlier v1 cost figures remain historical observations. No further prompt iteration is justified solely to maximize the same small development set. Retain v2 as the current conservative configuration, record its limitations, and move to independently contributed data and final evaluation preparation. This configuration is not yet a formal final freeze.
