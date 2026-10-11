import logging
import json
import os
from datetime import datetime, timezone

def setup_logger(name: str = "sar_ai"):
    """
    Configure and return a structured logger for the SAR-AI application.
    Logs to stdout and to logs/sar_ai.log
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times if instantiated multiple times
    if logger.hasHandlers():
        return logger
        
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(log_level)
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'sar_ai.log')
    
    # File Handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Formatter
    # We use a structured JSON-like or simple structured format
    # For a simple approach without external deps, standard formatting is fine,
    # but we can make it easily parsable.
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%SZ'
    )
    
    # For file, we can optionally use JSON if desired, but string format is often sufficient
    # Let's use string format for simplicity and readability without extra libs
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class StructuredAuditLogger:
    """Helper to log security/audit events distinctly from debug info."""
    def __init__(self):
        self.logger = setup_logger("sar_ai.audit")
        
    def log_event(self, event_type: str, details: dict, status: str = "SUCCESS"):
        # Strip highly sensitive data from details before logging
        safe_details = details.copy()
        if 'api_key' in safe_details:
            safe_details['api_key'] = "***REDACTED***"
            
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "status": status,
            "details": safe_details
        }
        
        self.logger.info(json.dumps(log_entry))
        
audit_logger = StructuredAuditLogger()
