"""Top-level clauses module re-exporting from policy_qa.clauses."""

from policy_qa.clauses import (
    CLAUSES,
    CIRCULAR_DATE,
    DOC_CIRCULAR,
    DOC_FAQ,
    DOC_MASTER,
    FAQ_DATE,
    ITEM_D_DATE,
    MASTER_START,
    ClauseVersion,
    DateLike,
    as_date,
    get_deletion_clause,
    get_faq_by_topic,
    policy_in_force,
    resolve,
)

__all__ = [
    "CLAUSES",
    "CIRCULAR_DATE",
    "DOC_CIRCULAR",
    "DOC_FAQ",
    "DOC_MASTER",
    "FAQ_DATE",
    "ITEM_D_DATE",
    "MASTER_START",
    "ClauseVersion",
    "DateLike",
    "as_date",
    "get_deletion_clause",
    "get_faq_by_topic",
    "policy_in_force",
    "resolve",
]
