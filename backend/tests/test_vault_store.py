import pytest
import os
import sqlite3
from app.crypto import KeyStore, DecryptionFailedError
from app.vault_store import VaultStore
import app.access_log as access_log

@pytest.fixture
def clean_env(tmp_path):
    ks_path = tmp_path / "keystore.json"
    vs_path = tmp_path / "vault.db"
    al_path = tmp_path / "audit.db"
    
    os.environ["VAULT_MASTER_KEY"] = ""
    access_log.DB_PATH = str(al_path)
    
    keystore = KeyStore(storage_path=str(ks_path))
    vault = VaultStore(keystore=keystore, db_path=str(vs_path))
    
    return vault, str(al_path)

def test_put_and_search_roundtrip(clean_env):
    vault, _ = clean_env
    
    vault.put("dataset1", "doc1", "This is a secret document")
    vault.put("dataset1", "doc2", "Another normal text")
    
    results = vault.search("dataset1", "secret")
    assert len(results) == 1
    assert results[0]["doc_id"] == "doc1"
    assert results[0]["content"] == "This is a secret document"
    
def test_search_no_match_creates_access_log(clean_env):
    vault, al_path = clean_env
    
    vault.put("dataset2", "doc1", "The password is foo")
    
    results = vault.search("dataset2", "elephant")
    assert len(results) == 0
    
    logs = access_log.get_access_log("dataset2")
    assert len(logs) == 1
    assert logs[0]["matched_doc_count"] == 0

def test_forget_dataset(clean_env):
    vault, _ = clean_env
    
    vault.put("dataset3", "doc1", "Top secret mission")
    
    results = vault.search("dataset3", "secret")
    assert len(results) == 1
    
    vault.forget_dataset("dataset3")
    
    with pytest.raises(DecryptionFailedError):
        vault.search("dataset3", "secret")
        
    conn = sqlite3.connect(vault.db_path)
    cursor = conn.execute("SELECT * FROM encrypted_docs WHERE dataset_id = 'dataset3'")
    rows = cursor.fetchall()
    assert len(rows) == 1

def test_access_log_never_contains_raw_query(clean_env):
    vault, al_path = clean_env
    
    vault.put("dataset4", "doc1", "My SSN is 1234")
    
    query = "SSN"
    vault.search("dataset4", query)
    
    logs = access_log.get_access_log("dataset4")
    assert len(logs) == 1
    assert query not in logs[0]["query_hash"]
    
    conn = sqlite3.connect(al_path)
    cursor = conn.execute("SELECT * FROM access_log WHERE dataset_id = 'dataset4'")
    row = cursor.fetchone()
    for field in row:
        if isinstance(field, str):
            assert query not in field
