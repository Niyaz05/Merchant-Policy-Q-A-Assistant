"""Tests for clauses.py versioned store and resolution logic."""

from datetime import date
from decimal import Decimal
import pytest

from clauses import resolve, get_deletion_clause, get_faq_by_topic


def test_before_2026_not_in_force():
    assert resolve("1.1", "2025-12-31") is None
    assert resolve("2.1", "2025-12-31") is None
    assert resolve("3.3", "2025-12-31") is None


def test_master_clauses_in_july_2026():
    c_1_1 = resolve("1.1", "2026-07-15")
    assert c_1_1 is not None
    assert c_1_1.clause_ref == "1.1"
    assert c_1_1.document == "Master Document v1.0"

    c_2_1 = resolve("2.1", "2026-07-15")
    assert c_2_1 is not None
    assert c_2_1.parsed["rate"] == Decimal("0.0030")

    c_2_3 = resolve("2.3", "2026-07-15")
    assert c_2_3 is not None
    assert c_2_3.parsed["cap"] == Decimal("15")


def test_circular_amendments_august_2026():
    # 2026-07-31 boundary
    c_prev = resolve("2.1", "2026-07-31")
    assert c_prev is not None
    assert c_prev.parsed["rate"] == Decimal("0.0030")

    # 2026-08-01 boundary
    c_new = resolve("2.1", "2026-08-01")
    assert c_new is not None
    assert "item B" in c_new.cite_clause
    assert c_new.parsed["rate"] == Decimal("0.0025")

    # 1.1 amended by Circular Item A
    c_settle = resolve("1.1", "2026-08-15")
    assert c_settle is not None
    assert "item A" in c_settle.cite_clause
    assert "Instant Settlement" in c_settle.text

    # 2.3 amended by Circular Item C
    c_cap = resolve("2.3", "2026-08-15")
    assert c_cap is not None
    assert "item C" in c_cap.cite_clause
    assert c_cap.parsed["cap_large"] == Decimal("25")


def test_clause_3_3_deletion_september_2026():
    # On 2026-08-20, 3.3 is in force
    c_aug = resolve("3.3", "2026-08-20")
    assert c_aug is not None
    assert c_aug.clause_ref == "3.3"

    # On 2026-08-31, 3.3 is in force
    c_aug_end = resolve("3.3", "2026-08-31")
    assert c_aug_end is not None

    # On 2026-09-01, 3.3 is deleted by Item D!
    c_sep = resolve("3.3", "2026-09-01")
    assert c_sep is None

    # Deletion clause lookup
    del_clause = get_deletion_clause("3.3", "2026-09-01")
    assert del_clause is not None
    assert "item D" in del_clause.cite_clause


def test_faq_entries():
    faq = get_faq_by_topic("mdr")
    assert faq is not None
    assert "no upper limit" in faq.answer
    assert faq.authoritative is False
