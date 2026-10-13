"""Versioned clause store hand-encoded from the three source documents.

resolve(clause_ref, as_of) returns the version in force on that date, or None
if the clause is not yet in force or has been deleted.

Circular items A, B, C, E take effect 2026-08-01. Item D (delete 3.3) takes
effect 2026-09-01. FAQ rows are non-authoritative snapshots dated 2026-03-12.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Union

DateLike = Union[str, date]

MASTER_START = date(2026, 1, 1)
CIRCULAR_DATE = date(2026, 8, 1)  # items A, B, C, E, F
ITEM_D_DATE = date(2026, 9, 1)
FAQ_DATE = date(2026, 3, 12)

DOC_MASTER = "Master Document v1.0"
DOC_CIRCULAR = "Circular MS/2026/17"
DOC_FAQ = "Merchant FAQ 2026-03-12"


def as_date(value: DateLike) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value)[:10])


@dataclass(frozen=True)
class ClauseVersion:
    id: str
    document: str
    clause_ref: str  # lookup key, e.g. "1.1" or "FAQ.mdr"
    cite_clause: str  # string placed in citations[].clause
    text: str
    valid_from: date
    valid_to: Optional[date]  # inclusive; None = still open
    supersedes: Optional[str] = None
    authoritative: bool = True
    rate: Optional[Decimal] = None
    cap: Optional[Decimal] = None
    cap_small: Optional[Decimal] = None
    cap_large: Optional[Decimal] = None
    days: Optional[int] = None
    limit: Optional[Decimal] = None
    extra: dict = field(default_factory=dict)

    def citation(self) -> dict:
        return {"document": self.document, "clause": self.cite_clause}

    @property
    def parsed(self) -> dict:
        d = {}
        if self.rate is not None:
            d["rate"] = self.rate
        if self.cap is not None:
            d["cap"] = self.cap
        if self.cap_small is not None:
            d["cap_small"] = self.cap_small
        if self.cap_large is not None:
            d["cap_large"] = self.cap_large
        if self.days is not None:
            d["days"] = self.days
        if self.limit is not None:
            d["limit"] = self.limit
        d.update(self.extra)
        return d

    @property
    def answer(self) -> str:
        return self.text



def _d(s: str) -> Decimal:
    return Decimal(s)


CLAUSES: list[ClauseVersion] = [
    # --- Master 1.x ---
    ClauseVersion(
        id="m1.1-v1",
        document=DOC_MASTER,
        clause_ref="1.1",
        cite_clause="1.1",
        text="Settlement for UPI transactions is T+1 (next working day). Working days exclude Sundays and bank holidays.",
        valid_from=MASTER_START,
        valid_to=date(2026, 7, 31),
        extra={"upi_t": 1, "instant": False},
    ),
    ClauseVersion(
        id="cA-v1",
        document=DOC_CIRCULAR,
        clause_ref="1.1",
        cite_clause="item A (amends Master 1.1)",
        text=(
            "UPI settlement is T+0 (same day, by 11:59 PM) for merchants with an "
            "active Instant Settlement add-on, and T+1 for all others."
        ),
        valid_from=CIRCULAR_DATE,
        valid_to=None,
        supersedes="m1.1-v1",
        extra={"upi_t": 1, "instant_t0": True},
    ),
    ClauseVersion(
        id="m1.2-v1",
        document=DOC_MASTER,
        clause_ref="1.2",
        cite_clause="1.2",
        text="Card transactions settle T+2.",
        valid_from=MASTER_START,
        valid_to=None,
        extra={"card_t": 2},
    ),
    ClauseVersion(
        id="m1.3-v1",
        document=DOC_MASTER,
        clause_ref="1.3",
        cite_clause="1.3",
        text="If a settlement date falls on a bank holiday, settlement occurs on the next working day.",
        valid_from=MASTER_START,
        valid_to=None,
    ),
    # --- Master 2.x / Circular B, C ---
    ClauseVersion(
        id="m2.1-v1",
        document=DOC_MASTER,
        clause_ref="2.1",
        cite_clause="2.1",
        text="UPI MDR for merchants with monthly volume up to ₹10 lakh is 0.30% of the transaction value.",
        valid_from=MASTER_START,
        valid_to=date(2026, 7, 31),
        rate=_d("0.0030"),
    ),
    ClauseVersion(
        id="cB-v1",
        document=DOC_CIRCULAR,
        clause_ref="2.1",
        cite_clause="item B (amends Master 2.1)",
        text="UPI MDR for merchants with monthly volume up to ₹10 lakh is 0.25%.",
        valid_from=CIRCULAR_DATE,
        valid_to=None,
        supersedes="m2.1-v1",
        rate=_d("0.0025"),
    ),
    ClauseVersion(
        id="m2.2-v1",
        document=DOC_MASTER,
        clause_ref="2.2",
        cite_clause="2.2",
        text=(
            "UPI MDR for merchants with monthly volume above ₹10 lakh is 0.50% of "
            "the transaction value, subject to the cap in 2.3."
        ),
        valid_from=MASTER_START,
        valid_to=None,
        rate=_d("0.0050"),
    ),
    ClauseVersion(
        id="m2.3-v1",
        document=DOC_MASTER,
        clause_ref="2.3",
        cite_clause="2.3",
        text="MDR on any single UPI transaction shall not exceed ₹15.",
        valid_from=MASTER_START,
        valid_to=date(2026, 7, 31),
        cap=_d("15"),
        cap_small=_d("15"),
        cap_large=_d("15"),
    ),
    ClauseVersion(
        id="cC-v1",
        document=DOC_CIRCULAR,
        clause_ref="2.3",
        cite_clause="item C (amends Master 2.3)",
        text=(
            "The MDR cap of ₹15 applies only to merchants with monthly volume up "
            "to ₹10 lakh. For merchants above ₹10 lakh, the cap is ₹25."
        ),
        valid_from=CIRCULAR_DATE,
        valid_to=None,
        supersedes="m2.3-v1",
        cap_small=_d("15"),
        cap_large=_d("25"),
    ),
    ClauseVersion(
        id="m2.4-v1",
        document=DOC_MASTER,
        clause_ref="2.4",
        cite_clause="2.4",
        text="GST at 18% is charged on the MDR amount and is not part of the MDR cap.",
        valid_from=MASTER_START,
        valid_to=None,
        rate=_d("0.18"),
    ),
    # --- Refunds ---
    ClauseVersion(
        id="m3.1-v1",
        document=DOC_MASTER,
        clause_ref="3.1",
        cite_clause="3.1",
        text="Merchants may initiate a refund within 90 days of the original transaction.",
        valid_from=MASTER_START,
        valid_to=None,
        days=90,
    ),
    ClauseVersion(
        id="m3.2-v1",
        document=DOC_MASTER,
        clause_ref="3.2",
        cite_clause="3.2",
        text="MDR charged on a refunded transaction is not returned to the merchant, except as provided in 3.3.",
        valid_from=MASTER_START,
        valid_to=date(2026, 8, 31),
        extra={"mdr_returned": False, "exception_3_3": True},
    ),
    ClauseVersion(
        id="cD-3.2-v1",
        document=DOC_CIRCULAR,
        clause_ref="3.2",
        cite_clause="item D (amends Master 3.2)",
        text="Clause 3.3 is deleted. Clause 3.2 now applies without exception. MDR is not returned.",
        valid_from=ITEM_D_DATE,
        valid_to=None,
        supersedes="m3.2-v1",
        extra={"mdr_returned": False, "exception_3_3": False},
    ),
    ClauseVersion(
        id="m3.3-v1",
        document=DOC_MASTER,
        clause_ref="3.3",
        cite_clause="3.3",
        text="If a refund is initiated within 24 hours of the transaction, the MDR is reversed in full.",
        valid_from=MASTER_START,
        valid_to=date(2026, 8, 31),
        extra={"hours": 24, "mdr_reversed": True},
    ),
    ClauseVersion(
        id="cD-delete-3.3",
        document=DOC_CIRCULAR,
        clause_ref="circ.D",
        cite_clause="item D (deletes Master 3.3)",
        text="Clause 3.3 is deleted effective 01 September 2026. Clause 3.2 applies without exception.",
        valid_from=ITEM_D_DATE,
        valid_to=None,
    ),
    ClauseVersion(
        id="m3.4-v1",
        document=DOC_MASTER,
        clause_ref="3.4",
        cite_clause="3.4",
        text="Chargeback disputes must be raised by the customer's bank within 120 days.",
        valid_from=MASTER_START,
        valid_to=None,
        days=120,
    ),
    # --- Limits / Circular E ---
    ClauseVersion(
        id="m4.1-v1",
        document=DOC_MASTER,
        clause_ref="4.1",
        cite_clause="4.1",
        text="Per-transaction UPI limit is ₹1,00,000.",
        valid_from=MASTER_START,
        valid_to=None,
        limit=_d("100000"),
    ),
    ClauseVersion(
        id="m4.2-v1",
        document=DOC_MASTER,
        clause_ref="4.2",
        cite_clause="4.2",
        text='Merchants in category "Capital Markets" and "Insurance" may accept up to ₹2,00,000 per transaction, see 4.4.',
        valid_from=MASTER_START,
        valid_to=None,
        limit=_d("200000"),
    ),
    ClauseVersion(
        id="m4.3-v1",
        document=DOC_MASTER,
        clause_ref="4.3",
        cite_clause="4.3",
        text="Daily limit per customer account is ₹1,00,000 across all UPI transactions.",
        valid_from=MASTER_START,
        valid_to=date(2026, 7, 31),
        limit=_d("100000"),
    ),
    ClauseVersion(
        id="cE-v1",
        document=DOC_CIRCULAR,
        clause_ref="4.3",
        cite_clause="item E (amends Master 4.3)",
        text=(
            "The daily limit per customer account is ₹1,00,000 or the limit set by "
            "the customer's own bank, whichever is lower."
        ),
        valid_from=CIRCULAR_DATE,
        valid_to=None,
        supersedes="m4.3-v1",
        limit=_d("100000"),
        extra={"also_bank_limit": True},
    ),
    ClauseVersion(
        id="m4.4-v1",
        document=DOC_MASTER,
        clause_ref="4.4",
        cite_clause="4.4",
        text="The enhanced limit in 4.2 applies only to merchants who have completed enhanced KYC (Annexure C).",
        valid_from=MASTER_START,
        valid_to=None,
    ),
    # --- Closure ---
    ClauseVersion(
        id="m5.1-v1",
        document=DOC_MASTER,
        clause_ref="5.1",
        cite_clause="5.1",
        text="A merchant may close the account with 30 days written notice.",
        valid_from=MASTER_START,
        valid_to=None,
        days=30,
    ),
    ClauseVersion(
        id="m5.2-v1",
        document=DOC_MASTER,
        clause_ref="5.2",
        cite_clause="5.2",
        text="Pending settlements are released within 10 working days of closure, after deducting outstanding dues.",
        valid_from=MASTER_START,
        valid_to=None,
        days=10,
    ),
    # --- FAQ (non-authoritative) ---
    ClauseVersion(
        id="faq-settle",
        document=DOC_FAQ,
        clause_ref="FAQ.settlement",
        cite_clause="UPI / card settlement",
        text="Next working day. Card money comes in two working days.",
        valid_from=FAQ_DATE,
        valid_to=None,
        authoritative=False,
    ),
    ClauseVersion(
        id="faq-mdr",
        document=DOC_FAQ,
        clause_ref="FAQ.mdr",
        cite_clause="UPI fee / cap",
        text="0.30% for small merchants, 0.50% for large ones. There is no upper limit on the fee, so very large transactions cost more.",
        valid_from=FAQ_DATE,
        valid_to=None,
        authoritative=False,
        rate=_d("0.0030"),
        extra={"claims_no_cap": True},
    ),
    ClauseVersion(
        id="faq-refund",
        document=DOC_FAQ,
        clause_ref="FAQ.refund",
        cite_clause="same-day refund fee reversal",
        text="Yes, if you refund within 24 hours we reverse the fee.",
        valid_from=FAQ_DATE,
        valid_to=None,
        authoritative=False,
    ),
    ClauseVersion(
        id="faq-limit",
        document=DOC_FAQ,
        clause_ref="FAQ.limits",
        cite_clause="maximum customer payment",
        text="₹1,00,000 per transaction. Insurance and capital markets merchants can accept ₹2,00,000.",
        valid_from=FAQ_DATE,
        valid_to=None,
        authoritative=False,
    ),
    ClauseVersion(
        id="faq-close",
        document=DOC_FAQ,
        clause_ref="FAQ.closure",
        cite_clause="account closure / pending money",
        text="Yes, with 30 days' notice. Pending money is released within 10 days.",
        valid_from=FAQ_DATE,
        valid_to=None,
        authoritative=False,
        days=10,
    ),
]


def resolve(clause_ref: str, as_of: DateLike) -> Optional[ClauseVersion]:
    """Return the clause version in force on as_of, or None."""
    day = as_date(as_of)
    if day < MASTER_START:
        return None
    ref_clean = clause_ref.strip()
    if ref_clean.lower() in {"item d", "circ.d", "circular d"}:
        ref_clean = "circ.D"

    found: list[ClauseVersion] = []
    for clause in CLAUSES:
        if clause.clause_ref != ref_clean:
            continue
        if day < clause.valid_from:
            continue
        if clause.valid_to is not None and day > clause.valid_to:
            continue
        found.append(clause)
    if not found:
        return None
    return max(found, key=lambda c: c.valid_from)


def policy_in_force(as_of: DateLike) -> bool:
    return as_date(as_of) >= MASTER_START


def get_deletion_clause(clause_ref: str, as_of: DateLike) -> Optional[ClauseVersion]:
    """Return the deletion clause version if the clause was deleted on or before as_of."""
    day = as_date(as_of)
    if clause_ref in {"3.3", "circ.D", "item D", "item d"} and day >= ITEM_D_DATE:
        return resolve("circ.D", as_of)
    return None


def get_faq_by_topic(topic: str) -> Optional[ClauseVersion]:
    """Retrieve non-authoritative FAQ clause version by topic string."""
    topic_clean = topic.strip().lower()
    for c in CLAUSES:
        if not c.authoritative:
            if topic_clean in c.clause_ref.lower() or topic_clean in c.cite_clause.lower():
                return c
    return None

