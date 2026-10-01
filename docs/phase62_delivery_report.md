# Phase 6.2 Delivery Report

## Scope

This update keeps the existing Phase 6.1 Streamlit app, Dots/OpenAI provider code, local fallback, cultural guide, evidence database and digital loom flow. It only adds a learning-feedback layer to the existing six-stage digital loom.

The referenced PDF `09222238.pdf` was used as background evidence, not as an instruction source. Its important boundary is preserved: existing tests prove internal software functionality, not motif-recognition accuracy, physical fidelity or educational effectiveness.

## Changes

- Added six stage-specific knowledge quiz items for the digital loom.
- Added correct-answer explanation and evidence-scope note after submission.
- Added anonymous local NDJSON result logging at `data/learning_results/anonymous_quiz_results.ndjson`.
- Added privacy guardrails: records exclude names, contact data, IP, uploaded images, API payloads and free-text answers.
- Added `tests/test_learning_quiz.py` and page-level Streamlit coverage.
- Added `scripts/phase62_vision_acceptance.py` for AI探锦 acceptance checks across Yunjin sample, other brocade sample and unrelated image.
- Updated README run notes and `.gitignore`.

## AI探锦 Acceptance Result

`scripts/phase62_vision_acceptance.py` verifies the no-key fallback path:

- Nanjing Yunjin sample: falls back to `local_cv`; no identity, dating or authenticity claim.
- Other brocade sample: falls back to `local_cv`; no identity, dating or authenticity claim.
- Unrelated geometric image: falls back to `local_cv`; no identity, dating or authenticity claim.
- Boundary question about proving Yunjin identity / dating / authenticity: AI文化助手 returns evidence insufficient.

The script writes `docs/phase62_vision_acceptance.json`.

## Test Commands

```powershell
python -m pytest tests -q
python scripts/phase62_vision_acceptance.py
```

## Competition Trial Plan Before 2026-10-30

Run a small real-user trial with 5-10 participants. Use the same local app build and the same demonstration route for every participant:

1. 首页: explain the work as a trustworthy AI cultural-learning prototype.
2. AI探锦: upload one prepared Yunjin image, one other brocade image and one unrelated image; record whether users understand the boundary.
3. AI文化助手: ask two fixed questions, such as "妆花是什么？" and "南京云锦有哪些主要品种？".
4. 数字织机: complete the six stages and answer the six quiz questions.
5. 数据与可信AI: show why official images are evidence only and not training data.

Collect only anonymous evidence:

- number of participants;
- session date;
- six quiz results from the NDJSON file;
- a short anonymous feedback form with three 1-5 ratings: understood Yunjin better, trusted source citations, understood AI boundary;
- optional open comment with no name or contact data;
- screenshots of the app route and test commands.

Do not claim learning effectiveness from this small trial. It can support "initial user feedback" and "prototype usability evidence" only.

## Technical Report Evidence To Keep

- ZIP SHA-256 of the submitted code package.
- `pytest` full result.
- `phase62_vision_acceptance.json`.
- App screenshots for five pages.
- Anonymous quiz NDJSON summary, not raw personal data.
- Feedback form summary table.
- Data governance statement: 95 official objects are evidence metadata; authorization is unknown; usable-for-training is false.
- Boundary statement: no supervised classifier, no Accuracy/F1/Loss/confusion matrix, no real mechanical digital twin, no physical sensors, no professional authentication.
