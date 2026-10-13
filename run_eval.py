#!/usr/bin/env python3
"""Run ask() over eval.json and print a pass/fail table."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from policy_qa.assistant import ask

ROOT = Path(__file__).resolve().parent


def cite_blob(result: dict) -> str:
    return " ".join(f"{c.get('document', '')} {c.get('clause', '')}" for c in result.get("citations", [])).lower()


def citations_match(result: dict, expected: list) -> bool:
    if not expected:
        return result.get("citations") == [] or expected == []
    blob = cite_blob(result)
    return all(str(needle).lower() in blob for needle in expected)


def answer_contains(result: dict, needles: list) -> bool:
    text = result.get("answer", "").lower()
    return all(str(n).lower() in text for n in needles)


def main() -> int:
    cases = json.loads((ROOT / "eval.json").read_text(encoding="utf-8"))
    rows = []
    fails = 0
    print(
        f"{'id':<8} {'adv':<5} {'status':<8} {'cites':<8} {'answer':<8} {'result'}"
    )
    print("-" * 56)
    for case in cases:
        result = ask(case["question"], as_of_date=case.get("as_of_date", "2026-08-15"))
        st_ok = result.get("status") == case["expected_status"]
        ci_ok = citations_match(result, case.get("expected_citations") or [])
        an_ok = answer_contains(result, case.get("expected_answer_contains") or [])
        ok = st_ok and ci_ok and an_ok
        if not ok:
            fails += 1
        flag = "Y" if case.get("adversarial") else "n"
        print(
            f"{case['id']:<8} {flag:<5} "
            f"{'Y' if st_ok else 'N':<8} "
            f"{'Y' if ci_ok else 'N':<8} "
            f"{'Y' if an_ok else 'N':<8} "
            f"{'PASS' if ok else 'FAIL'}"
        )
        if not ok:
            print(f"         status={result.get('status')} cites={result.get('citations')}")
            print(f"         answer={result.get('answer')[:300]}")
        rows.append(ok)
    print("-" * 56)
    print(f"Passed {len(rows) - fails}/{len(rows)}; failed {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
