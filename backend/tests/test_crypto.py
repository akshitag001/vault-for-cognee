import pytest
import os
from app.crypto import (
    generate_dataset_key, 
    KeyStore, 
    encrypt_content, 
    decrypt_content, 
    DecryptionFailedError
)

@pytest.fixture
def keystore(tmp_path):
    # Use a temporary file for the keystore to avoid leaving side effects
    ks_path = tmp_path / "test_keystore.json"
    
    # Generate an ephemeral master key for testing so it doesn't clutter output
    os.environ["VAULT_MASTER_KEY"] = ""
    
    return KeyStore(storage_path=str(ks_path))

def test_encrypt_decrypt_roundtrip():
    key = generate_dataset_key()
    plaintext = "This is a highly sensitive secret."
    
    blob = encrypt_content(plaintext, key)
    
    assert blob.ciphertext != plaintext.encode('utf-8')
    
    decrypted = decrypt_content(blob, key)
    assert decrypted == plaintext

def test_decrypt_wrong_key_raises_error():
    key1 = generate_dataset_key()
    key2 = generate_dataset_key()
    
    plaintext = "Sensitive data"
    blob = encrypt_content(plaintext, key1)
    
    with pytest.raises(DecryptionFailedError):
        decrypt_content(blob, key2)

def test_cryptographic_erasure(keystore):
    dataset_id = "test_dataset_1"
    key = generate_dataset_key()
    
    # 1. Store the key
    keystore.store_key(dataset_id, key)
    
    # 2. Encrypt content
    plaintext = "Permanent record to be erased"
    retrieved_key = keystore.get_key(dataset_id)
    assert retrieved_key is not None
    
    blob = encrypt_content(plaintext, retrieved_key)
    
    # 3. Verify it decrypts currently
    decrypted = decrypt_content(blob, retrieved_key)
    assert decrypted == plaintext
    
    # 4. Destroy the key (cryptographic erasure)
    assert keystore.destroy_key(dataset_id) is True
    
    # 5. Verify the key is gone
    erased_key = keystore.get_key(dataset_id)
    assert erased_key is None
    
    # 6. Attempt to decrypt should fail gracefully indicating unrecoverable
    with pytest.raises(DecryptionFailedError, match="permanently unrecoverable"):
        decrypt_content(blob, erased_key)
