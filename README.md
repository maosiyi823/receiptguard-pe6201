# ReceiptGuard

PE6201 coursework prototype by Mao Siyi. ReceiptGuard compares Regex with GPT-4o-mini extraction and applies shared deterministic reimbursement checks. It processes synthetic receipt **text**, not receipt photographs.

## Observed frozen-test results

| Metric | Regex + rules | AI + rules |
|---|---:|---:|
| Correct automated handling | 38/50 (76%) | 45/50 (90%) |
| Correct routing including abstention | 43/50 | 50/50 |
| Abstentions | 12/50 | 5/50 |
| Total-field accuracy | 43/50 | 49/50 |
| False releases observed | 0 | 0 |

Five cases intentionally require abstention. Correct automatic handling includes flagging violations: **90% is not an automatic-approval rate**. The AI pipeline returned 16 PASS, 29 FLAG and 5 ABSTAIN. One item-price/total error remained in an abstained case. These are small-sample synthetic results, not evidence of production safety.

## Start without an API key

Python 3.9+; standard library only. No package installation is required.

1. Open `demo/index.html` in a browser, or on macOS double-click `Open Demo.command`. This shows **saved real API outputs**, not live inference.
2. From a terminal in the project directory, run:

```sh
python3 -m unittest discover -s tests -v
python3 -c "from run_final import verify; print(verify()['status'])"
python3 compare_development.py
```

The tests are offline and use explicitly simulated API responses. Integrity verification checks the frozen dataset and implementation hashes. See `docs/FINAL_RESULTS.md` for the full interpretation and `results/final_20260924T122051343232Z/summary.json` for recorded metrics.

## Live requests (optional for inspecting the submitted evidence)

An OpenRouter account and API key are required. Paid usage may apply. Keys are entered with a hidden terminal prompt and are not saved. Do not put keys in source code, chat or GitHub.

```sh
python3 first_ai_run.py       # one synthetic receipt
python3 run_development.py   # 14 development requests
```

On macOS, the corresponding `.command` launchers can be double-clicked. If downloaded launcher permissions are absent, use the Python commands above.

The submitted final run is retained unchanged. `python3 run_final.py` intentionally refuses to repeat it if any `results/final_*` directory exists. To reproduce a fresh paid 50-case experiment, use a separate copy of the project, move the existing final-results directory OUTSIDE that copy's `results/` directory while preserving the original archive, then run `python3 run_final.py`. The runner verifies hashes first, saves each response, performs no automatic retries and stops on a connection error. Incomplete runs are not headline final scores. Do not tune the code or alter labels after reviewing final predictions and then describe a rerun as an unseen test.

## Architecture and demo policy

Receipt text -> Regex or hosted model -> shared evidence/format validation -> deterministic Python policy checks -> PASS / FLAG / ABSTAIN.

Demo policy: meal category, SGD, positive total at most SGD 50.00, submission 0–30 days after purchase. Missing, unsupported or ambiguous required information leads to ABSTAIN. FLAG and ABSTAIN require review. PASS is not payment authorization. Raw fields and evidence are preserved; evidence occurrence alone does not prove semantic correctness.

The active extraction prompt is `prompts/extract_v2.txt`. Arithmetic reconciliation, tax-ID verification, image OCR, RAG, agents and LLM-as-judge scoring are not implemented. This is narrower than the initial proposal and is disclosed in the report.

## Data and reproducibility

- `data/dev.json`: 14 synthetic development cases.
- `data/frozen_v1/`: 50 frozen inputs, separate labels, corrections, code snapshot and SHA-256 manifest.
- Final composition: 40 locally generated cases and 10 contributed by Gemini 2.5 Flash-Lite, distinct from the GPT-4o-mini extractor.
- Groups: 16 clean varied, 17 distractor, 12 simulated-noise and 5 insufficient-information cases.
- Labels were checked with AI assistance before scoring; no independent human verification is claimed.
- `data/independent/`: original generation response, prompt and proposed labels, retained for provenance.
- `data/generate_test_candidate.py` and `data/assemble_reviewed.py`: reproducible generation and assembly; generating candidates does not alter the frozen files.

See `docs/DATA_REVIEW.md` for corrections. The different-model generator made errors, including claiming 35 exceeds 50; these were corrected before scoring. This is not a wholly independent benchmark. Synthetic noise cannot establish real-photo/OCR performance.

## Files for review

- `submission/Business_Technical_Analysis.md`: English analysis, under 1,200 words.
- `submission/Problem_Statement.md`: updated scope; does not replace the historical milestone automatically.
- `submission/Video_Script.md`: suggested English narration; video not recorded yet.
- `docs/FINAL_RESULTS.md`: metrics, errors and limitations.
- `docs/DEVELOPMENT_FINDINGS.md`: development iterations, clearly separated from final results.
- `run_final.py`: formal evaluator; `common_validation.py`: shared guardrails.

## AI assistance and authorship

Codex assisted with implementation, synthetic-data tooling, label review, analysis and English drafting. The student ran the API experiments locally. Gemini contributed ten synthetic test cases; GPT-4o-mini was the extractor. The student should review, understand and adapt the submission and follow the course's AI-assistance disclosure requirements. Do not represent this as unaided coding or independent human annotation.

## References

Accessed 24 September 2026:
- [OpenRouter quickstart](https://openrouter.ai/docs/quickstart)
- [Structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs)
- [GPT-4o-mini](https://openrouter.ai/openai/gpt-4o-mini)
- [Gemini 2.5 Flash-Lite](https://openrouter.ai/google/gemini-2.5-flash-lite)

Costs in the report come from saved API usage records, not quoted list-price estimates. Reported model costs exclude OCR, hosting, funding fees and human review.
