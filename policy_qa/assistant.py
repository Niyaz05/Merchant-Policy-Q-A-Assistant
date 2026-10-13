"""ask(): route a question onto in-force clauses. No LLM."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Union

from policy_qa.calc import inr, mdr as mdr_calc
from policy_qa.calendar import add_working_days, holiday_assumption_note, yesterday
from policy_qa.clauses import (
    MASTER_START,
    as_date,
    policy_in_force,
    resolve,
)
from policy_qa.router import detect

DateLike = Union[str, date]


def _used(*clauses) -> list[dict]:
    seen = []
    keys = set()
    for c in clauses:
        if c is None:
            continue
        key = (c.document, c.cite_clause)
        if key in keys:
            continue
        keys.add(key)
        seen.append(c.citation())
    return seen


def _result(answer: str, citations: list, status: str, notes: str = "") -> dict:
    out = {"answer": answer, "citations": citations, "status": status}
    if notes:
        out["notes"] = notes
    return out


def ask(question: str, as_of_date: DateLike = "2026-08-15") -> dict:
    as_of = as_date(as_of_date)
    if as_of < MASTER_START:
        return _result(
            "No Merchant Services Policy clauses are in force before 2026-01-01. Cannot answer.",
            [],
            "CANNOT_ANSWER",
            "as_of_date is before Master Document v1.0 effective date.",
        )
    if not policy_in_force(as_of):
        return _result("No policy in force on this date.", [], "CANNOT_ANSWER")

    parsed = detect(question)
    q = question.lower()

    if parsed.intent == "unknown":
        return _result(
            "The documents do not cover this topic (or the question could not be mapped to a clause).",
            [],
            "CANNOT_ANSWER",
        )
    handlers = {
        "settlement": _settlement,
        "mdr": _mdr,
        "refund": _refund,
        "limits": _limits,
        "closure": _closure,
        "faq": _faq,
        "chargeback": _chargeback,
    }
    return handlers[parsed.intent](question, parsed, as_of, q)


def _settlement(question, parsed, as_of: date, q: str) -> dict:
    c11 = resolve("1.1", as_of)
    c12 = resolve("1.2", as_of)
    c13 = resolve("1.3", as_of)
    faq = resolve("FAQ.settlement", as_of)
    notes = [holiday_assumption_note(as_of)]
    same_day = "same day" in q or "t+0" in q or "instant" in q

    if parsed.rail == "card" or ("card" in q and "upi" not in q):
        parts = [
            "Card transactions settle T+2 (Master 1.2).",
        ]
        if c11 and c11.extra.get("instant_t0"):
            parts.append(
                "The Instant Settlement T+0 add-on in Circular MS/2026/17 item A applies only to UPI, not cards."
            )
        parts.append(
            "The documents do not provide for same-day card settlement."
        )
        if c13:
            parts.append(
                "If a settlement date falls on a Sunday or bank holiday, settlement moves to the next working day (Master 1.3)."
            )
        status = "ANSWERED"
        cites = _used(c12, c11 if same_day else None, c13)
        return _result(" ".join(parts), cites, status, " ".join(notes))

    # UPI (default when asking about receiving UPI money, or unspecified rail on settlement)
    if c11 is None:
        return _result("UPI settlement clause is not in force on this date.", [], "CANNOT_ANSWER")

    if c11.extra.get("instant_t0"):
        answer = (
            "For UPI, settlement is T+1 (next working day) by default. "
            "T+0 (same day, by 11:59 PM) applies only if the merchant has an active "
            "Instant Settlement add-on. Add-on status is unknown, so both rules are stated. "
            "If the settlement date falls on a bank holiday, settlement occurs on the next "
            "working day (Master 1.3). Working days exclude Sundays and bank holidays."
        )
        notes.append("Instant Settlement add-on status is unknown; answered with the conditional rule.")
        cites = _used(c11, c13)
        status = "ANSWERED"
        if faq:
            answer += (
                " The FAQ (12 Mar 2026) also says UPI money arrives the next working day, "
                "which matches the default T+1 rule, but the FAQ is not authoritative."
            )
        return _result(answer, cites, status, " ".join(notes))

    answer = (
        "For UPI, settlement is T+1 (next working day). "
        "If the settlement date falls on a bank holiday, settlement occurs on the next "
        "working day (Master 1.3). Working days exclude Sundays and bank holidays."
    )
    return _result(answer, _used(c11, c13), "ANSWERED", " ".join(notes))


def _mdr(question, parsed, as_of: date, q: str) -> dict:
    false_no_cap = bool(
        "cap was removed" in q or "no upper limit" in q or "cap removed" in q
    )
    faq = resolve("FAQ.mdr", as_of)
    c21 = resolve("2.1", as_of)
    c22 = resolve("2.2", as_of)
    c23 = resolve("2.3", as_of)
    c24 = resolve("2.4", as_of)
    c41 = resolve("4.1", as_of)
    c42 = resolve("4.2", as_of)
    c44 = resolve("4.4", as_of)

    if parsed.rail == "card":
        return _result(
            "The documents specify UPI MDR only; card MDR is not covered.",
            [],
            "CANNOT_ANSWER",
        )

    size = parsed.size
    amount = parsed.amount
    notes = []
    cites_extra = []

    # FAQ / false-premise path even without a numeric example.
    conflict = False
    conflict_bits = []
    if faq and faq.extra.get("claims_no_cap"):
        if (
            parsed.faq_focus
            or false_no_cap
            or "no upper limit" in q
            or "faq" in q
        ):
            conflict = True
            conflict_bits.append(
                "The FAQ says there is no upper limit on the MDR; that is wrong. "
                "Master 2.3 has capped MDR at Rs 15.00 since 2026-01-01. "
            )
            if c23 and c23.cite_clause.startswith("item C"):
                conflict_bits.append(
                    "From 2026-08-01 Circular item C keeps the Rs 15 cap for merchants "
                    "with monthly volume up to Rs 10 lakh and sets a Rs 25 cap above that. "
                )
            else:
                conflict_bits.append("On this date the cap is Rs 15 for all merchants. ")
            if c21 and c21.rate == Decimal("0.0025"):
                conflict_bits.append(
                    "The FAQ small-merchant rate of 0.30% is also stale; from 2026-08-01 "
                    "the rate is 0.25% (Circular item B). "
                )
            conflict_bits.append(
                "The FAQ is not authoritative; Circular then Master prevail over the FAQ."
            )
            cites_extra = [faq, c23, c21, c22]

    if amount is None or size is None:
        if conflict:
            return _result(
                "".join(conflict_bits),
                _used(*cites_extra, c24),
                "CONFLICT_RESOLVED",
                "FAQ never overrides policy. Circular > Master > FAQ.",
            )
        # Describe the in-force schedule if we cannot compute.
        bits = []
        if c21:
            bits.append(f"Small merchants (monthly volume up to Rs 10 lakh): {c21.rate * 100:.2f}% UPI MDR ({c21.cite_clause}).")
        if c22:
            bits.append(f"Large merchants (above Rs 10 lakh): {c22.rate * 100:.2f}% UPI MDR ({c22.cite_clause}), subject to the cap.")
        if c23:
            bits.append(
                f"Cap: Rs {c23.cap_small:.2f} up to Rs 10 lakh monthly volume; "
                f"Rs {c23.cap_large:.2f} above ( {c23.cite_clause} )."
            )
        if c24:
            bits.append("GST at 18% is charged on the capped MDR and is outside the cap (Master 2.4).")
        bits.append("Need merchant size and transaction amount to compute a figure. Exactly Rs 10 lakh monthly volume is treated as small ('up to').")
        return _result(" ".join(bits), _used(c21, c22, c23, c24), "ANSWERED", "Missing amount and/or merchant size.")

    try:
        br = mdr_calc(amount, size, as_of)
    except ValueError as exc:
        return _result(str(exc), [], "CANNOT_ANSWER")

    parts = [
        f"UPI MDR for a {br['size']} merchant is {br['rate'] * 100:.2f}% of {inr(br['amount'])} "
        f"= {inr(br['uncapped'])}"
        + (
            f", capped at {inr(br['cap'])}"
            if br["uncapped"] > br["cap"]
            else f", which is below the {inr(br['cap'])} cap"
        )
        + f" → MDR {inr(br['mdr'])}.",
        f"GST at 18% of the capped MDR is {inr(br['gst'])} (GST is outside the cap, Master 2.4).",
        f"Total = {inr(br['total'])}.",
    ]
    if as_of >= date(2026, 8, 1) and br["size"] == "large" and br["cap"] == Decimal("25"):
        parts.append("The former Rs 15 cap does not apply to large merchants from 2026-08-01.")
    if false_no_cap:
        conflict = True
        parts.append(
            "The premise that the cap was removed is false: a cap remains in force (Master 2.3 / Circular item C)."
        )

    if c41 and amount > c41.limit:
        parts.append(
            f"{inr(amount)} exceeds the per-transaction UPI limit of {inr(c41.limit)} (Master 4.1), "
            "unless the merchant is in Capital Markets or Insurance (Master 4.2) and has completed "
            "enhanced KYC (Master 4.4). Annexure C is not provided, so enhanced-KYC eligibility cannot be verified."
        )
        notes.append("Annexure C missing; 4.2 enhanced limit cannot be confirmed.")
        cites_extra.extend([c41, c42, c44])

    status = "CONFLICT_RESOLVED" if conflict else "ANSWERED"
    if conflict:
        parts = conflict_bits + parts
        notes.append("FAQ never overrides policy. Circular > Master > FAQ.")
    return _result(
        " ".join(p.strip() for p in parts if p),
        _used(br["rate_clause"], br["cap_clause"], br["gst_clause"], faq if conflict else None, *cites_extra),
        status,
        " ".join(notes),
    )


def _refund(question, parsed, as_of: date, q: str) -> dict:
    c32 = resolve("3.2", as_of)
    c33 = resolve("3.3", as_of)
    c_d = resolve("circ.D", as_of)
    faq = resolve("FAQ.refund", as_of)
    notes = [
        "Effective date is judged by the refund-initiation date (the as_of_date), not the sale date."
    ]
    false_333 = "3.3 still applies" in q or ("october" in q and "3.3" in q)

    within = None
    if parsed.hours is not None:
        within = parsed.hours <= 24
    elif "within 24" in q or "same day" in q:
        within = True

    if c33 is not None:
        # 3.3 still in force (until 2026-08-31 inclusive)
        if within is False:
            answer = (
                "The refund is outside 24 hours, so Master 3.2 applies: MDR is not returned "
                "(the 3.3 exception does not apply)."
            )
            return _result(answer, _used(c32, c33), "ANSWERED", " ".join(notes))
        if within is None:
            answer = (
                "Whether MDR is returned depends on timing, which was not stated. "
                "If the refund is initiated within 24 hours, Master 3.3 (still in force on this date) "
                "reverses MDR in full. Otherwise Master 3.2 applies: MDR is not returned. "
                "Merchants may initiate a refund within 90 days (Master 3.1)."
            )
            notes.append("Refund-to-sale lag unknown; answered with the 3.2 / 3.3 conditional.")
            return _result(answer, _used(c33, c32, resolve("3.1", as_of)), "ANSWERED", " ".join(notes))
        answer = (
            f"A refund initiated {parsed.hours:g} hours after the sale is within 24 hours. "
            "On this date Master 3.3 is still in force, so MDR is reversed in full."
        )
        status = "ANSWERED"
        if faq:
            answer += " The FAQ ('yes within 24 hours') agrees for this date but is not authoritative."
        return _result(answer, _used(c33), status, " ".join(notes))

    # 3.3 deleted
    answer = (
        "Clause 3.3 has been deleted by Circular MS/2026/17 item D (effective 2026-09-01), "
        "so it is not in force on this date. Clause 3.2 applies without exception: "
        "MDR is not returned, even if the refund is initiated within 24 hours."
    )
    if false_333:
        answer = (
            "The premise that Master 3.3 still applies (e.g. in October) is false. " + answer
        )
    status = "ANSWERED"
    if faq:
        answer += (
            " The FAQ ('yes, if you refund within 24 hours we reverse the fee') is stale "
            "for this date and does not override the Circular."
        )
        status = "CONFLICT_RESOLVED"
        notes.append("FAQ contradicts in-force 3.2 (no 3.3 exception); Circular/Master win.")
    return _result(answer, _used(c_d, c32, faq if status == "CONFLICT_RESOLVED" else None), status, " ".join(notes))


def _limits(question, parsed, as_of: date, q: str) -> dict:
    c41 = resolve("4.1", as_of)
    c42 = resolve("4.2", as_of)
    c43 = resolve("4.3", as_of)
    c44 = resolve("4.4", as_of)
    faq = resolve("FAQ.limits", as_of)
    notes = [
        "Master 4.2 (Rs 2 lakh per txn for Capital Markets/Insurance) can exceed the "
        "Rs 1,00,000 daily per-customer cap in 4.3; 4.3 still binds the customer account."
    ]

    two = "two payments" in q or "two transactions" in q or "same day by one customer" in q
    if two and parsed.amounts:
        each = parsed.amounts[0]
        total = each * 2 if len(parsed.amounts) == 1 else parsed.amounts[0] + parsed.amounts[1]
        bank = c43.extra.get("also_bank_limit") if c43 else False
        answer = (
            f"No. Daily limit per customer account is {inr(c43.limit)} across all UPI "
            f"transactions ({c43.cite_clause})."
        )
        if bank:
            answer += (
                " From 2026-08-01 this is the lower of Rs 1,00,000 and the customer's own bank limit "
                "(bank limit unknown)."
            )
        answer += (
            f" Two payments of {inr(each)} on the same day total {inr(total)} and would exceed "
            f"{inr(c43.limit)}; the second payment would not be allowed under 4.3."
        )
        if each > (c41.limit if c41 else Decimal("100000")):
            answer += f" Each payment also exceeds the per-transaction limit of {inr(c41.limit)} (Master 4.1)."
        return _result(answer, _used(c43, c41), "ANSWERED", " ".join(notes))

    parts = []
    if c41:
        parts.append(f"Per-transaction UPI limit is {inr(c41.limit)} (Master 4.1).")
    if parsed.amount and c41 and parsed.amount > c41.limit:
        parts.append(
            f"{inr(parsed.amount)} is above that default cap. Capital Markets and Insurance merchants "
            f"may accept up to {inr(c42.limit) if c42 else 'Rs 2,00,000.00'} per transaction (Master 4.2) "
            "only if they have completed enhanced KYC (Master 4.4). Annexure C is not provided, so "
            "enhanced-KYC eligibility cannot be verified — both outcomes are stated."
        )
        if c43:
            parts.append(
                f"Separately, daily limit per customer account is {inr(c43.limit)} "
                f"({c43.cite_clause}); a single {inr(parsed.amount)} UPI debit would also exceed 4.3."
            )
        notes.append("Annexure C missing; 4.2 enhanced limit cannot be confirmed.")
        return _result(" ".join(parts), _used(c41, c42, c44, c43), "ANSWERED", " ".join(notes))
    if c42:
        parts.append(
            f"Capital Markets and Insurance merchants may accept up to {inr(c42.limit)} per transaction "
            "(Master 4.2) only after enhanced KYC (Master 4.4). Annexure C is not provided, so that status cannot be verified."
        )
    if c43:
        parts.append(c43.text)
    return _result(" ".join(parts), _used(c41, c42, c43, c44), "ANSWERED", " ".join(notes))


def _closure(question, parsed, as_of: date, q: str) -> dict:
    c51 = resolve("5.1", as_of)
    c52 = resolve("5.2", as_of)
    faq = resolve("FAQ.closure", as_of)
    closure_date = yesterday(as_of) if "yesterday" in q else as_of
    estimate = add_working_days(closure_date, c52.days if c52 else 10)
    notes = [
        holiday_assumption_note(as_of),
        f"Closure date taken as {closure_date.isoformat()} "
        + ("(as_of minus 1 day because the question said yesterday)." if "yesterday" in q else "(as_of_date)."),
    ]
    answer = (
        f"Master 5.2: pending settlements are released within 10 working days of closure "
        f"({closure_date.isoformat()}), after deducting outstanding dues. "
        f"Estimated release by {estimate.isoformat()} if no bank holidays fall in the window "
        f"(only Sundays excluded; holiday list empty by default). An exact date cannot be guaranteed."
    )
    status = "ANSWERED"
    if faq:
        answer += (
            " The FAQ says pending money is released within '10 days' (calendar days), which "
            "conflicts with '10 working days' in Master 5.2. The FAQ is not authoritative; policy wins."
        )
        status = "CONFLICT_RESOLVED"
        notes.append("FAQ '10 days' vs Master 5.2 '10 working days'; Circular > Master > FAQ.")
    return _result(answer, _used(c52, c51, faq if status == "CONFLICT_RESOLVED" else None), status, " ".join(notes))


def _faq(question, parsed, as_of: date, q: str) -> dict:
    """Generic FAQ-vs-policy when topic was not classified more specifically."""
    return _mdr(question, parsed, as_of, q)
