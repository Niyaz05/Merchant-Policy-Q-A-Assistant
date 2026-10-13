# Where it breaks

Based on **actual** `ask()` runs after the eval suite passed 19/19, not on invented failures.

## 1. Unseen phrasing (keyword router)

The router only fires on a small keyword set (`upi`, `mdr`, `refund`, `close`+`account`, `limit`, `faq`, …). Real misses:

| Question | What happened |
|---|---|
| "What's the payout lag for QR payments for a kirana?" | `CANNOT_ANSWER`. Should have been UPI T+1 / T+0 (Circular A). “QR” and “kirana” are not in the keyword list. |
| "How many business days after I shut shop do funds land?" | `CANNOT_ANSWER`. Master 5.2 applies, but “shut shop” ≠ `close`+`account`. |
| "What percent do large merchants pay?" | `CANNOT_ANSWER`. 2.2 is in the store; the question never says MDR/fee/UPI/amount. |
| "How long does the customer's bank have to raise a chargeback?" | `CANNOT_ANSWER`. **3.4 is encoded** (120 days) but nothing routes to it. |

Do not trust the assistant on paraphrase, jargon, or any clause that has no handler (today: 3.1 window, 3.4, 5.1-only questions).

## 2. Exact closure / settlement calendar dates

`ask("I closed my account yesterday. Give me the exact date I will be paid.")` on 2026-08-15 returned **estimated 2026-08-26** (10 working days after 2026-08-14, Sundays skipped only). Notes correctly say the date cannot be guaranteed, but the ISO date is still easy to over-trust.

2026-08-15 is Independence Day (and a Saturday). The default holiday list is empty, so Saturday 15 Aug is counted as a **working** day. A real bank calendar would skip it and push the estimate. **Never treat the printed date as certain.**

## 3. Enhanced KYC / Annexure C (and similar missing facts)

`ask("I am an insurance merchant. Can I take Rs 1,80,000 in one UPI payment?")` → `CANNOT_ANSWER` because the router did not see `limit`/`per transaction`/`two payments`. Even with a better parse, Annexure C is absent: 4.2+4.4 are conditional and cannot be verified. Same class of unknown: customer bank limit (Circular E), Instant Settlement add-on status.

A related live miss: `"If I turned on same-day credit, when does UPI land?"` **did** route to settlement, but still treated add-on status as unknown — it did not bind “same-day credit” to Instant Settlement. Conditional answers are safer than guessing; they are also incomplete.
