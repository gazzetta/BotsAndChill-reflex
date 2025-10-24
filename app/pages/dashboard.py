import reflex as rx
from app.states.auth_state import AuthState
from app.states.dashboard_state import DashboardState
from app.components.dashboard.overview_card import overview_card


def dashboard_page() -> rx.Component:
    return rx.el.div(
        rx.el.h1("Dashboard", class_name="text-3xl font-bold text-gray-800 mb-6"),
        rx.el.div(
            overview_card(
                icon="bot",
                title="Total Bots",
                value=DashboardState.total_bots.to_string(),
                color="text-teal-600",
            ),
            overview_card(
                icon="play-circle",
                title="Active Bots",
                value=DashboardState.active_bots.to_string(),
                color="text-green-600",
            ),
            overview_card(
                icon="trending-up",
                title="Total P/L",
                value=f"${DashboardState.total_pnl.to_string()}",
                color="text-blue-600",
            ),
            overview_card(
                icon="wallet",
                title="Account Balance",
                value=f"${DashboardState.account_balance.to_string()}",
                color="text-purple-600",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6",
        ),
        on_mount=AuthState.check_login,
    )