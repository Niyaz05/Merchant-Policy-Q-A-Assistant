# Decisions (ambiguities and how they were resolved)

Authority order: **Circular > Master > FAQ**. FAQ is never used as a source of truth. When a FAQ line contradicts in-force policy, `status=CONFLICT_RESOLVED` and notes name the clash.

## Circular effective dates

- Items A, B, C, E, F: **2026-08-01** (circular header: “Effective 01 August 2026 unless stated otherwise”).
- Item D (delete 3.3; 3.2 without exception): **2026-09-01**, not 08-01. Encoded as `valid_to=2026-08-31` on 3.3 and on the exception-bearing 3.2.
- Item F: every other master clause stays as written (1.2, 1.3, 2.2, 2.4, 3.1, 3.4, 4.1, 4.2, 4.4, 5.1, 5.2).

## Refund: which date?

The effective-date test is the **refund-initiation date**, taken as `as_of_date` (not the original sale date). A sale on 31 Aug with a refund initiated 1 Sep is judged under post-D rules. Recorded because the documents do not say this explicitly.

## “Up to Rs 10 lakh” (small vs large)

**Inclusive.** Monthly volume of exactly Rs 10 lakh uses 2.1 / the Rs 15 cap. Above Rs 10 lakh uses 2.2 / the Rs 25 cap (from 2026-08-01).

## FAQ authority

FAQ dated 2026-03-12 is stored with `authoritative=False`. It may be cited when a conflict is explained; it never wins. Agreement with policy (Q1 default T+1) does **not** change status to CONFLICT_RESOLVED.

## Instant Settlement add-on

Circular A is conditional. If the question does not say the add-on is active, both T+0 and T+1 are stated and notes mark add-on status **unknown**.

## Holidays / working days

Master 1.1: working days exclude Sundays and bank holidays. **No holiday calendar is in the bundle**, so `HOLIDAYS` defaults to empty. Saturday is a working day unless listed. Estimates (e.g. 10 working days after closure) are labelled as estimates; an exact date is never guaranteed. 2026-08-15 is Saturday **and** Independence Day; with the empty list it is still counted as a working Saturday — that is an assumption, not a fact.

“Yesterday” = `as_of_date - 1 day`.

## Annexure C / enhanced KYC

4.2’s Rs 2 lakh per-txn limit applies only with enhanced KYC (4.4). Annexure C is missing, so eligibility is **unknown**. The assistant states the conditional rule and does not certify the higher limit.

## Tension between 4.2 and 4.3

4.2 allows Capital Markets/Insurance up to Rs 2,00,000 **per transaction**. 4.3 (and Circular E) caps a **customer account** at Rs 1,00,000 per day (or the bank’s lower limit). A 4.2 merchant still cannot take two Rs 1,00,000 UPI payments from the same customer on one day. 4.3 binds the customer even when 4.2 would allow a larger single txn — a single Rs 2 lakh hit would also break 4.3 unless the customer had unused daily room, which 4.3 does not grant above Rs 1 lakh. The internal tension is unresolved in the source text; this implementation lets **4.3 win for daily customer totals** and **4.1/4.2 win for per-txn merchant capacity**, and says so in notes on limit questions.

## Rounding

MDR = `min(rate × amount, cap)`, then ROUND_HALF_UP to paise. GST = 18% of that **capped** MDR (Master 2.4: GST is outside the cap), also ROUND_HALF_UP to paise.

## Card vs UPI

Only UPI MDR is specified. Card settlement is T+2 (1.2). Circular A T+0 is UPI-only. Same-day **card** settlement is not provided for (Q8). Card MDR / international cards → `CANNOT_ANSWER`.

## Before 2026-01-01

Nothing in the master is in force → `CANNOT_ANSWER`, no citations.

## Missing facts

If a missing fact changes the rule (add-on, customer bank limit, enhanced KYC, holiday calendar), answer with the conditional rule and name what is unknown. If the documents simply do not speak to the topic (chargeback **fee**, international cards) → `CANNOT_ANSWER` with no citations.

## Keyword router

Intent is keyword-based, not NLU. Unseen paraphrases (“QR payout lag”, “shut shop”) are expected to miss. That is accepted for a 60-minute build; see WHERE_IT_BREAKS.md.

## Source files

Hand-encoded from `data/policy_master_v1.md`, `data/circular_2026_08_amendment.md`, `data/merchant_faq_2026-03.md`. Those files were not modified. Clause numbers are only those that appear in the sources.
