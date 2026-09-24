# ReceiptGuard: Receipt Extraction with Rule-Based Review

Mao Siyi | PE6201 | Updated scope statement

## Problem and intended user
A finance reviewer must read differently formatted receipts, extract key facts, and check reimbursement conditions. Missing or ambiguous information requires additional attention. ReceiptGuard explores whether a hosted language model can improve extraction coverage compared with a simple Regex parser while retaining explicit, reviewable policy checks.

The primary user is a finance executive reviewing meal-expense claims on a laptop. The intended change is to inspect extracted evidence and prioritize flagged or uncertain cases instead of manually transcribing every field. A workload of 80 receipts per day is an illustrative assumption; no measured enterprise savings are claimed.

## Proposed solution and scope
The prototype accepts receipt text and separate claim metadata. It extracts date, currency and total, then applies shared Python checks for a demonstration policy: SGD meal expenses up to SGD 50, submitted within 30 days. It outputs PASS, FLAG or ABSTAIN with evidence and reasons. PASS only means the implemented checks passed; payment authorization stays outside scope.

GPT-4o-mini is accessed through OpenRouter for extraction. Regex is the non-AI baseline. Policies remain deterministic, and ambiguous information triggers human review. RAG and agents are excluded because this prototype uses a small fixed rule set and a linear workflow.

## Data and evaluation
A 14-case development suite supports iteration. The frozen final suite contains 50 synthetic text receipts, including format variation, distracting amounts, simulated OCR noise and five insufficient-information cases. Ten cases were contributed by a different model; proposed labels were reviewed before scoring. These are not real photographs and do not establish real OCR performance.

Success is measured by correct required fields and correct non-abstained decisions across all cases, alongside coverage, field accuracy, violation recall and false releases. Abstention does not count as automatic completion. Code, prompts, source data, corrections and run logs are retained for reproducibility.

## Risks and scope changes
Models may guess missing fields or mistake item prices for totals. Shared validation, null values, evidence and manual review reduce but do not eliminate these risks. No production safety or compliance claim is made. Compared with the initial proposal, this implemented version omits tax-ID verification, arithmetic reconciliation and LLM-as-judge evaluation. It uses direct field and rule checks instead. Original unverified baseline and business-impact figures are not retained as facts.

This updated scope statement supplements the original submitted milestone; it does not alter that historical submission.
