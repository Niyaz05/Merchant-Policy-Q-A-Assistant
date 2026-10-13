from datetime import date
from decimal import Decimal

import pytest

from policy_qa.calc import classify_size, mdr, parse_indian_amount, round_paise
from policy_qa.clauses import resolve


def test_parse_indian_formats():
    assert parse_indian_amount("1,50,000") == Decimal("150000")
    assert parse_indian_amount("Rs.4,000") == Decimal("4000")
    assert parse_indian_amount("Rs 4,000") == Decimal("4000")
    assert parse_indian_amount("10 lakh") == Decimal("1000000")
    assert parse_indian_amount("₹15") == Decimal("15")
    assert parse_indian_amount("Rs 1,00,000") == Decimal("100000")


def test_size_boundary_10_lakh_is_small():
    assert classify_size("small") == "small"
    assert classify_size("large") == "large"
    assert classify_size(Decimal("1000000")) == "small"
    assert classify_size(Decimal("1000000.01")) == "large"


def test_round_half_up():
    assert round_paise(Decimal("1.225")) == Decimal("1.23")
    assert round_paise(Decimal("1.224")) == Decimal("1.22")


def test_mdr_q2_large_4000_after_circular():
    br = mdr(Decimal("4000"), "large", "2026-08-15")
    assert br["mdr"] == Decimal("20.00")
    assert br["cap"] == Decimal("25")
    assert br["gst"] == Decimal("3.60")
    assert br["total"] == Decimal("23.60")


def test_mdr_q3_capped():
    br = mdr(Decimal("150000"), "large", "2026-08-15")
    assert br["uncapped"] == Decimal("750.00")
    assert br["mdr"] == Decimal("25.00")
    assert br["gst"] == Decimal("4.50")
    assert br["total"] == Decimal("29.50")


def test_mdr_must_not_use_old_15_cap_for_large_after_aug():
    br = mdr(Decimal("4000"), "large", "2026-08-01")
    assert br["cap"] == Decimal("25")
    br_before = mdr(Decimal("4000"), "large", "2026-07-31")
    assert br_before["cap"] == Decimal("15")
    assert br_before["mdr"] == Decimal("15.00")


def test_small_rate_changes_on_aug_1():
    before = mdr(Decimal("10000"), "small", "2026-07-31")
    after = mdr(Decimal("10000"), "small", "2026-08-01")
    assert before["rate"] == Decimal("0.0030")
    assert after["rate"] == Decimal("0.0025")
    assert before["cap"] == after["cap"] == Decimal("15")


def test_exactly_10_lakh_uses_small_schedule():
    br = mdr(Decimal("10000"), Decimal("1000000"), "2026-08-15")
    assert br["size"] == "small"
    assert br["rate"] == Decimal("0.0025")
    assert br["cap"] == Decimal("15")


def test_mdr_not_in_force_before_master():
    with pytest.raises(ValueError):
        mdr(Decimal("100"), "small", "2025-12-31")


def test_resolve_33_deleted_on_sep_1():
    assert resolve("3.3", date(2026, 8, 31)) is not None
    assert resolve("3.3", date(2026, 9, 1)) is None
    assert resolve("circ.D", date(2026, 8, 31)) is None
    assert resolve("circ.D", date(2026, 9, 1)) is not None
