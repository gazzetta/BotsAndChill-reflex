import reflex as rx
import os
import logging
import resend


class EmailService(rx.State):
    def _send_email(self, to_email: str, subject: str, html_body: str):
        api_key = os.environ.get("RESEND_API_KEY")
        if not api_key:
            logging.error("RESEND_API_KEY not set. Cannot send email.")
            logging.info(f"Email intended for {to_email} with subject '{subject}'")
            return
        resend.api_key = api_key
        from_address = os.environ.get("EMAIL_FROM_ADDRESS", "onboarding@resend.dev")
        params = {
            "from": from_address,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }
        try:
            email = resend.Emails.send(params)
            logging.info(f"Email sent successfully to {to_email}: {email}")
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