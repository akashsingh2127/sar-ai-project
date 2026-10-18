import pytest
import os
import json
from storage.sqlite_store import SQLiteStore
from storage.jsonl_store import JsonlStore
from storage import get_storage

@pytest.fixture
def sqlite_store(tmp_path):
    db_path = tmp_path / "test_sar.db"
    return SQLiteStore(str(db_path))

@pytest.fixture
def jsonl_store(tmp_path):
    jsonl_path = tmp_path / "test_audit.jsonl"
    return JsonlStore(str(jsonl_path))

def test_sqlite_investigation(sqlite_store):
    sqlite_store.save_investigation("INV-100", "OPEN")
    inv = sqlite_store.get_investigation("INV-100")
    assert inv is not None
    assert inv["status"] == "OPEN"
    
    # Update investigation
    sqlite_store.save_investigation("INV-100", "CLOSED")
    inv = sqlite_store.get_investigation("INV-100")
    assert inv["status"] == "CLOSED"

def test_sqlite_sar_report(sqlite_store):
    sqlite_store.save_investigation("INV-101", "OPEN")
    sar_data = {"report_status": "DRAFT", "narrative": "test"}
    sqlite_store.save_sar_report("SAR-200", "INV-101", sar_data)
    
    report = sqlite_store.get_sar_report("SAR-200")
    assert report is not None
    assert report["narrative"] == "test"
    
    # Update
    sar_data["narrative"] = "updated test"
    sqlite_store.save_sar_report("SAR-200", "INV-101", sar_data)
    report = sqlite_store.get_sar_report("SAR-200")
    assert report["narrative"] == "updated test"
    
    all_sars = sqlite_store.get_all_sars()
    assert len(all_sars) == 1

def test_sqlite_audit_log(sqlite_store):
    sqlite_store.log_audit("SAR-200", "SAR_REPORT", "REVIEWED", "PASSED", {"notes": "ok"})
    history = sqlite_store.get_audit_history()
    assert len(history) == 1
    assert history[0]["entity_id"] == "SAR-200"
    assert history[0]["action"] == "REVIEWED"
    assert history[0]["details"]["notes"] == "ok"

def test_sqlite_failure_handling(tmp_path):
    # Invalid path
    bad_path = "/invalid_path/test.db"
    with pytest.raises(Exception):
        SQLiteStore(bad_path)

def test_jsonl_investigation(jsonl_store):
    jsonl_store.save_investigation("INV-300", "OPEN")
    inv = jsonl_store.get_investigation("INV-300")
    assert inv is not None
    assert inv["investigation_id"] == "INV-300"
    assert inv["status"] == "OPEN"

    jsonl_store.save_investigation("INV-300", "CLOSED")
    inv = jsonl_store.get_investigation("INV-300")
    assert inv["status"] == "CLOSED"

def test_jsonl_sar_report(jsonl_store):
    sar_data = {"report_status": "DRAFT", "narrative": "jsonl test"}
    jsonl_store.save_sar_report("SAR-400", "INV-300", sar_data)
    
    report = jsonl_store.get_sar_report("SAR-400")
    assert report is not None
    assert report["narrative"] == "jsonl test"
    
    sar_data["narrative"] = "updated jsonl test"
    jsonl_store.save_sar_report("SAR-400", "INV-300", sar_data)
    report = jsonl_store.get_sar_report("SAR-400")
    assert report["narrative"] == "updated jsonl test"

    all_sars = jsonl_store.get_all_sars()
    assert len(all_sars) == 1

def test_jsonl_audit_log(jsonl_store):
    jsonl_store.log_audit("SAR-400", "SAR_REPORT", "REVIEWED", "FAILED")
    history = jsonl_store.get_audit_history()
    assert len(history) == 1
    assert history[0]["entity_id"] == "SAR-400"
    assert history[0]["action"] == "REVIEWED"

def test_jsonl_malformed_record(jsonl_store):
    # Manually append a broken line
    with open(jsonl_store.file_path, "a") as f:
        f.write("this is not json\n")
    
    jsonl_store.log_audit("SAR-401", "SAR_REPORT", "TEST", "OK")
    history = jsonl_store.get_audit_history()
    
    # Should safely skip the malformed line and read the good one
    assert len(history) == 1
    assert history[0]["entity_id"] == "SAR-401"

def test_get_storage_factory(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "jsonl")
    store = get_storage()
    assert isinstance(store, JsonlStore)
    
    monkeypatch.setenv("STORAGE_BACKEND", "sqlite")
    store = get_storage()
    assert isinstance(store, SQLiteStore)

def test_storage_audit_log_path_canonical(monkeypatch, tmp_path):
    custom_path = str(tmp_path / "canonical_audit.jsonl")
    monkeypatch.setenv("STORAGE_BACKEND", "jsonl")
    monkeypatch.setenv("AUDIT_LOG_PATH", custom_path)
    monkeypatch.delenv("SAR_JSONL_PATH", raising=False)
    
    store = get_storage()
    assert isinstance(store, JsonlStore)
    assert store.file_path == custom_path

def test_storage_sar_jsonl_path_legacy_fallback(monkeypatch, tmp_path):
    legacy_path = str(tmp_path / "legacy_audit.jsonl")
    monkeypatch.setenv("STORAGE_BACKEND", "jsonl")
    monkeypatch.delenv("AUDIT_LOG_PATH", raising=False)
    monkeypatch.setenv("SAR_JSONL_PATH", legacy_path)
    
    store = get_storage()
    assert isinstance(store, JsonlStore)
    assert store.file_path == legacy_path

def test_storage_precedence_audit_over_legacy(monkeypatch, tmp_path):
    canonical_path = str(tmp_path / "canonical.jsonl")
    legacy_path = str(tmp_path / "legacy.jsonl")
    monkeypatch.setenv("STORAGE_BACKEND", "jsonl")
    monkeypatch.setenv("AUDIT_LOG_PATH", canonical_path)
    monkeypatch.setenv("SAR_JSONL_PATH", legacy_path)
    
    store = get_storage()
    assert isinstance(store, JsonlStore)
    assert store.file_path == canonical_path

def test_storage_preserves_existing_data(tmp_path):
    target = tmp_path / "existing_audit.jsonl"
    with open(target, "w") as f:
        f.write(json.dumps({"type": "audit_log", "entity_id": "PRESERVED_1", "action": "INITIAL", "timestamp": "2023-01-01T00:00:00Z"}) + "\n")
        
    store = JsonlStore(str(target))
    history = store.get_audit_history()
    assert len(history) == 1
    assert history[0]["entity_id"] == "PRESERVED_1"
    
    # Appending a new record preserves the old one
    store.log_audit("NEW_2", "SAR_REPORT", "APPEND", "OK")
    updated_history = store.get_audit_history()
    assert len(updated_history) == 2
    assert any(h["entity_id"] == "PRESERVED_1" for h in updated_history)
    assert any(h["entity_id"] == "NEW_2" for h in updated_history)
