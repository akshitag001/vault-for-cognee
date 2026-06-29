import os
import json
import base64
import logging
from datetime import datetime, timezone
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from app.models import EncryptedBlob

logger = logging.getLogger(__name__)

class DecryptionFailedError(Exception):
    """Raised when decryption fails due to invalid key, missing key, or corrupted data."""
    pass

def generate_dataset_key() -> bytes:
    """Generates a fresh 256-bit (32 bytes) key for a dataset."""
    return AESGCM.generate_key(bit_length=256)

class KeyStore:
    """
    Manages cryptographic keys for datasets.
    
    Note: In production, this should be replaced with a proper secrets manager
    (e.g., AWS KMS, HashiCorp Vault), rather than storing keys in memory or a local file.
    """
    def __init__(self, storage_path: str = "keystore.json"):
        self.storage_path = storage_path
        self._keys: dict[str, bytes] = {}
        
        master_key_b64 = os.environ.get("VAULT_MASTER_KEY")
        if not master_key_b64:
            logger.warning(
                "VAULT_MASTER_KEY not set in environment! Generating an ephemeral master key. "
                "WARNING: Restarting this process will result in the loss of access to ALL vault data, "
                "as the master key will be lost. This is intentional behavior for the fallback key."
            )
            self._master_key = AESGCM.generate_key(bit_length=256)
        else:
            self._master_key = base64.b64decode(master_key_b64)
            
        self._load()

    def _load(self):
        if not os.path.exists(self.storage_path):
            return
            
        try:
            with open(self.storage_path, 'rb') as f:
                data = f.read()
            if not data:
                return
                
            aesgcm = AESGCM(self._master_key)
            nonce = data[:12]
            ciphertext = data[12:]
            
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            keys_dict = json.loads(plaintext.decode('utf-8'))
            self._keys = {k: base64.b64decode(v) for k, v in keys_dict.items()}
        except InvalidTag:
            logger.error("Failed to decrypt keystore. Master key might be incorrect.")
        except Exception as e:
            logger.error(f"Error loading keystore: {e}")

    def _save(self):
        aesgcm = AESGCM(self._master_key)
        nonce = os.urandom(12)
        keys_dict = {k: base64.b64encode(v).decode('utf-8') for k, v in self._keys.items()}
        plaintext = json.dumps(keys_dict).encode('utf-8')
        
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        
        with open(self.storage_path, 'wb') as f:
            f.write(nonce + ciphertext)

    def store_key(self, dataset_id: str, key: bytes) -> None:
        """Stores a key for a specific dataset ID."""
        self._keys[dataset_id] = key
        self._save()

    def get_key(self, dataset_id: str) -> bytes | None:
        """Retrieves the key for a dataset ID, or None if it doesn't exist."""
        return self._keys.get(dataset_id)

    def destroy_key(self, dataset_id: str) -> bool:
        """
        Cryptographically erases a dataset by removing its encryption key.
        Returns True if a key was destroyed, False if the key didn't exist.
        """
        if dataset_id in self._keys:
            del self._keys[dataset_id]
            self._save()
            return True
        return False

def encrypt_content(plaintext: str, key: bytes) -> EncryptedBlob:
    """Encrypts plaintext using AES-256-GCM."""
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
    
    return EncryptedBlob(
        ciphertext=ciphertext,
        nonce=nonce,
        created_at=datetime.now(timezone.utc)
    )

def decrypt_content(blob: EncryptedBlob, key: bytes | None) -> str:
    """Decrypts an EncryptedBlob back into plaintext."""
    if not key:
        raise DecryptionFailedError("Key is missing or destroyed. Data is permanently unrecoverable.")
        
    try:
        aesgcm = AESGCM(key)
        plaintext_bytes = aesgcm.decrypt(blob.nonce, blob.ciphertext, None)
        return plaintext_bytes.decode('utf-8')
    except InvalidTag as e:
        raise DecryptionFailedError("Invalid key, corrupted data, or authentication tag mismatch.") from e
    except Exception as e:
        raise DecryptionFailedError(f"Decryption failed: {str(e)}") from e
