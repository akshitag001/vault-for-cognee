import sqlite3
import hashlib
import json
from datetime import datetime, timezone

DB_PATH = "vault_audit.db"

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS access_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            dataset_id TEXT,
            query_hash TEXT,
            matched_doc_count INTEGER,
            matched_doc_ids TEXT
        )
    ''')
    return conn

def log_access(dataset_id: str, query: str, matched_doc_ids: list[str]) -> None:
    """Logs an access attempt against a sensitive dataset."""
    query_hash = hashlib.sha256(query.encode('utf-8')).hexdigest()
    timestamp = datetime.now(timezone.utc).isoformat()
    
    with _get_conn() as conn:
        conn.execute(
            'INSERT INTO access_log (timestamp, dataset_id, query_hash, matched_doc_count, matched_doc_ids) VALUES (?, ?, ?, ?, ?)',
            (timestamp, dataset_id, query_hash, len(matched_doc_ids), json.dumps(matched_doc_ids))
        )

def get_access_log(dataset_id: str | None = None) -> list[dict]:
    """Retrieves audit log entries, most recent first."""
    with _get_conn() as conn:
        conn.row_factory = sqlite3.Row
        if dataset_id:
            cursor = conn.execute(
                'SELECT * FROM access_log WHERE dataset_id = ? ORDER BY timestamp DESC',
                (dataset_id,)
            )
        else:
            cursor = conn.execute(
                'SELECT * FROM access_log ORDER BY timestamp DESC'
            )
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row["id"],
                "timestamp": row["timestamp"],
                "dataset_id": row["dataset_id"],
                "query_hash": row["query_hash"],
                "matched_doc_count": row["matched_doc_count"],
                "matched_doc_ids": json.loads(row["matched_doc_ids"])
            })
        return results
