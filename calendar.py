"""Top-level calendar module.

Exposes policy working-day helpers while preserving Python's standard library
`calendar` attributes (so tools like pytest/faker do not fail when importing
standard library calendar).
"""

from __future__ import annotations

import importlib
import sys

# Dynamically load standard library calendar module to avoid shadow issues
_stdlib_calendar = importlib.import_module("calendar")
if _stdlib_calendar is sys.modules[__name__]:
    # If shadowed, find and load the stdlib one
    import importlib.util
    for _p in sys.path:
        if _p and _p != "" and _p != ".":
            _candidate = f"{_p}/calendar.py"
            try:
                _spec = importlib.util.spec_from_file_location("_stdlib_calendar", _candidate)
                if _spec and _spec.loader:
                    _mod = importlib.util.module_from_spec(_spec)
                    _spec.loader.exec_module(_mod)
                    _stdlib_calendar = _mod
                    break
            except Exception:
                pass

# Re-export all standard library calendar symbols
for _k in dir(_stdlib_calendar):
    if not _k.startswith("__"):
        globals()[_k] = getattr(_stdlib_calendar, _k)

# Policy calendar exports
from policy_qa.calendar import (
    HOLIDAYS,
    add_working_days,
    holiday_assumption_note,
    is_working_day,
    yesterday,
)

__all__ = [
    "HOLIDAYS",
    "add_working_days",
    "holiday_assumption_note",
    "is_working_day",
    "yesterday",
]
