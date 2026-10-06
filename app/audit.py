import json
from datetime import datetime, timezone
from storage import get_storage

def log_audit(evidence, sar_report, structured_sar=None):
    """
    Logs investigation details to the configured storage backend.
    Maintains backward compatibility with string sar_report.
    """
    storage = get_storage()
    
    # Extract IDs
    transaction_id = str(evidence.get('transaction_details', {}).get('transaction_id') or evidence.get('transaction_id', 'Unknown'))
    
    if structured_sar:
        # Save as StructuredSAR object
        sar_id = structured_sar.sar_id
        storage.save_investigation(transaction_id, structured_sar.report_status.value if hasattr(structured_sar.report_status, "value") else structured_sar.report_status)
        storage.save_sar_report(sar_id, transaction_id, json.loads(structured_sar.to_json()))
        
        # Log audit action
        storage.log_audit(
            entity_id=sar_id,
            entity_type="SAR_REPORT",
            action="GENERATION_AND_AUDIT",
            status=structured_sar.validation_status,
            details=structured_sar.audit_result
        )
    else:
        # Fallback for old logic or tests
        storage.save_investigation(transaction_id, "COMPLETED")
        storage.log_audit(
            entity_id=transaction_id,
            entity_type="INVESTIGATION",
            action="LEGACY_LOG",
            status="UNKNOWN",
            details={
                "risk_level": evidence.get('risk_score', 0),
                "summary": str(sar_report)[:100] + "..." if sar_report else ""
            }
        )