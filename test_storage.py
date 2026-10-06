import sys
import os
sys.path.insert(0, os.path.abspath("."))
from app.storage import Storage

def run_test():
    storage = Storage("test_sar.db")
    
    # Test investigation
    storage.save_investigation("TXN-101", "COMPLETED")
    
    # Test SAR report
    sar_data = {
        "generated_timestamp": "2023-10-01T10:00:00Z",
        "model_provider": "gemini-test",
        "report_status": "READY_FOR_REVIEW",
        "reviewer_status": "AWAITING_HUMAN_REVIEW",
        "risk_score": 0.85,
        "narrative": "This is a test narrative."
    }
    storage.save_sar_report("SAR-1234", "TXN-101", sar_data)
    
    # Test Audit log
    storage.log_audit("SAR-1234", "SAR_REPORT", "TEST_ACTION", "PASSED", {"info": "test"})
    
    retrieved = storage.get_sar_report("SAR-1234")
    if retrieved and retrieved["narrative"] == "This is a test narrative.":
        print("Storage test passed!")
    else:
        print("Storage test failed!", retrieved)

if __name__ == "__main__":
    run_test()
