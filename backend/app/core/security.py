from cryptography.fernet import Fernet
import base64
import hashlib


def get_fernet(key: str) -> Fernet:
    key_bytes = hashlib.sha256(key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_bytes))


def encrypt_string(plain_text: str, key: str) -> str:
    f = get_fernet(key)
    encrypted = f.encrypt(plain_text.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_string(cipher_text: str, key: str) -> str:
    try:
        f = get_fernet(key)
        decoded = base64.urlsafe_b64decode(cipher_text.encode())
        return f.decrypt(decoded).decode()
    except Exception:
        return ""


def mask_string(text: str, keep_start: int = 4, keep_end: int = 4) -> str:
    if not text or len(text) <= keep_start + keep_end:
        return "*" * len(text) if text else ""
    return text[:keep_start] + "*" * (len(text) - keep_start - keep_end) + text[-keep_end:]
