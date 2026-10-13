"""Decimal MDR / GST arithmetic and Indian-amount parsing."""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Union

from policy_qa.clauses import as_date, resolve

PAISE = Decimal("0.01")
LAKH = Decimal("100000")
GST_RATE = Decimal("0.18")
SMALL_VOLUME_MAX = Decimal("1000000")  # Rs 10 lakh inclusive = small


def round_paise(value: Decimal) -> Decimal:
    return value.quantize(PAISE, rounding=ROUND_HALF_UP)


def parse_indian_amount(text: str) -> Optional[Decimal]:
    """Parse the first money-like token: 1,50,000 / Rs.4,000 / 10 lakh / ₹15.

    Commas are grouping only (Indian xx,xx,xxx or Western x,xxx); '.' is decimal.
    """
    if not text:
        return None
    t = text.replace("₹", "Rs ")
    m = re.search(r"(?:rs\.?\s*)?([\d,]+(?:\.\d+)?)\s*lakh\b", t, flags=re.I)
    if m:
        return Decimal(m.group(1).replace(",", "")) * LAKH
    m = re.search(r"(?:rs\.?|inr)\s*([\d,]+(?:\.\d+)?)", t, flags=re.I)
    if m:
        return Decimal(m.group(1).replace(",", ""))
    # Indian: 1,50,000 (last group 3 digits, earlier groups of 2)
    m = re.search(r"\b(\d{1,3}(?:,\d{2})*,\d{3}(?:\.\d+)?)\b", t)
    if m:
        return Decimal(m.group(1).replace(",", ""))
    m = re.search(r"\b(\d{1,3}(?:,\d{3})+(?:\.\d+)?)\b", t)
    if m:
        return Decimal(m.group(1).replace(",", ""))
    return None


def classify_size(merchant_size: Union[str, Decimal, None]) -> Optional[str]:
    """'small' = monthly volume up to Rs 10 lakh (inclusive); 'large' = above."""
    if merchant_size is None:
        return None
    if isinstance(merchant_size, Decimal):
        return "small" if merchant_size <= SMALL_VOLUME_MAX else "large"
    s = str(merchant_size).strip().lower()
    if s in {"small", "upto_10_lakh", "up_to_10_lakh"}:
        return "small"
    if s in {"large", "above_10_lakh"}:
        return "large"
    amt = parse_indian_amount(s)
    if amt is not None:
        return "small" if amt <= SMALL_VOLUME_MAX else "large"
    return None


def mdr(
    amount: Union[Decimal, str, int],
    merchant_size: Union[str, Decimal],
    as_of: Union[str, date],
) -> dict:
    """min(rate * amount, cap) using clauses in force; GST 18% of capped MDR."""
    amt = amount if isinstance(amount, Decimal) else Decimal(str(amount).replace(",", ""))
    size = classify_size(merchant_size)
    if size is None:
        raise ValueError("merchant_size must be small/large or a monthly volume")
    day = as_date(as_of)
    rate_clause = resolve("2.1" if size == "small" else "2.2", day)
    cap_clause = resolve("2.3", day)
    gst_clause = resolve("2.4", day)
    if rate_clause is None or cap_clause is None or gst_clause is None:
        raise ValueError("MDR clauses not in force on this date")
    cap = cap_clause.cap_small if size == "small" else cap_clause.cap_large
    if cap is None:
        cap = cap_clause.cap
    raw = amt * rate_clause.rate
    mdr_amt = round_paise(min(raw, cap))
    gst = round_paise(mdr_amt * GST_RATE)
    return {
        "amount": amt,
        "size": size,
        "rate": rate_clause.rate,
        "uncapped": round_paise(raw),
        "cap": cap,
        "mdr": mdr_amt,
        "gst": gst,
        "total": mdr_amt + gst,
        "rate_clause": rate_clause,
        "cap_clause": cap_clause,
        "gst_clause": gst_clause,
    }


def inr(value: Decimal) -> str:
    """Indian grouping: Rs 1,50,000.00 / Rs 4,000.00 / Rs 20.00."""
    v = round_paise(value)
    sign = "-" if v < 0 else ""
    v = abs(v)
    whole = int(v)
    paise = int(v * 100) % 100
    s = str(whole)
    if len(s) <= 3:
        grouped = s
    else:
        last3, rest = s[-3:], s[:-3]
        chunks = []
        while rest:
            chunks.append(rest[-2:])
            rest = rest[:-2]
        grouped = ",".join(reversed(chunks)) + "," + last3
    return f"{sign}Rs {grouped}.{paise:02d}"
