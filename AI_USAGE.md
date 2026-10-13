# AI usage log

This project was built in Cursor with an AI coding assistant (Grok 4.6) generating the Python modules, tests, eval harness, and markdown from the written spec and the three files under `data/`.

## What the model generated

- Hand-encoded `policy_qa/clauses.py` from a full read of the master, circular, and FAQ (files themselves were not edited).
- `calc.py`, `calendar.py`, `router.py`, `assistant.py`, `tests/`, `eval.json`, `run_eval.py`, and the four markdown docs.

## What was checked against the sources (not trusted blindly)

- Circular item **D effective 1 Sep 2026**, not 1 Aug — confirmed in `circular_2026_08_amendment.md` and encoded as such.
- No clause numbers invented; 1.1–1.3, 2.1–2.4, 3.1–3.4, 4.1–4.4, 5.1–5.2 and circular letters A–F only.
- Indian grouping parse was wrong on the first run (`1,50,000` → 150, `Rs 4,000` → 400). Fixed by treating commas as grouping only; re-ran tests.
- Q1–Q8 and `eval.json` (19 rows) were verified with `pytest` and `python3 run_eval.py` (25 passed / 19 eval PASS).
- `WHERE_IT_BREAKS.md` is from live `ask()` calls (QR/kirana, shut shop, chargeback window, insurance Rs 1,80,000, exact closure date), not hypotheticals.

## Runtime

No model, API, or network call is used inside `ask()`. Retrieval is the in-memory clause list + keyword router.

## Residual risk

The assistant is only as good as the keyword map and the decisions in `DECISIONS.md`. Do not treat estimated calendar dates or FAQ-shaped questions with novel wording as reliable.
