import json
from datetime import datetime

def log_audit(evidence, sar_report):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "transaction_id": evidence.get('transaction_id', 'Unknown'),
        "risk_level": evidence.get('risk_score', 0), # Uses .get() to avoid KeyError
        "typology": evidence.get('typology', 'N/A'),
        "summary": sar_report[:100] + "..."
    }
    with open("audit_trail.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")