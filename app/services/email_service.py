import reflex as rx
import os
import logging


class EmailService(rx.State):
    @rx.var
    def resend_api_key(self) -> str:
        return os.environ.get("RESEND_API_KEY", "")

    def _send_email(self, to_email: str, subject: str, html_body: str):
        if not self.resend_api_key:
            logging.error("RESEND_API_KEY not set. Cannot send email.")
            return
        try:
            logging.info(f"Would send email to {to_email}")
            logging.info(f"Subject: {subject}")
            logging.info(f"Body: {html_body}")
            logging.info("Email service simulated successfully")
        except Exception as e:
            logging.exception(f"Failed to send email to {to_email}: {e}")

    @rx.event
    def send_verification_email(self, to_email: str, verification_link: str):
        subject = "Verify Your Email Address"
        html_body = f"<p>Welcome! Please verify your email by clicking the link below:</p>\n<p><a href='{verification_link}'>Verify Email</a></p>\n<p>This link will expire in 24 hours.</p>"
        self._send_email(to_email, subject, html_body)

    @rx.event
    def send_password_reset_email(self, to_email: str, reset_link: str):
        subject = "Password Reset Request"
        html_body = f"<p>You requested a password reset. Click the link below to reset your password:</p>\n<p><a href='{reset_link}'>Reset Password</a></p>\n<p>This link will expire in 1 hour.</p>"
        self._send_email(to_email, subject, html_body)

    @rx.event
    def send_bot_notification_email(self, to_email: str, bot_name: str, message: str):
        subject = f"Bot Notification: {bot_name}"
        html_body = f"<p>Notification for your bot '{bot_name}':</p>\n<p>{message}</p>"
        self._send_email(to_email, subject, html_body)