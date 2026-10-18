import os
from .base import StorageProvider
from .sqlite_store import SQLiteStore
from .jsonl_store import JsonlStore

def get_storage() -> StorageProvider:
    """
    Factory function to get the configured storage provider.
    Reads STORAGE_BACKEND env var (default: sqlite).
    
    For JSONL backend:
    Canonical configuration is AUDIT_LOG_PATH (default: 'audit_trail.jsonl').
    Falls back to legacy SAR_JSONL_PATH if AUDIT_LOG_PATH is not set.
    
    For SQLite backend:
    Reads SAR_DB_PATH (default: 'sar_data.db').
    """
    backend = os.environ.get("STORAGE_BACKEND", "sqlite").lower()
    
    if backend == "jsonl":
        file_path = os.environ.get("AUDIT_LOG_PATH") or os.environ.get("SAR_JSONL_PATH", "audit_trail.jsonl")
        return JsonlStore(file_path)
    else:
        # Default to SQLite
        db_path = os.environ.get("SAR_DB_PATH", "sar_data.db")
        return SQLiteStore(db_path)
