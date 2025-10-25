from sqlalchemy.orm import Session
from . import models, security
import json
import uuid
from datetime import datetime, timedelta


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_verification_token(db: Session, token: str):
    return db.query(models.User).filter(models.User.verification_token == token).first()


def create_password_reset_token(db: Session, user: models.User) -> str:
    token = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(hours=1)
    user.password_reset_token = token
    user.password_reset_token_expires = expires
    db.commit()
    return token


def get_user_by_password_reset_token(db: Session, token: str):
    return (
        db.query(models.User).filter(models.User.password_reset_token == token).first()
    )


def create_user(db: Session, username: str, email: str, password: str):
    hashed_password = security.hash_password(password)
    verification_token = str(uuid.uuid4())
    token_expires = datetime.utcnow() + timedelta(hours=24)
    db_user = models.User(
        email=email,
        hashed_password=hashed_password,
        username=username,
        verification_token=verification_token,
        verification_token_expires=token_expires,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_api_keys(db: Session, user_id: int, api_key: str, secret_key: str):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.encrypted_api_key = security.encrypt_data(api_key)
        user.encrypted_secret_key = security.encrypt_data(secret_key)
        db.commit()


def get_user_api_keys(db: Session, user_id: int) -> dict | None:
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user and user.encrypted_api_key and user.encrypted_secret_key:
        return {
            "api_key": security.decrypt_data(user.encrypted_api_key),
            "secret_key": security.decrypt_data(user.encrypted_secret_key),
        }
    return None