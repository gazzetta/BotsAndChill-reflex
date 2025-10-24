import reflex as rx
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.states.exchange_state import ExchangeState


class DashboardState(rx.State):
    total_bots: int = 0
    active_bots: int = 0
    total_pnl: float = 0.0
    account_balance: float = 0.0

    @rx.var
    def display_balance(self) -> str:
        return f"{self.account_balance:.2f}"