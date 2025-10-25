import reflex as rx
from app.states.auth_state import AuthState
from app.components.sidebar import sidebar
from app.components.app_bar import app_bar
from app.pages.login import login_page
from app.pages.register import register_page
from app.pages.dashboard import dashboard_page
from app.pages.placeholder_pages import bots_page
from app.pages.subscription import subscription_page
from app.pages.settings import settings_page
from app.pages.analytics_page import analytics_page
from app.pages.bot_detail_page import bot_detail_page
from app.pages.forgot_password import forgot_password_page
from app.pages.reset_password import reset_password_page
from app.api import api


def main_layout(child: rx.Component) -> rx.Component:
    return rx.el.div(
        sidebar(),
        rx.el.div(
            app_bar(),
            rx.el.main(child, class_name="p-8 bg-gray-50 flex-1"),
            class_name="flex-1 flex flex-col",
        ),
        class_name="flex h-screen bg-gray-50 font-['Roboto']",
    )


def index() -> rx.Component:
    return rx.cond(AuthState.is_logged_in, main_layout(dashboard_page()), login_page())


app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
from app.pages.verify_email_page import verify_email_page

app.add_page(index, route="/", on_load=AuthState.check_login)
app.add_page(login_page, route="/login")
app.add_page(register_page, route="/register")
app.add_page(forgot_password_page, route="/forgot-password")
app.add_page(reset_password_page, route="/reset-password/[token]")
app.add_page(
    verify_email_page, route="/verify-email/[token]", on_load=AuthState.verify_email
)
app.add_page(
    lambda: main_layout(bots_page()), route="/bots", on_load=AuthState.check_login
)
app.add_page(
    lambda: main_layout(bot_detail_page()),
    route="/bots/[bot_id]",
    on_load=AuthState.check_login,
)
app.add_page(
    lambda: main_layout(analytics_page()),
    route="/analytics",
    on_load=AuthState.check_login,
)
app.add_page(
    lambda: main_layout(settings_page()),
    route="/settings",
    on_load=AuthState.check_login,
)
from app.pages.subscription import subscription_page
from app.api import api as api_router

app.add_page(
    lambda: main_layout(subscription_page()),
    route="/subscription",
    on_load=AuthState.check_login,
)
app.api_router = api_router