# ReceiptGuard: Receipt Extraction with Rule-Based Review

Mao Siyi | PE6201 | Business and Technical Trade-off Analysis

## Problem and scope
I am developing ReceiptGuard to assist a finance reviewer with extracting receipt information and checking a small set of explicit reimbursement rules. The intended workflow is to review extracted evidence and focus attention on flagged or uncertain cases. I use an illustrative workload of 80 receipts per day; this is a scenario assumption, not a measured business workload.

The prototype operates on receipt text. It does not verify receipt authenticity, execute payments, or implement a complete corporate reimbursement policy. Its demonstration policy covers SGD meal expenses up to SGD 50 submitted within 30 days. These thresholds are project assumptions, not real company requirements.

## Business and technical trade-offs
I compare a Python Regex extractor with GPT-4o-mini accessed through OpenRouter. Both receive the same text and feed shared deterministic checks. The language model handles variable wording and layouts, while Python performs monetary and date comparisons. This division makes policy decisions inspectable and avoids relying on a model for arithmetic.

I use a hosted model rather than train one because the project focuses on a small, bounded prototype without a large labelled training set. I own the extraction instructions, validation, policy logic, data generation and evaluation. The trade-off is dependence on an external service, network latency and usage charges. I do not use RAG because the current rules are a small fixed configuration, or an agent because processing follows a fixed sequence. Direct Python implementation provides control over validation and logging.

## Data and evaluation
The initial development set contains 14 synthetic examples. The final challenge set contains 50 synthetic receipt-text cases with format variation, distractor amounts, simulated OCR noise and insufficient information. The final frozen set contains 40 locally generated and 10 different-model-generated cases. Labels were reviewed before scoring; two erroneous proposed annotations were corrected. Review was by the implementation assistant, not an independent human. Simulated noise cannot establish performance on real photographed receipts.

The primary metric is correct automated handling across all cases: the system must answer with correct required fields and the correct policy status. Abstention earns no automated-completion credit. I separately report coverage, answered accuracy, field accuracy, routing accuracy, violation recall and false releases. Raw extraction and validated fields are reported separately. A majority-class routing reference and an always-abstain reference expose metrics that reward trivial strategies.

## Development findings and iteration
In the first real 14-case development run, Regex correctly automated 8 cases and the AI pipeline 9. AI routed all 14 cases correctly, but made two field errors: guessing USD from a bare dollar sign and selecting a value from conflicting totals. Both cases were abstained, preventing an incorrect release. The result demonstrates why correct routing must not be described as perfect extraction.

I added shared source checks that clear unsupported currency guesses and conflicting explicit totals, retaining raw fields for audit. Offline replay corrected these normalized fields without new model calls. A revised prompt stopped these two guesses in a second live development run, but unnecessarily omitted the otherwise visible amount or currency. Aggregate field accuracy did not improve; final routing remained correct. This illustrates a trade-off between avoiding guesses and retaining usable information. These are development observations, not final held-out results.

## Cost, risk and limitations
The final run reported USD 0.00509295 for 50 calls and mean AI pipeline latency of about 1.977 seconds. At that observed per-receipt cost, 80 receipts would cost approximately USD 0.00815 in model usage. This illustrative estimate excludes OCR, hosting, human review and funding fees; this small synthetic sample does not establish production cost.

PASS means only that implemented checks passed. FLAG and ABSTAIN require human review. Evidence snippets help verification but do not prove semantic correctness. Missing data, unsupported inputs and failed requests must not silently pass. The prototype has not demonstrated production safety, statutory compliance or generalization to real photographs.

## Final results and conclusion
On the frozen 50-case synthetic set, Regex correctly automated 38 cases (76%) and the AI pipeline 45 (90%). Five cases required abstention, so 90% was the set's maximum valid automated-completion rate. Correct routing, including abstention, was 43/50 versus 50/50. AI total-field accuracy was 49/50: it treated an item price as the final total in one incomplete receipt, but missing currency still triggered review. Neither system falsely released a case.

In the 12 simulated-noise cases, Regex correctly automated 7 and AI 12. On the 10 different-model cases, the corresponding counts were 7 and 9. Regex's seven overall misses involved label or layout variations and resulted in abstention. Several could be addressed by stronger parsing rules, limiting claims about superiority over non-AI methods.

The development-selected always-PASS reference achieved 32% routing accuracy; always-abstaining achieved 10% routing accuracy and zero automated completion. The largest test class was FLAG (58%), reported as descriptive context rather than a predictor selected after testing.

These results support improved coverage relative to this baseline on this bounded synthetic set. They do not support 90% automatic approval: the AI pipeline returned 16 PASS, 29 FLAG and 5 ABSTAIN, with 68% still requiring human review. I would treat this as a reviewer-assistance prototype and require real-receipt validation before deployment. Arithmetic reconciliation, tax-ID verification and the originally proposed LLM judge were not implemented; direct field and rule evaluation is the evidence presented here.


## Sources and reproducibility

- Project evidence: `results/final_20260924T122051343232Z/`, `data/frozen_v1/manifest.json`, and `docs/DATA_REVIEW.md`.
- OpenRouter, Structured Outputs: https://openrouter.ai/docs/guides/features/structured-outputs (accessed 24 September 2026). The application validates outputs locally rather than treating schema conformance as factual correctness.
- OpenRouter model identifiers: `openai/gpt-4o-mini` (extractor), `google/gemini-2.5-flash-lite` (additional synthetic-case generator). Usage costs above are from saved API responses.
