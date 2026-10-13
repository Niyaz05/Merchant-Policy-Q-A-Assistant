# Merchant policy Q&A (offline)

Small deterministic assistant over three local policy documents. **No LLM / no network at runtime.** Python 3.10+ standard library; `pytest` only for tests.

Source documents (do not edit): `data/policy_master_v1.md`, `data/circular_2026_08_amendment.md`, `data/merchant_faq_2026-03.md`.

## Run

```bash
# from this directory
python3 -c 'from policy_qa import ask; import json; print(json.dumps(ask("When does a small merchant receive UPI money?"), indent=2))'

python3 -m pytest tests/ -q
python3 run_eval.py          # exit 1 if any eval row fails
```

`ask(question, as_of_date="2026-08-15")` returns `answer`, `citations` (`document` + `clause`), `status` (`ANSWERED` | `CONFLICT_RESOLVED` | `CANNOT_ANSWER`), and optional `notes`.

## Layout

| Module | Role |
|---|---|
| `policy_qa/clauses.py` | Hand-encoded versioned clause store + `resolve(ref, as_of)` |
| `policy_qa/calc.py` | Indian-amount parse; MDR = min(rate×amount, cap); GST 18%; paise ROUND_HALF_UP |
| `policy_qa/calendar.py` | Working days = not Sunday, minus optional holiday set (empty default) |
| `policy_qa/router.py` | Keyword intent + amount / size / rail / hours / dates |
| `policy_qa/assistant.py` | `ask()` glue; citations only from versions actually used |

Eval: `eval.json` (≥12 items, including Q1–Q8 and adversarial traps) + `run_eval.py`.

## What works

Dated clause lookup (D on **2026-09-01**, A/B/C/E on **2026-08-01**). Q1–Q8 behaviours in the brief. FAQ vs policy conflicts. Conditional answers when add-on / KYC / bank limit / holidays are unknown. `as_of` before 2026-01-01 and out-of-scope topics → `CANNOT_ANSWER` with no citations. Never invents a clause number.

## What does not

Paraphrase and jargon the keyword router misses; exact working-day dates without a holiday calendar; proving enhanced KYC (Annexure C missing); clauses that are stored but not routed (e.g. 3.4). See `WHERE_IT_BREAKS.md` and `DECISIONS.md`.
