from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    ForeignKey,
    JSON,
    LargeBinary,
    DateTime,
)
from sqlalchemy.orm import relationship
from .database import Base
import datetime


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    subscription_tier = Column(String, default="FREE")
    email_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String, unique=True, index=True, nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    password_reset_token = Column(String, unique=True, index=True, nullable=True)
    password_reset_token_expires = Column(DateTime, nullable=True)
    encrypted_api_key = Column(LargeBinary, nullable=True)
    encrypted_secret_key = Column(LargeBinary, nullable=True)
    bots = relationship("Bot", back_populates="owner")


class Bot(Base):
    __tablename__ = "bots"
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True)
    status = Column(String, default="stopped")
    config = Column(JSON)
    total_pnl = Column(Float, default=0.0)
    deals_count = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="bots")
    deals = relationship("Deal", back_populates="bot", cascade="all, delete-orphan")


class Deal(Base):
    __tablename__ = "deals"
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, index=True)
    entry_time = Column(Float)
    close_time = Column(Float, nullable=True)
    realized_pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    average_entry_price = Column(Float, default=0.0)
    total_quantity = Column(Float, default=0.0)
    bot_id = Column(Integer, ForeignKey("bots.id"))
    bot = relationship("Bot", back_populates="deals")
    orders = relationship("Order", back_populates="deal", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_id_str = Column(String, unique=True, index=True)
    timestamp = Column(Float)
    side = Column(String)
    price = Column(Float)
    quantity = Column(Float)
    order_type = Column(String)
    status = Column(String)
    deal_id = Column(Integer, ForeignKey("deals.id"))
    deal = relationship("Deal", back_populates="orders")