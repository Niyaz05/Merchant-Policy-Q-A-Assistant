"""Deterministic keyword intent + slot extraction. No ML."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional

from policy_qa.calc import parse_indian_amount

MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
}


@dataclass
class ParsedQuery:
    intent: str
    rail: Optional[str] = None  # "upi" | "card"
    size: Optional[str] = None  # "small" | "large"
    amount: Optional[Decimal] = None
    amounts: list = field(default_factory=list)
    hours: Optional[float] = None
    mentioned_dates: list = field(default_factory=list)
    faq_focus: bool = False
    raw: str = ""


def _mentions_faq(q: str) -> bool:
    return bool(re.search(r"\bfaq\b", q)) or "frequently asked" in q


def _rail(q: str) -> Optional[str]:
    has_upi = "upi" in q
    has_card = bool(re.search(r"\bcard\b", q))
    if has_upi and not has_card:
        return "upi"
    if has_card and not has_upi:
        return "card"
    if has_upi and has_card:
        return "both"
    return None


def _size(q: str) -> Optional[str]:
    if re.search(r"\bsmall\b", q):
        return "small"
    if re.search(r"\blarge\b", q):
        return "large"
    m = re.search(
        r"(?:monthly volume|volume)\s+(?:of\s+)?(?:exactly\s+)?(?:rs\.?\s*)?([\d,]+(?:\.\d+)?)\s*lakh",
        q,
        re.I,
    )
    if m:
        lakhs = Decimal(m.group(1).replace(",", ""))
        return "small" if lakhs <= 10 else "large"
    m = re.search(
        r"(?:exactly\s+)?(?:rs\.?\s*)?([\d,]+(?:\.\d+)?)\s*lakh\s+monthly",
        q,
        re.I,
    )
    if m:
        lakhs = Decimal(m.group(1).replace(",", ""))
        return "small" if lakhs <= 10 else "large"
    if re.search(r"exactly\s+(?:rs\.?\s*)?10\s*lakh", q):
        return "small"
    return None


def _hours(q: str) -> Optional[float]:
    m = re.search(r"(\d+(?:\.\d+)?)\s*hours?", q)
    if m:
        return float(m.group(1))
    if "within 24 hours" in q or "within twenty four" in q:
        return 24.0
    if "same day" in q and "refund" in q:
        return 12.0  # same calendar day, treated as within 24h
    return None


def _dates(q: str) -> list[date]:
    found: list[date] = []
    for m in re.finditer(r"\b(\d{4})-(\d{2})-(\d{2})\b", q):
        found.append(date(int(m.group(1)), int(m.group(2)), int(m.group(3))))
    pat = re.compile(
        r"\b(\d{1,2})\s+(january|february|march|april|may|june|july|"
        r"august|september|october|november|december|jan|feb|mar|apr|jun|"
        r"jul|aug|sep|sept|oct|nov|dec)\s+(\d{4})\b",
        re.I,
    )
    for m in pat.finditer(q):
        found.append(date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1))))
    pat2 = re.compile(
        r"\b(january|february|march|april|may|june|july|august|september|"
        r"october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|"
        r"oct|nov|dec)\s+(\d{1,2}),?\s+(\d{4})\b",
        re.I,
    )
    for m in pat2.finditer(q):
        found.append(date(int(m.group(3)), MONTHS[m.group(1).lower()], int(m.group(2))))
    return found


def _amounts(q: str) -> list[Decimal]:
    found: list[Decimal] = []
    t = q.replace("₹", "Rs ")
    for m in re.finditer(
        r"(?:rs\.?\s*)([\d,]+(?:\.\d+)?)(?:\s*lakh)?",
        t,
        flags=re.I,
    ):
        val = parse_indian_amount(m.group(0))
        if val is not None and val not in found:
            found.append(val)
    for m in re.finditer(r"\b(\d{1,3}(?:,\d{2})+,\d{3}(?:\.\d+)?)\b", t):
        val = parse_indian_amount(m.group(1))
        if val is not None and val not in found:
            found.append(val)
    return found


def detect(question: str) -> ParsedQuery:
    q = question.lower()
    faq_focus = _mentions_faq(q)
    amounts = _amounts(q)
    rail = _rail(q)
    size = _size(q)
    hours = _hours(q)

    closure = bool(re.search(r"\bclos(e|ed|ing|ure)\b", q)) and (
        "account" in q or "pending" in q or "yesterday" in q
    )
    refund = "refund" in q
    limits = bool(
        re.search(r"\blimits?\b", q)
        or "two payments" in q
        or "two transactions" in q
        or "same day by one customer" in q
        or "maximum amount a customer" in q
        or "per transaction" in q
        or "per-transaction" in q
        or "daily limit" in q
        or "capital market" in q
        or "insurance" in q
        or (("can i take" in q or "can i accept" in q or "in one upi" in q) and bool(amounts))
    )
    mdr = bool(
        re.search(r"\bmdr\b", q)
        or "fee" in q
        or "gst" in q
        or "upper limit" in q
        or "cap" in q
        or "what do i pay" in q
        or "discount rate" in q
        or "0.30" in q
        or "0.25%" in q
        or "0.50" in q
        or (("percent" in q or "percentage" in q) and (size or "merchant" in q))
    )
    # Amount + merchant size + UPI and not another topic → fee calc (Q2/Q3 phrasing).
    if amounts and size and rail in {"upi", None} and not (closure or refund or limits):
        if "receive" not in q and "settle" not in q and "when" not in q:
            mdr = True
    settlement = bool(
        "settle" in q
        or "settlement" in q
        or "receive" in q
        or "when will i get" in q
        or "when do" in q
        or "get my money" in q
        or "get my upi" in q
        or "same day" in q
        or "t+0" in q
        or "t+1" in q
        or "t+2" in q
    )

    out_of_scope = bool(
        "chargeback fee" in q
        or "international" in q
        or "visa" in q
        or "mastercard fee" in q
        or "fx" in q
        or "foreign" in q
        or "amex" in q
        or "debit card mdr" in q
        or "credit card mdr" in q
    )

    chargeback_fee = "chargeback" in q and "fee" in q
    chargeback = "chargeback" in q and not chargeback_fee
    if chargeback_fee:
        out_of_scope = True

    if out_of_scope:
        intent = "unknown"
    elif closure:
        intent = "closure"
    elif chargeback:
        intent = "chargeback"
    elif refund:
        intent = "refund"
    elif limits and not mdr:
        intent = "limits"
    elif mdr:
        intent = "mdr"
    elif settlement:
        intent = "settlement"
    elif faq_focus:
        intent = "faq"
    else:
        intent = "unknown"

    primary_amount = None
    if amounts:
        # Prefer a transaction-sized amount over "10 lakh" volume.
        non_volume = [a for a in amounts if a != Decimal("1000000")]
        primary_amount = (non_volume or amounts)[0]

    return ParsedQuery(
        intent=intent,
        rail=rail,
        size=size,
        amount=primary_amount,
        amounts=amounts,
        hours=hours,
        mentioned_dates=_dates(q),
        faq_focus=faq_focus,
        raw=question,
    )


