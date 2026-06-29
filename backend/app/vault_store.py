import sqlite3
import datetime
from app.crypto import KeyStore, generate_dataset_key, encrypt_content, decrypt_content, DecryptionFailedError
from app.trapdoor_index import TrapdoorIndex, generate_trapdoor_key
from app.access_log import log_access
from app.models import EncryptedBlob

class VaultStore:
    def __init__(self, keystore: KeyStore, db_path: str = "vault_store.db"):
        self.keystore = keystore
        self.db_path = db_path
        self._indexes: dict[str, TrapdoorIndex] = {}
        
        with self._get_conn() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS encrypted_docs (
                    doc_id TEXT PRIMARY KEY,
                    dataset_id TEXT,
                    ciphertext BLOB,
                    nonce BLOB,
                    created_at TEXT
                )
            ''')

    def _get_conn(self):
        return sqlite3.connect(self.db_path)
        
    def _get_or_create_keys(self, dataset_id: str) -> tuple[bytes, bytes]:
        aes_key_id = f"{dataset_id}:aes"
        hmac_key_id = f"{dataset_id}:hmac"
        
        aes_key = self.keystore.get_key(aes_key_id)
        if not aes_key:
            aes_key = generate_dataset_key()
            self.keystore.store_key(aes_key_id, aes_key)
            
        hmac_key = self.keystore.get_key(hmac_key_id)
        if not hmac_key:
            hmac_key = generate_trapdoor_key()
            self.keystore.store_key(hmac_key_id, hmac_key)
            
        return aes_key, hmac_key

    def put(self, dataset_id: str, doc_id: str, content: str) -> None:
        aes_key, hmac_key = self._get_or_create_keys(dataset_id)
        
        blob = encrypt_content(content, aes_key)
        
        with self._get_conn() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO encrypted_docs (doc_id, dataset_id, ciphertext, nonce, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (doc_id, dataset_id, blob.ciphertext, blob.nonce, blob.created_at.isoformat()))
            
        if dataset_id not in self._indexes:
            self._indexes[dataset_id] = TrapdoorIndex()
            
        self._indexes[dataset_id].add_document(doc_id, content, hmac_key)

    def search(self, dataset_id: str, query: str) -> list[dict]:
        hmac_key = self.keystore.get_key(f"{dataset_id}:hmac")
        aes_key = self.keystore.get_key(f"{dataset_id}:aes")
        
        if dataset_id not in self._indexes or not hmac_key or not aes_key:
            log_access(dataset_id, query, [])
            if not hmac_key or not aes_key:
                raise DecryptionFailedError("Dataset keys have been destroyed.")
            return []
            
        matching_doc_ids = list(self._indexes[dataset_id].search(query, hmac_key))
        
        # Log before returning results
        log_access(dataset_id, query, matching_doc_ids)
        
        results = []
        if not matching_doc_ids:
            return results
            
        with self._get_conn() as conn:
            conn.row_factory = sqlite3.Row
            placeholders = ','.join('?' for _ in matching_doc_ids)
            cursor = conn.execute(
                f'SELECT * FROM encrypted_docs WHERE dataset_id = ? AND doc_id IN ({placeholders})',
                [dataset_id] + matching_doc_ids
            )
            
            for row in cursor.fetchall():
                blob = EncryptedBlob(
                    ciphertext=row["ciphertext"],
                    nonce=row["nonce"],
                    created_at=datetime.datetime.fromisoformat(row["created_at"])
                )
                try:
                    plaintext = decrypt_content(blob, aes_key)
                    results.append({
                        "doc_id": row["doc_id"],
                        "content": plaintext,
                        "dataset_id": dataset_id
                    })
                except DecryptionFailedError:
                    raise
                    
        return results

    def forget_dataset(self, dataset_id: str) -> None:
        self.keystore.destroy_key(f"{dataset_id}:aes")
        self.keystore.destroy_key(f"{dataset_id}:hmac")
        
        if dataset_id in self._indexes:
            del self._indexes[dataset_id]
