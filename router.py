"""Top-level router module for intent detection and entity extraction."""

from policy_qa.router import (
    MONTHS,
    ParsedQuery,
    detect,
    effective_as_of,
)

__all__ = [
    "MONTHS",
    "ParsedQuery",
    "detect",
    "effective_as_of",
]
