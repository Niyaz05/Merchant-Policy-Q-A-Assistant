from policy_qa.assistant import ask


def _blob(r):
    return (r["answer"] + " " + " ".join(
        c["document"] + " " + c["clause"] for c in r["citations"]
    )).lower()


def test_q1_upi_settlement_conditional():
    r = ask("When does a small merchant receive UPI money?")
    b = _blob(r)
    assert r["status"] == "ANSWERED"
    assert "t+1" in b
    assert "t+0" in b
    assert "instant settlement" in b
    assert "unknown" in b.lower() or "unknown" in (r.get("notes") or "").lower()
    assert "item a" in b
    assert "1.3" in b


def test_q2_large_4000():
    r = ask("Large merchant, Rs 4,000 UPI")
    b = _blob(r)
    assert r["status"] == "ANSWERED"
    assert "20.00" in r["answer"]
    assert "3.60" in r["answer"]
    assert "23.60" in r["answer"]
    assert "25" in r["answer"]
    assert "2.2" in b
    assert "item c" in b
    assert "2.4" in b
    assert "15.00" not in r["answer"] or "former rs 15" in r["answer"].lower()


def test_q3_large_150000_and_limit():
    r = ask("Large merchant, Rs 1,50,000 UPI MDR")
    assert "25.00" in r["answer"]
    assert "4.50" in r["answer"]
    assert "29.50" in r["answer"]
    assert "1,00,000" in r["answer"] or "100000" in r["answer"].replace(",", "") or "Rs 100000.00" in r["answer"]
    assert "4.1" in _blob(r)
    assert "annexure c" in r["answer"].lower()


def test_q4_refund_before_and_after_d():
    a = ask("Refund 3 hours after sale", as_of_date="2026-08-20")
    assert a["status"] == "ANSWERED"
    assert "3.3" in _blob(a)
    assert "reversed" in a["answer"].lower()
    b = ask("Refund 3 hours after sale", as_of_date="2026-09-05")
    assert b["status"] == "CONFLICT_RESOLVED"
    assert "not returned" in b["answer"].lower()
    assert "item d" in _blob(b)
    assert "3.3" in _blob(b) or "deleted" in b["answer"].lower()


def test_q5_faq_cap_wrong():
    r = ask("The FAQ says there is no upper limit on MDR. Is the FAQ right?")
    assert r["status"] == "CONFLICT_RESOLVED"
    b = _blob(r)
    assert "15" in r["answer"]
    assert "25" in r["answer"]
    assert "0.25" in r["answer"]
    assert "item c" in b


def test_q6_two_payments():
    r = ask("Two payments of Rs 1,00,000 same day by one customer?")
    assert "no" in r["answer"].lower()
    assert "4.3" in _blob(r) or "item e" in _blob(r)
    assert "second" in r["answer"].lower()


def test_q7_closure_yesterday():
    r = ask("I closed my account yesterday. When will I get my money?")
    assert r["status"] == "CONFLICT_RESOLVED"
    assert "10 working days" in r["answer"].lower()
    assert "cannot be guaranteed" in r["answer"].lower()
    assert "2026-08-14" in r["answer"]
    assert "5.2" in _blob(r)


def test_q8_same_day_card():
    r = ask("Does the policy allow me to settle card payments same day?")
    assert r["status"] == "ANSWERED"
    b = _blob(r)
    assert "t+2" in b
    assert "1.2" in b
    assert "upi" in r["answer"].lower()
    assert "do not provide" in r["answer"].lower() or "not provide" in r["answer"].lower()


def test_cannot_answer_before_policy():
    r = ask("When does a small merchant receive UPI money?", as_of_date="2025-12-31")
    assert r["status"] == "CANNOT_ANSWER"
    assert r["citations"] == []


def test_cannot_answer_chargeback_fee():
    r = ask("What is the chargeback fee?")
    assert r["status"] == "CANNOT_ANSWER"
    assert r["citations"] == []
