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


def get_user_id_from_email(db: Session, email: str) -> int | None:
    user = get_user_by_email(db, email)
    return user.id if user else None


def create_bot(db: Session, user_id: int, bot_data: dict) -> models.Bot:
    db_bot = models.Bot(
        uuid=bot_data["id"],
        name=bot_data["name"],
        status=bot_data["status"],
        config=bot_data["config"],
        total_pnl=bot_data["total_pnl"],
        deals_count=bot_data["deals_count"],
        user_id=user_id,
    )
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    return db_bot


def get_bots_by_user(db: Session, user_id: int) -> list[models.Bot]:
    return db.query(models.Bot).filter(models.Bot.user_id == user_id).all()


def get_bot_by_uuid(db: Session, bot_uuid: str) -> models.Bot | None:
    return db.query(models.Bot).filter(models.Bot.uuid == bot_uuid).first()


def update_bot_status(db: Session, bot_uuid: str, status: str):
    bot = get_bot_by_uuid(db, bot_uuid)
    if bot:
        bot.status = status
        db.commit()


def update_bot_stats(
    db: Session, bot_uuid: str, pnl_delta: float, deals_increment: int
):
    bot = get_bot_by_uuid(db, bot_uuid)
    if bot:
        bot.total_pnl += pnl_delta
        bot.deals_count += deals_increment
        db.commit()


def delete_bot(db: Session, bot_uuid: str):
    bot = get_bot_by_uuid(db, bot_uuid)
    if bot:
        db.delete(bot)
        db.commit()


def create_deal(db: Session, bot_id: int, deal_data: dict) -> models.Deal:
    orders_data = deal_data.pop("orders", [])
    db_deal = models.Deal(bot_id=bot_id, **deal_data)
    db.add(db_deal)
    db.commit()
    db.refresh(db_deal)
    for order_data in orders_data:
        create_order(db, db_deal.id, order_data)
    return db_deal


def get_deal_by_bot_id(db: Session, bot_id: int, active_only: bool = False):
    query = db.query(models.Deal).filter(models.Deal.bot_id == bot_id)
    if active_only:
        query = query.filter(models.Deal.status == "active")
    return query.first()


def get_deals_by_bot_id(db: Session, bot_id: int) -> list[models.Deal]:
    return (
        db.query(models.Deal)
        .filter(models.Deal.bot_id == bot_id)
        .order_by(models.Deal.entry_time.desc())
        .all()
    )


def update_deal(db: Session, deal_id: int, deal_data: dict):
    deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if deal:
        for key, value in deal_data.items():
            setattr(deal, key, value)
        db.commit()


def close_deal(db: Session, deal_id: int, realized_pnl: float, close_time: float):
    deal = db.query(models.Deal).filter(models.Deal.id == deal_id).first()
    if deal:
        deal.status = "completed"
        deal.realized_pnl = realized_pnl
        deal.close_time = close_time
        db.commit()


def create_order(db: Session, deal_id: int, order_data: dict) -> models.Order:
    db_order = models.Order(
        deal_id=deal_id,
        order_id_str=order_data["order_id"],
        timestamp=order_data["timestamp"],
        side=order_data["side"],
        price=order_data["price"],
        quantity=order_data["quantity"],
        order_type=order_data["order_type"],
        status=order_data["status"],
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


def get_orders_by_deal_id(db: Session, deal_id: int) -> list[models.Order]:
    return db.query(models.Order).filter(models.Order.deal_id == deal_id).all()


def get_order_by_order_id_str(db: Session, order_id_str: str) -> models.Order | None:
    return (
        db.query(models.Order).filter(models.Order.order_id_str == order_id_str).first()
    )


def update_order_status(
    db: Session,
    order_id_str: str,
    status: str,
    filled_price: float | None = None,
    filled_qty: float | None = None,
):
    order = get_order_by_order_id_str(db, order_id_str)
    if order:
        order.status = status
        if filled_price is not None:
            order.price = filled_price
        if filled_qty is not None:
            order.quantity = filled_qty
        db.commit()
        return order
    return None


def get_all_running_bots(db: Session) -> list[models.Bot]:
    running_statuses = [
        "starting",
        "monitoring",
        "placing_order",
        "in_position",
        "closing",
        "waiting_for_balance",
        "active",
    ]
    return db.query(models.Bot).filter(models.Bot.status.in_(running_statuses)).all()