import reflex as rx
from typing import TypedDict, Literal
import re
import logging
from app.database import crud, security, models
from app.database.database import get_db
from sqlalchemy.orm import Session
from app.services.email_service import EmailService


class User(TypedDict):
    username: str
    email: str
    subscription_tier: Literal["FREE", "PRO"]
    email_verified: bool


class AuthState(rx.State):
    is_logged_in: bool = False
    current_user: User | None = None
    login_error: str = ""

    def _get_db(self) -> Session:
        return next(get_db())

    def _validate_password(self, password: str) -> bool:
        if len(password) < 8:
            self.login_error = "Password must be at least 8 characters long."
            return False
        if not re.search("[A-Z]", password):
            self.login_error = "Password must contain an uppercase letter."
            return False
        if not re.search("[a-z]", password):
            self.login_error = "Password must contain a lowercase letter."
            return False
        if not re.search("[0-9]", password):
            self.login_error = "Password must contain a number."
            return False
        return True

    async def _send_verification_email_async(self, user: models.User):
        verification_link = f"{self.router.page.full_raw_url.replace('/register', '').replace('/login', '')}/verify-email/{user.verification_token}"
        email_service = await self.get_state(EmailService)
        email_service.send_verification_email(user.email, verification_link)
        return rx.toast.info(
            "A verification email has been sent. Please check your inbox.",
            duration=5000,
        )

    @rx.event
    def set_user_tier(self, tier: Literal["FREE", "PRO"]):
        if not self.current_user:
            return
        db = self._get_db()
        user = crud.get_user_by_email(db, self.current_user["email"])
        if user:
            user.subscription_tier = tier
            db.commit()
            self.current_user["subscription_tier"] = tier
        db.close()

    @rx.event
    def set_user_tier_by_email(self, email: str, tier: Literal["FREE", "PRO"]):
        db = self._get_db()
        user = crud.get_user_by_email(db, email)
        if user:
            user.subscription_tier = tier
            db.commit()
            if self.current_user and self.current_user["email"] == email:
                self.current_user["subscription_tier"] = tier
        db.close()

    @rx.event
    async def login(self, form_data: dict):
        email = form_data["email"]
        password = form_data["password"]
        db = self._get_db()
        user = crud.get_user_by_email(db, email)
        if user and security.verify_password(password, user.hashed_password):
            if not user.email_verified:
                self.login_error = "Please verify your email address. Check your inbox."
                db.close()
                return await self._send_verification_email_async(user)
            self.is_logged_in = True
            self.current_user = User(
                username=user.username,
                email=user.email,
                subscription_tier=user.subscription_tier,
                email_verified=user.email_verified,
            )
            self.login_error = ""
            db.close()
            return rx.redirect("/")
        else:
            self.login_error = "Invalid email or password."
            self.is_logged_in = False
            self.current_user = None
            db.close()

    @rx.event
    async def register(self, form_data: dict):
        email = form_data["email"]
        password = form_data["password"]
        username = form_data["username"]
        if not self._validate_password(password):
            return
        db = self._get_db()
        if crud.get_user_by_email(db, email):
            self.login_error = "User with this email already exists."
            db.close()
            return
        new_user = crud.create_user(db, username, email, password)
        db.close()
        return await self._send_verification_email_async(new_user)

    @rx.event
    def logout(self):
        self.is_logged_in = False
        self.current_user = None
        return (rx.clear_local_storage(), rx.redirect("/login"))

    @rx.event
    def check_login(self):
        if not self.is_logged_in:
            return rx.redirect("/login")

    @rx.event
    async def on_load(self):
        self.check_login()
        from app.states.exchange_state import ExchangeState

        exchange_state = await self.get_state(ExchangeState)
        return exchange_state.connect_binance_on_load

    @rx.event
    def verify_email(self):
        token = self.router.page.params.get("token", "")
        if not token:
            self.login_error = "Invalid verification link."
            return rx.redirect("/login")
        db = self._get_db()
        user = crud.get_user_by_verification_token(db, token)
        if not user:
            self.login_error = "Invalid or expired verification link."
            db.close()
            return rx.redirect("/login")
        if user.email_verified:
            db.close()
            return (
                rx.toast.info("Email already verified. Please log in."),
                rx.redirect("/login"),
            )
        from datetime import datetime

        if (
            user.verification_token_expires
            and user.verification_token_expires < datetime.utcnow()
        ):
            self.login_error = (
                "Verification link has expired. Please request a new one."
            )
            db.close()
            return rx.redirect("/login")
        user.email_verified = True
        user.verification_token = None
        user.verification_token_expires = None
        db.commit()
        db.close()
        return (
            rx.toast.success("Email verified successfully! You can now log in."),
            rx.redirect("/login"),
        )