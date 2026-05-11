import os
import pytest
from cryptography.fernet import Fernet
from src.core.auth import CredentialManager, SecretStore

@pytest.fixture
def master_key():
    return Fernet.generate_key().decode()

@pytest.fixture
def auth_manager(master_key, tmp_path):
    # Use a temporary database file
    db_path = str(tmp_path / "test_creds.db") if 'tmp_path' in locals() else "test_creds.db"
    # To avoid conflicts and pollution, we use a unique path per test via tmp_path
    # but the current fixture signature needs to be handled carefully.
    # Let's just use a temporary file.
    return None # Handled inside test or redefined

def test_secret_store_encryption(master_key):
    store = SecretStore(master_key)
    original = "my-secret-password"
    encrypted = store.encrypt(original)
    assert encrypted != original
    assert store.decrypt(encrypted) == original

def test_secret_store_invalid_key():
    with pytest.raises(ValueError):
        SecretStore("invalid-key")

def test_credential_manager_persistence(tmp_path, master_key):
    db_path = str(tmp_path / "test_creds.db")
    manager = CredentialManager(db_path=db_path, master_key=master_key)
    
    service = "twitter"
    secret = "twitter-api-key-123"
    
    manager.save_credential(service, secret)
    assert manager.get_credential(service) == secret
    
    # Test updating
    new_secret = "twitter-api-key-456"
    manager.save_credential(service, new_secret)
    assert manager.get_credential(service) == new_secret

def test_credential_manager_missing_key(tmp_path):
    # Clear env var
    if "PUBLISHER_MASTER_KEY" in os.environ:
        del os.environ["PUBLISHER_MASTER_KEY"]
    
    with pytest.raises(EnvironmentError):
        CredentialManager(db_path=str(tmp_path / "test.db"))

def test_credential_manager_env_key(tmp_path, master_key):
    os.environ["PUBLISHER_MASTER_KEY"] = master_key
    db_path = str(tmp_path / "test_env_creds.db")
    manager = CredentialManager(db_path=db_path) # Should use env var
    
    service = "github"
    secret = "gh-token-789"
    manager.save_credential(service, secret)
    assert manager.get_credential(service) == secret
    
    del os.environ["PUBLISHER_MASTER_KEY"]
