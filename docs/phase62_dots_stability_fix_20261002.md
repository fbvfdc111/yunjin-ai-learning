# Phase 6.2 Dots structured response stability fix

## Change summary

- Hardened Dots vision parsing in `src/yunjin_ai/vision.py`.
- Accepted valid JSON wrapped in Markdown `json` code fences.
- Extracted exactly one JSON object from model text with safe surrounding prose.
- Added conservative normalization for known field aliases and scalar string values.
- Kept required schema validation and evidence-boundary checks intact.
- Added one automatic retry for structured-response parse failures and transient Dots/network errors.
- Preserved existing API key, base URL, model, provider, and prompt configuration.

## Tests run

- `python -m unittest tests.test_phase4_dots tests.test_phase4_vision`
  - Result: 14 tests passed.
- `python -m unittest discover -s tests -p "test_phase4_*.py"`
  - Result: 17 tests passed.
- `python scripts/phase62_vision_acceptance.py`
  - Result: passed, `ok: true`.
- `python -X utf8 scripts/phase6_health_check.py`
  - Result: functional checks passed, but overall `ok: false` because the baseline protection check correctly detected changed protected files, including `src/yunjin_ai/vision.py` and `tests/test_phase4_dots.py`.

## Not run

- `pytest` suite was not run in this local Codex runtime because `pytest` is not installed.
- Streamlit AppTest/product tests were not run because `streamlit` is not installed in this local Codex runtime.
- Real external Dots stability testing was not run because no real `DOTS_API_KEY` was available in this environment.

## Deployment note

Upload or copy this project into the existing `yunjin-ai-learning` GitHub repository, commit the changed files, and push. Streamlit Cloud should automatically redeploy from the GitHub update if the app is already connected to that repository.
