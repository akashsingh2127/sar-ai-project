from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import re
from datetime import datetime, timezone

class Discrepancy(BaseModel):
    field: str
    expected_value: Any
    generated_value: Optional[Any] = None
    severity: str = "HIGH"
    description: str

class AuditResult(BaseModel):
    overall_passed: bool = False
    validation_status: str = "PENDING"
    checks_run: int = 0
    checks_passed: int = 0
    checks_failed: int = 0
    discrepancies: List[Discrepancy] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    checked_transaction_ids: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

def _extract_all_numbers(text: str) -> List[float]:
    """Extract all potential numbers from text (handles commas and decimals)."""
    # Match patterns like 1,000.50 or 1000.50 or 1000
    matches = re.findall(r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b|\b\d+(?:\.\d+)?\b', text)
    nums = []
    for m in matches:
        try:
            clean = m.replace(',', '')
            nums.append(float(clean))
        except ValueError:
            pass
    return nums

def validate_transaction_id(evidence: dict, narrative: str) -> List[Discrepancy]:
    discrepancies = []
    # 1. Check if expected transaction ID is present
    txn_id = None
    if "transaction_details" in evidence and isinstance(evidence["transaction_details"], dict):
        txn_id = evidence["transaction_details"].get("transaction_id")
    elif "transaction_id" in evidence: # Fallback
        txn_id = evidence.get("transaction_id")
        
    narrative_upper = narrative.upper()
    
    if txn_id is not None:
        if str(txn_id).upper() not in narrative_upper:
            discrepancies.append(Discrepancy(
                field="transaction_id",
                expected_value=txn_id,
                description=f"Missing expected Transaction ID: {txn_id}"
            ))
            
    # 2. Check for fabricated IDs (rudimentary check looking for 'TXN...' or 'ID ...' if applicable)
    # If the ID is just a number, it's hard to distinguish from amounts. 
    # We will look for explicit mentions like "Transaction 999" or "TXN999"
    expected_ids = set()
    if txn_id is not None:
        expected_ids.add(str(txn_id).upper())
        
    for hist in evidence.get("customer_history", []):
        if "transaction_id" in hist:
            expected_ids.add(str(hist["transaction_id"]).upper())
            
    for rt in evidence.get("related_transactions", []):
        expected_ids.add(str(rt).upper())
        
    # Regex to find "Transaction [ID]" or "TXN[ID]" or just "TXN-123"
    # To avoid missing prefixes, we will just find all "words" that look like IDs
    # and if they are not in the expected list and contain numbers and letters/dashes, flag them.
    # Alternatively, just look for the expected IDs. Finding fabricated IDs without false positives is hard.
    # Let's refine the regex: we want to capture the whole token if it has TXN.
    txn_mentions = re.findall(r'\b(?:TRANSACTION\s+)?([A-Z0-9_-]*\d+[A-Z0-9_-]*)\b', narrative_upper)
    for mentioned_id in txn_mentions:
        # Ignore normal amounts or dates
        if re.match(r'^[\d.,]+$', mentioned_id) or re.match(r'^\d{4}-\d{2}-\d{2}$', mentioned_id):
            continue
            
        if mentioned_id not in expected_ids and mentioned_id not in ['ID', 'DETAILS', 'REPORT', 'SUMMARY']:
            discrepancies.append(Discrepancy(
                field="transaction_id",
                expected_value=list(expected_ids),
                generated_value=mentioned_id,
                description=f"Fabricated or unsupported Transaction ID referenced: {mentioned_id}"
            ))
            
    return discrepancies

def validate_amount(evidence: dict, narrative: str) -> List[Discrepancy]:
    discrepancies = []
    amount = None
    if "transaction_details" in evidence and isinstance(evidence["transaction_details"], dict):
        amount = evidence["transaction_details"].get("amount")
    elif "amount" in evidence:
        amount = evidence.get("amount")
        
    if amount is not None:
        amount_float = float(amount)
        # Extract all numbers from narrative
        found_nums = _extract_all_numbers(narrative)
        
        # Check if the exact amount or something very close (floating point) is in the narrative
        # If amount_float is not in found_nums, maybe it wasn't mentioned.
        # But wait, if they mention an amount with a currency symbol right next to it, _extract_all_numbers handles it (it just extracts the digit part)
        
        # We should require the amount to be explicitly mentioned.
        # However, some SARs might not explicitly say the exact amount but rather a summary. 
        # For fact-checking, if the exact amount is missing, it's missing evidence.
        
        amt_str = str(amount)
        if amt_str.endswith(".0"):
            amt_str = amt_str[:-2]
        formatted_amt = f"{amount_float:,.2f}"
        formatted_amt_no_cents = f"{amount_float:,.0f}"
        
        # We can just check string inclusion first for speed
        if amt_str not in narrative and formatted_amt not in narrative and formatted_amt_no_cents not in narrative:
            discrepancies.append(Discrepancy(
                field="amount",
                expected_value=amount,
                description=f"Missing or materially incorrect amount. Expected {amount} not found in narrative."
            ))
            
    return discrepancies

def validate_currency(evidence: dict, narrative: str) -> List[Discrepancy]:
    discrepancies = []
    currency = None
    if "transaction_details" in evidence and isinstance(evidence["transaction_details"], dict):
        currency = evidence["transaction_details"].get("currency")
    elif "currency" in evidence:
        currency = evidence.get("currency")
        
    if currency and str(currency).upper() != "UNKNOWN":
        curr_str = str(currency).upper()
        if curr_str not in narrative.upper():
            discrepancies.append(Discrepancy(
                field="currency",
                expected_value=curr_str,
                description=f"Missing expected currency: {curr_str}"
            ))
    return discrepancies

def validate_date(evidence: dict, narrative: str) -> List[Discrepancy]:
    discrepancies = []
    timestamp = None
    if "transaction_details" in evidence and isinstance(evidence["transaction_details"], dict):
        timestamp = evidence["transaction_details"].get("timestamp")
    elif "timestamp" in evidence:
        timestamp = evidence.get("timestamp")
        
    if timestamp:
        # Usually format is YYYY-MM-DD or ISO timestamp
        ts_str = str(timestamp).split("T")[0]
        if ts_str not in narrative:
            discrepancies.append(Discrepancy(
                field="date",
                expected_value=ts_str,
                description=f"Missing Timestamp/Date: {ts_str}"
            ))
    return discrepancies

def validate_customer_id(evidence: dict, narrative: str) -> List[Discrepancy]:
    discrepancies = []
    sender = None
    if "transaction_details" in evidence and isinstance(evidence["transaction_details"], dict):
        sender = evidence["transaction_details"].get("sender")
    elif "sender" in evidence:
        sender = evidence.get("sender")
        
    if sender and str(sender).upper() != "UNKNOWN":
        if str(sender).upper() not in narrative.upper():
            discrepancies.append(Discrepancy(
                field="customer_id",
                expected_value=sender,
                description=f"Missing Sender/Customer ID: {sender}"
            ))
            
    receiver = None
    if "transaction_details" in evidence and isinstance(evidence["transaction_details"], dict):
        receiver = evidence["transaction_details"].get("receiver")
    elif "receiver" in evidence:
        receiver = evidence.get("receiver")
        
    if receiver and str(receiver).upper() != "UNKNOWN":
        if str(receiver).upper() not in narrative.upper():
            discrepancies.append(Discrepancy(
                field="customer_id",
                expected_value=receiver,
                description=f"Missing Receiver ID: {receiver}"
            ))
            
    return discrepancies

def validate_typology_evidence(evidence: dict, narrative: str) -> List[Discrepancy]:
    discrepancies = []
    narrative_upper = narrative.upper()
    
    # 1. Check if all detected typologies are mentioned
    typologies = evidence.get("typologies", [])
    for typo in typologies:
        t_name = typo.get("typology_name", "")
        if t_name and t_name.upper() not in narrative_upper:
            discrepancies.append(Discrepancy(
                field="typology",
                expected_value=t_name,
                severity="MEDIUM",
                description=f"Detected typology '{t_name}' is not mentioned in the narrative."
            ))
            
    # 2. Check for fabricated typologies (typologies mentioned but not in evidence)
    # This requires a list of known typologies to check against
    known_typologies = ["STRUCTURING", "HIGH-VALUE ANOMALY", "CIRCULAR", "RAPID MOVEMENT", "BURST", "COUNTERPARTY"]
    expected_typology_names = [t.get("typology_name", "").upper() for t in typologies]
    
    for kt in known_typologies:
        if kt in narrative_upper:
            # Check if this kt is in expected (partial match)
            is_supported = False
            for etn in expected_typology_names:
                if kt in etn:
                    is_supported = True
                    break
            
            if not is_supported:
                discrepancies.append(Discrepancy(
                    field="typology",
                    expected_value=expected_typology_names,
                    generated_value=kt,
                    severity="HIGH",
                    description=f"Unsupported typology claimed in narrative: {kt}"
                ))
    
    return discrepancies

def run_deterministic_audit(evidence: dict, narrative: str) -> AuditResult:
    """Run all validators and aggregate the results into an AuditResult."""
    if not narrative:
        return AuditResult(
            overall_passed=False,
            validation_status="FAILED",
            discrepancies=[Discrepancy(field="narrative", expected_value="Non-empty", description="Narrative is empty.")]
        )
        
    validators = [
        validate_transaction_id,
        validate_amount,
        validate_currency,
        validate_date,
        validate_customer_id,
        validate_typology_evidence
    ]
    
    all_discrepancies = []
    checks_run = len(validators)
    checks_failed = 0
    
    for validator in validators:
        discs = validator(evidence, narrative)
        if discs:
            all_discrepancies.extend(discs)
            checks_failed += 1
            
    checks_passed = checks_run - checks_failed
    
    unsupported = [d.description for d in all_discrepancies if "unsupported" in d.description.lower() or "fabricated" in d.description.lower()]
    missing = [d.description for d in all_discrepancies if "missing" in d.description.lower()]
    
    passed = len(all_discrepancies) == 0
    
    # Extract transaction IDs explicitly to populate checked_transaction_ids
    txn_id = None
    if "transaction_details" in evidence and isinstance(evidence["transaction_details"], dict):
        txn_id = evidence["transaction_details"].get("transaction_id")
    elif "transaction_id" in evidence:
        txn_id = evidence.get("transaction_id")
        
    return AuditResult(
        overall_passed=passed,
        validation_status="PASSED" if passed else "FAILED",
        checks_run=checks_run,
        checks_passed=checks_passed,
        checks_failed=checks_failed,
        discrepancies=all_discrepancies,
        unsupported_claims=unsupported,
        missing_evidence=missing,
        checked_transaction_ids=[str(txn_id)] if txn_id else []
    )
