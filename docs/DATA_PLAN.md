# Data plan and provenance

## Authority and scope
The instructor permits synthetic data and specifically suggests either 10 photographed receipts OR realistic noise. The Watch-outs also asks for reproducible generation, labels fixed before evaluation, leakage checks, and held-out cases produced by someone else or a different model when the system author designs the cases.

We use synthetic text with simulated OCR noise. This does not establish performance on photographed receipts. No claim of real OCR accuracy will be made.

## Current files
- `data/dev.json`: 14 development cases already used for implementation.
- `data/test_candidate_inputs.json`: 50 candidate inputs; no labels or difficulty groups in the model input.
- `data/test_candidate_labels.json`: separate answers, source tags, rule expectations and annotation notes.
- `data/test_candidate_manifest.json`: source, seed, hashes and explicit non-frozen status.
- `data/generate_test_candidate.py`: deterministic generator; seed 62012026.

Candidate distribution: 15 clean varied layouts, 15 distractor-rich receipts, 15 simulated-noise receipts, 5 insufficient-information cases. All names and transactions are fictional. There are 15 expected PASS, 30 expected FLAG and 5 expected ABSTAIN cases. This distribution is a challenge suite, not an estimate of production prevalence. Automated processing has a ceiling of 45/50 under the labels. The original <10% abstention target is incompatible with five mandatory abstentions; report coverage and abstention quality instead, with any revised targets fixed before evaluation.

## What has and has not been checked
Generation consistency checks verify unique IDs, reproducibility, split separation, input/label alignment, category counts, and nonempty notes. They do not constitute independent validation of ground truth. No model or Regex predictions have been run on the candidates.

The implementation assistant authored these candidates. They are NOT an independently authored holdout. Before declaring a final set, obtain cases from a different model/person and manually review their labels; do not falsely relabel this set as independent. AI API access is needed for separate model-generated cases if that route is chosen. Exact amounts, dates, and ambiguity judgments need review before freezing.

## Freeze checklist
- [ ] Independent case contribution recorded with actual author/model and prompt.
- [ ] Human review of labels, particularly ambiguous/missing fields.
- [ ] Final group counts, metric denominators and intended targets set.
- [ ] Shared validation rules fixed for Regex and AI.
- [ ] Data, prompt, code and policy hashes recorded together.
- [ ] Final inputs and labels frozen before either method is evaluated.

Labels stay out of requests. Both methods receive identical receipt text and use identical policy metadata. Group labels, expected decisions and annotation notes are evaluation-only. Candidate edits must be justified without consulting prediction scores. If candidates are used for tuning, reclassify them as development data and construct a new holdout.

## Independent contribution procedure (prepared, not yet executed)

`Prepare Test Data.command` makes one request to `google/gemini-2.5-flash-lite`, distinct from tested `openai/gpt-4o-mini`. The exact task-only prompt is stored in `prompts/independent_cases_v1.txt`; no implementation, candidate examples, extraction prompts or predictions are sent. Generated answers remain proposals and must be reviewed against input text and policy. Provenance includes the actual returned model, full response, usage and prompt hash. This is different-model authorship within a shared specification, not a fully independent external benchmark.

Predeclared assembly plan before seeing generated cases or scores: retain the first 12 candidates from each 15-case group and the first 4 insufficient-information cases (40); add the 10 independently contributed cases (3 clean, 3 distractor, 3 noise, 1 insufficient). This preserves 15/15/15/5 group counts. Do not select additions or replacements based on extractor scores. Record any required label corrections; retain the unmodified generation response. The old 50 candidates stay archived. Neither final assembly nor freezing has occurred.

Model reference checked 2026-09-24: https://openrouter.ai/google/gemini-2.5-flash-lite

## Completed generation and review

The different-model generation was completed and saved under `data/independent/20260924T121556999530Z/`. Review found and corrected label errors before scoring; see `DATA_REVIEW.md`. The actual reviewed mix is 16 clean, 17 distractor, 12 simulated-noise and 5 insufficient cases, not the original intended 15/15/15/5. These files remain reviewed candidates, not a frozen final set.
