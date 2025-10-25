import reflex as rx
import logging
from app.database import crud, security, models
from app.database.database import get_db
from sqlalchemy.orm import Session
from app.services.email_service import EmailService
from datetime import datetime


class ResetPasswordState(rx.State):
    message: str = ""
    error: bool = False
    is_loading: bool = False

    def _get_db(self) -> Session:
        return next(get_db())

    @rx.event(background=True)
    async def request_password_reset(self, form_data: dict):
        async with self:
            self.is_loading = True
            self.message = ""
            self.error = False
        try:
            email = form_data["email"]
            db = self._get_db()
            user = crud.get_user_by_email(db, email)
            if user:
                token = crud.create_password_reset_token(db, user)
                base_url = self.router.page.full_raw_url.replace("/forgot-password", "")
                reset_link = f"{base_url}/reset-password/{token}"
                async with self:
                    email_service = await self.get_state(EmailService)
                    email_service.send_password_reset_email(user.email, reset_link)
                async with self:
                    self.message = "If an account with that email exists, a password reset link has been sent."
            else:
                async with self:
                    self.message = "If an account with that email exists, a password reset link has been sent."
            db.close()
        except Exception as e:
            logging.exception(f"Error requesting password reset: {e}")
            async with self:
                self.message = "An error occurred. Please try again."
                self.error = True
        finally:
            async with self:
                self.is_loading = False

    @rx.event(background=True)
    async def on_load_verify_token(self):
        async with self:
            self.message = ""
            self.error = False
        token = self.router.page.params.get("token", "")
        if not token:
            async with self:
                self.message = "Invalid password reset link."
                self.error = True
            return
        db = self._get_db()
        user = crud.get_user_by_password_reset_token(db, token)
        if not user or user.password_reset_token_expires < datetime.utcnow():
            async with self:
                self.message = "Invalid or expired password reset link."
                self.error = True
        db.close()

    @rx.event(background=True)
    async def reset_password(self, form_data: dict):
        async with self:
            self.is_loading = True
            self.message = ""
            self.error = False
        try:
            token = self.router.page.params.get("token", "")
            password = form_data["password"]
            confirm_password = form_data["confirm_password"]
            if password != confirm_password:
                async with self:
                    self.message = "Passwords do not match."
                    self.error = True
                    self.is_loading = False
                return
            db = self._get_db()
            user = crud.get_user_by_password_reset_token(db, token)
            if not user or user.password_reset_token_expires < datetime.utcnow():
                async with self:
                    self.message = "Invalid or expired password reset link."
                    self.error = True
                db.close()
                return
            user.hashed_password = security.hash_password(password)
            user.password_reset_token = None
            user.password_reset_token_expires = None
            db.commit()
            db.close()
            async with self:
                self.message = (
                    "Password has been reset successfully. You can now log in."
                )
            return rx.redirect("/login")
        except Exception as e:
            logging.exception(f"Error resetting password: {e}")
            async with self:
                self.message = "An error occurred. Please try again."
                self.error = True
        finally:
            async with self:
                self.is_loading = False