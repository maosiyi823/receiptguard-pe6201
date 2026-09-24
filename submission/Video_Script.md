# ReceiptGuard demonstration script

Suggested practice length: approximately 3–4 minutes; the official duration must still be confirmed. This is a suggested script, not a course-imposed time limit. The page shows recorded real API outputs, not live inference.

## 1. Introduce the system
[Open the demo page.]
“Hello, I am Mao Siyi. My project is ReceiptGuard, a receipt extraction and review assistant. It compares a Regex parser with GPT-4o-mini and uses the same Python policy checks for both. This page displays saved outputs from the actual frozen experiment. It does not make new AI requests.”

## 2. Explain the normal workflow
[Click Normal.]
“The input is receipt text and separate claim metadata. The demonstration rules support SGD meal expenses of at most 50 dollars, submitted within 30 days. Here, the fields are readable and the checks pass. PASS means the implemented checks passed, not that a payment has been approved.”

## 3. Show an observed difference
[Click Noisy label.]
“This receipt uses a zero in the total label. The frozen Regex implementation misses the amount and abstains, while the model extracts it. The model still does not decide the policy: Python performs that check. A stronger Regex parser could address this specific pattern, so my conclusion is limited to the implementations tested.”

## 4. Show review decisions
[Click Over limit, then Missing total.]
“An explicit policy violation produces FLAG. Missing required information produces ABSTAIN. These outcomes are different: FLAG identifies a problem, while ABSTAIN means the system cannot confidently complete the assessment.”

## 5. Show an actual model error
[Click AI field error.]
“Here, the model treats an item price as a final total. Under the frozen annotation convention, the expected total is unknown. Missing currency still triggers ABSTAIN, so the receipt is not released. This is why correct routing is not the same as perfect extraction.”

## 6. Explain results and trade-offs
[Return to the summary.]
“On 50 frozen synthetic cases, Regex correctly automated 38 and the AI pipeline 45, or 76 and 90 percent. Five cases intentionally required abstention. Therefore 90 percent was the valid automatic-completion ceiling. It is not an automatic-approval rate: 29 cases were flagged and five abstained, so 68 percent still required review.”

“The model cost reported by the API was about 0.0051 US dollars for all 50 calls, with a mean pipeline time of about 1.98 seconds. This excludes hosting, OCR and human labour. Rules are faster, cheaper and easier to inspect, while the model improves handling of some layout variations.”

## 7. State limitations
“Forty cases were locally generated and ten contributed by a different model. All are synthetic and the labels were reviewed with AI assistance, not independently verified by a human. These results do not establish performance on real photographs or production safety. The final version also excludes tax-ID verification and arithmetic reconciliation. My next validation step would use real receipts and a stronger rules baseline.”
