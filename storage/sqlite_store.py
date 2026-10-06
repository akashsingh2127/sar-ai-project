import sqlite3
import json
import logging
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Dict, Any, Optional, List

from .base import StorageProvider

logger = logging.getLogger(__name__)

class SQLiteStore(StorageProvider):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS investigations (
                        investigation_id TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sar_reports (
                        sar_id TEXT PRIMARY KEY,
                        investigation_id TEXT NOT NULL,
                        generated_timestamp TEXT NOT NULL,
                        model_provider TEXT,
                        report_status TEXT,
                        reviewer_status TEXT,
                        risk_score REAL,
                        content_json TEXT NOT NULL,
                        FOREIGN KEY (investigation_id) REFERENCES investigations (investigation_id)
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entity_id TEXT NOT NULL,
                        entity_type TEXT NOT NULL,
                        action TEXT NOT NULL,
                        status TEXT NOT NULL,
                        details TEXT,
                        timestamp TEXT NOT NULL
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize SQLite database at {self.db_path}: {e}")
            raise

    @contextmanager
    def get_conn(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            # Use dictionary-like row objects
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            logger.error(f"SQLite connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def save_investigation(self, inv_id: str, status: str):
        now = datetime.now(timezone.utc).isoformat()
        try:
            with self.get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO investigations (investigation_id, status, created_at, updated_at) VALUES (?, ?, ?, ?) "
                    "ON CONFLICT(investigation_id) DO UPDATE SET status=excluded.status, updated_at=excluded.updated_at",
                    (inv_id, status, now, now)
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to save investigation {inv_id}: {e}")

    def save_sar_report(self, sar_id: str, inv_id: str, sar_data: Dict[str, Any]):
        now = datetime.now(timezone.utc).isoformat()
        try:
            with self.get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO sar_reports (sar_id, investigation_id, generated_timestamp, model_provider, report_status, reviewer_status, risk_score, content_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                    "ON CONFLICT(sar_id) DO UPDATE SET report_status=excluded.report_status, reviewer_status=excluded.reviewer_status, content_json=excluded.content_json",
                    (
                        sar_id,
                        inv_id,
                        sar_data.get("generated_timestamp", now),
                        sar_data.get("model_provider", "UNKNOWN"),
                        sar_data.get("report_status", "GENERATED"),
                        sar_data.get("reviewer_status", "AWAITING_HUMAN_REVIEW"),
                        float(sar_data.get("risk_score", 0.0)),
                        json.dumps(sar_data)
                    )
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to save SAR report {sar_id}: {e}")

    def log_audit(self, entity_id: str, entity_type: str, action: str, status: str, details: Optional[Dict[str, Any]] = None):
        now = datetime.now(timezone.utc).isoformat()
        details_str = json.dumps(details) if details else "{}"
        try:
            with self.get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO audit_logs (entity_id, entity_type, action, status, details, timestamp) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (entity_id, entity_type, action, status, details_str, now)
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to log audit event {action} for {entity_type} {entity_id}: {e}")

    def get_sar_report(self, sar_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self.get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT content_json FROM sar_reports WHERE sar_id = ?", (sar_id,))
                row = cursor.fetchone()
                if row:
                    return json.loads(row["content_json"])
                return None
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve SAR report {sar_id}: {e}")
            return None

    def get_all_sars(self) -> List[Dict[str, Any]]:
        try:
            with self.get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT content_json FROM sar_reports ORDER BY generated_timestamp DESC")
                rows = cursor.fetchall()
                return [json.loads(row["content_json"]) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve all SAR reports: {e}")
            return []

    def get_investigation(self, inv_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self.get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM investigations WHERE investigation_id = ?", (inv_id,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve investigation {inv_id}: {e}")
            return None

    def get_audit_history(self) -> List[Dict[str, Any]]:
        try:
            with self.get_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC")
                rows = cursor.fetchall()
                result = []
                for row in rows:
                    row_dict = dict(row)
                    # parse details back to dict if valid JSON
                    if row_dict.get("details"):
                        try:
                            row_dict["details"] = json.loads(row_dict["details"])
                        except json.JSONDecodeError:
                            pass
                    result.append(row_dict)
                return result
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve audit history: {e}")
            return []
