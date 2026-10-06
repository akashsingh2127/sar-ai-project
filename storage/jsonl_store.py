import json
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from .base import StorageProvider

logger = logging.getLogger(__name__)

class JsonlStore(StorageProvider):
    def __init__(self, file_path: str):
        self.file_path = file_path
        # Ensure file exists
        if not os.path.exists(self.file_path):
            try:
                with open(self.file_path, "w") as f:
                    pass
            except Exception as e:
                logger.error(f"Failed to create JSONL file at {self.file_path}: {e}")

    def _append_record(self, record: Dict[str, Any]):
        try:
            with open(self.file_path, "a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.error(f"Failed to write to JSONL store: {e}")

    def save_investigation(self, inv_id: str, status: str):
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "type": "investigation_update",
            "timestamp": now,
            "investigation_id": inv_id,
            "status": status
        }
        self._append_record(record)

    def save_sar_report(self, sar_id: str, inv_id: str, sar_data: Dict[str, Any]):
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "type": "sar_report_update",
            "timestamp": now,
            "sar_id": sar_id,
            "investigation_id": inv_id,
            "report_status": sar_data.get("report_status", "GENERATED"),
            "reviewer_status": sar_data.get("reviewer_status", "AWAITING_HUMAN_REVIEW"),
            "sar_data": sar_data
        }
        self._append_record(record)

    def log_audit(self, entity_id: str, entity_type: str, action: str, status: str, details: Optional[Dict[str, Any]] = None):
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "type": "audit_log",
            "timestamp": now,
            "entity_id": entity_id,
            "entity_type": entity_type,
            "action": action,
            "status": status,
            "details": details or {}
        }
        self._append_record(record)

    def get_sar_report(self, sar_id: str) -> Optional[Dict[str, Any]]:
        # In an append-only JSONL, we scan for the latest record with matching sar_id
        latest_sar = None
        try:
            with open(self.file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        if record.get("type") == "sar_report_update" and record.get("sar_id") == sar_id:
                            # Update with latest found
                            latest_sar = record.get("sar_data")
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Error reading JSONL for SAR report: {e}")
        return latest_sar

    def get_all_sars(self) -> List[Dict[str, Any]]:
        sars = {}
        try:
            with open(self.file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        if record.get("type") == "sar_report_update":
                            sar_id = record.get("sar_id")
                            if sar_id:
                                sars[sar_id] = record.get("sar_data")
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Error reading JSONL for all SARs: {e}")
        # Return descending by some timestamp ideally, but we'll just return list
        return list(sars.values())

    def get_investigation(self, inv_id: str) -> Optional[Dict[str, Any]]:
        latest = None
        try:
            with open(self.file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        if record.get("type") == "investigation_update" and record.get("investigation_id") == inv_id:
                            latest = record
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Error reading JSONL for investigation: {e}")
        return latest

    def get_audit_history(self) -> List[Dict[str, Any]]:
        history = []
        try:
            with open(self.file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        if record.get("type") == "audit_log":
                            history.append(record)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Error reading JSONL for audit history: {e}")
        # Sort descending by timestamp
        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return history
