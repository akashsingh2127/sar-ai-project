import pytest
from agents.validators import (
    validate_transaction_id,
    validate_amount,
    validate_currency,
    validate_date,
    validate_customer_id,
    validate_typology_evidence,
    run_deterministic_audit
)

@pytest.fixture
def base_evidence():
    return {
        "transaction_details": {
            "transaction_id": "TXN123",
            "amount": 142500,
            "currency": "USD",
            "timestamp": "2026-01-10T14:32:00",
            "sender": "CUST-99",
            "receiver": "CUST-88"
        },
        "typologies": [
            {"typology_name": "Structuring", "supporting_transaction_ids": ["TXN123", "TXN124"]}
        ],
        "related_transactions": ["TXN124"]
    }

def test_correct_transaction_id(base_evidence):
    narrative = "The transaction TXN123 is suspicious."
    discs = validate_transaction_id(base_evidence, narrative)
    assert len(discs) == 0

def test_wrong_transaction_id(base_evidence):
    narrative = "The transaction TXN999 is suspicious."
    discs = validate_transaction_id(base_evidence, narrative)
    assert any(d.field == "transaction_id" for d in discs)

def test_correct_amount(base_evidence):
    narrative = "Amount involved is 142,500 USD."
    discs = validate_amount(base_evidence, narrative)
    assert len(discs) == 0

def test_wrong_amount(base_evidence):
    narrative = "Amount involved is 12500 USD."
    discs = validate_amount(base_evidence, narrative)
    assert any(d.field == "amount" for d in discs)

def test_correct_currency(base_evidence):
    narrative = "Amount involved is 142500 USD."
    discs = validate_currency(base_evidence, narrative)
    assert len(discs) == 0

def test_wrong_currency(base_evidence):
    narrative = "Amount involved is 142500 INR."
    discs = validate_currency(base_evidence, narrative)
    assert any(d.field == "currency" for d in discs)

def test_correct_date(base_evidence):
    narrative = "Date: 2026-01-10"
    discs = validate_date(base_evidence, narrative)
    assert len(discs) == 0

def test_wrong_date(base_evidence):
    narrative = "Date: 2025-12-31"
    discs = validate_date(base_evidence, narrative)
    assert any(d.field == "date" for d in discs)

def test_correct_customer_id(base_evidence):
    narrative = "Sender CUST-99 and receiver CUST-88 were involved."
    discs = validate_customer_id(base_evidence, narrative)
    assert len(discs) == 0

def test_wrong_customer_id(base_evidence):
    narrative = "Sender CUST-55 sent money."
    discs = validate_customer_id(base_evidence, narrative)
    assert any(d.field == "customer_id" for d in discs)

def test_supported_typology(base_evidence):
    narrative = "Detected structuring pattern."
    discs = validate_typology_evidence(base_evidence, narrative)
    assert len(discs) == 0

def test_unsupported_typology(base_evidence):
    narrative = "Detected rapid movement and circular patterns."
    discs = validate_typology_evidence(base_evidence, narrative)
    assert any("Unsupported typology claimed" in d.description for d in discs)

def test_typology_without_evidence():
    evidence = {"transaction_details": {"transaction_id": "TXN1"}, "typologies": []}
    narrative = "Detected structuring."
    discs = validate_typology_evidence(evidence, narrative)
    assert any("Unsupported typology claimed" in d.description for d in discs)

def test_missing_transaction_evidence(base_evidence):
    # Test when expected txn_id is missing from narrative
    narrative = "A large transfer occurred."
    discs = validate_transaction_id(base_evidence, narrative)
    assert any("Missing expected Transaction ID" in d.description for d in discs)

def test_missing_required_evidence():
    evidence = {"transaction_details": {}}
    narrative = "Transaction TXN123 amount 5000."
    res = run_deterministic_audit(evidence, narrative)
    assert not res.overall_passed

def test_multiple_transactions(base_evidence):
    narrative = "TXN123 and TXN124 are related structuring events."
    discs = validate_transaction_id(base_evidence, narrative)
    assert len(discs) == 0

def test_formatting_differences(base_evidence):
    narrative1 = "Amount is 142500"
    narrative2 = "Amount is 142,500.00"
    assert len(validate_amount(base_evidence, narrative1)) == 0
    assert len(validate_amount(base_evidence, narrative2)) == 0

def test_invalid_malformed_values():
    # If the LLM generates a weird amount
    evidence = {"amount": 500}
    narrative = "Amount is five hundred."
    discs = validate_amount(evidence, narrative)
    # The numeric check will fail since "500" isn't strictly found. This is expected behavior for strict matching.
    assert len(discs) > 0

def test_empty_evidence():
    res = run_deterministic_audit({}, "Narrative.")
    # Without evidence, it can't check much, but shouldn't crash.
    assert res.overall_passed == True

def test_fabricated_values(base_evidence):
    narrative = "TXN123 for 142500 USD on 2026-01-10. Also TXN999 for 12500."
    res = run_deterministic_audit(base_evidence, narrative)
    assert not res.overall_passed
    assert any("Fabricated" in d.description for d in res.discrepancies)

def test_full_audit_integration(base_evidence):
    narrative = "TXN123 amount = 12500 USD sent by CUST-99 on 2026-01-10. Structuring."
    res = run_deterministic_audit(base_evidence, narrative)
    assert not res.overall_passed
    assert any(d.field == "amount" for d in res.discrepancies)
