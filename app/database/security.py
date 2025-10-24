from cryptography.fernet import Fernet
import os
import bcrypt


def get_fernet() -> Fernet:
    key = os.environ.get("ENCRYPTION_KEY")
    if not key:
        raise ValueError("ENCRYPTION_KEY environment variable not set.")
    return Fernet(key.encode())


def encrypt_data(data: str) -> bytes:
    f = get_fernet()
    return f.encrypt(data.encode())


def decrypt_data(encrypted_data: bytes) -> str:
    f = get_fernet()
    return f.decrypt(encrypted_data).decode()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())