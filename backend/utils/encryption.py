from cryptography.fernet import Fernet
import os
import base64

# Get key from env or generate one (for dev only, in prod this must be persistent)
# In a real app, this should be loaded from a secure secret manager
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    # For development convenience, generate one if missing, but warn
    # This key will change on restart, invalidating stored keys!
    print("WARNING: ENCRYPTION_KEY not set. Generating temporary key. Stored API keys will be invalid after restart.")
    ENCRYPTION_KEY = Fernet.generate_key().decode()

cipher_suite = Fernet(ENCRYPTION_KEY.encode())

def encrypt_value(value: str) -> str:
    """Encrypts a string value."""
    if not value:
        return None
    encrypted_bytes = cipher_suite.encrypt(value.encode())
    return base64.urlsafe_b64encode(encrypted_bytes).decode()

def decrypt_value(encrypted_value: str) -> str:
    """Decrypts an encrypted string value."""
    if not encrypted_value:
        return None
    try:
        decoded_bytes = base64.urlsafe_b64decode(encrypted_value)
        decrypted_bytes = cipher_suite.decrypt(decoded_bytes)
        return decrypted_bytes.decode()
    except Exception as e:
        print(f"Decryption failed: {e}")
        return None
