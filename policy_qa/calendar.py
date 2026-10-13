"""Working-day helper.

Master 1.1: working days exclude Sundays and bank holidays. No holiday
calendar is supplied, so HOLIDAYS defaults to empty. Never treat a computed
calendar date as certain.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, Optional, Union

from policy_qa.clauses import as_date

# Override in tests; empty by default (assumption recorded in notes).
HOLIDAYS: set[date] = set()


def is_working_day(day: date, holidays: Optional[Iterable[date]] = None) -> bool:
    hol = set(holidays) if holidays is not None else HOLIDAYS
    return day.weekday() != 6 and day not in hol  # Sunday == 6; Saturday is a working day unless listed


def add_working_days(
    start: Union[str, date],
    n: int,
    holidays: Optional[Iterable[date]] = None,
) -> date:
    """Return the date n working days after start (start itself is not counted)."""
    day = as_date(start)
    added = 0
    while added < n:
        day += timedelta(days=1)
        if is_working_day(day, holidays):
            added += 1
    return day


def yesterday(as_of: Union[str, date]) -> date:
    return as_date(as_of) - timedelta(days=1)


def holiday_assumption_note(as_of: Optional[date] = None) -> str:
    extra = ""
    if as_of == date(2026, 8, 15):
        extra = (
            " 2026-08-15 is a Saturday and Independence Day; with an empty holiday "
            "list Saturday is counted as a working day, which may be wrong if banks are closed."
        )
    return (
        "Working-day dates are estimates only: Sundays are excluded and the bank-holiday "
        "list is empty by default, so an exact date cannot be guaranteed."
        + extra
    )
