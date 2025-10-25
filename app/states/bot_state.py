import reflex as rx
from typing import TypedDict, Literal, cast
import uuid
import logging
from app.states.auth_state import AuthState, User


class BotConfig(TypedDict):
    pair: str
    base_order_size: float
    safety_order_size: float
    safety_order_volume_scale: float
    safety_order_step_scale: float
    max_safety_orders: int
    immediate_safety_orders: int
    price_deviation: float
    take_profit_percentage: float


BotStatus = Literal[
    "active",
    "paused",
    "stopped",
    "starting",
    "monitoring",
    "placing_order",
    "in_position",
    "closing",
    "waiting_for_balance",
    "error",
]


class Bot(TypedDict):
    id: str
    name: str
    status: BotStatus
    in_deal: bool
    config: BotConfig
    total_pnl: float
    deals_count: int


class BotsState(rx.State):
    bots: list[Bot] = []
    selected_bot: Bot | None = None
    show_create_wizard: bool = False
    show_upgrade_dialog: bool = False
    current_bot_config: BotConfig = {
        "pair": "BTCUSDT",
        "base_order_size": 10.0,
        "safety_order_size": 10.0,
        "safety_order_volume_scale": 1.5,
        "safety_order_step_scale": 1.2,
        "max_safety_orders": 5,
        "immediate_safety_orders": 1,
        "price_deviation": 1.0,
        "take_profit_percentage": 2.0,
    }

    @rx.event
    def get_bot_by_id(self):
        bot_id = self.router.page.params.get("bot_id", None)
        if bot_id:
            self.selected_bot = next((b for b in self.bots if b["id"] == bot_id), None)
        else:
            self.selected_bot = None

    @rx.event
    def open_create_wizard(self):
        self.show_create_wizard = True

    @rx.event
    def close_create_wizard(self):
        self.show_create_wizard = False

    @rx.event
    def update_bot_config_pair(self, value: str):
        self.current_bot_config["pair"] = value

    @rx.event
    def update_bot_config_field(self, name: str, value: str):
        if name in self.current_bot_config:
            try:
                if name == "max_safety_orders":
                    self.current_bot_config[name] = int(value)
                else:
                    self.current_bot_config[name] = float(value)
            except (ValueError, TypeError) as e:
                logging.exception(
                    f"Could not convert '{value}' for config field '{name}': {e}"
                )

    @rx.var
    def required_balance(self) -> float:
        config = self.current_bot_config
        base_order_cost = config["base_order_size"]
        safety_orders_cost = sum(
            (
                config["safety_order_size"] * config["safety_order_volume_scale"] ** i
                for i in range(config["immediate_safety_orders"])
            )
        )
        return base_order_cost + safety_orders_cost

    @rx.event
    async def add_bot(self):
        from app.states.exchange_state import ExchangeState

        auth_state = await self.get_state(AuthState)
        user = cast(User, auth_state.current_user)
        if not user:
            return rx.toast.error("You must be logged in to create a bot.")
        if user["subscription_tier"] == "FREE" and len(self.bots) >= 1:
            self.show_upgrade_dialog = True
            return
        if user["subscription_tier"] == "PRO" and len(self.bots) >= 5:
            return rx.toast.info(
                "You have reached the maximum bot limit for your PRO plan."
            )
        exchange_state = await self.get_state(ExchangeState)
        balance_ok, current_balance = await exchange_state.validate_balance(
            "USDT", self.required_balance
        )
        if not balance_ok:
            return rx.toast.error(
                f"Insufficient balance. Need {self.required_balance:.2f} USDT, have {current_balance:.2f} USDT.",
                duration=5000,
            )
        new_bot_id = str(uuid.uuid4())
        new_bot = Bot(
            id=new_bot_id,
            name=f"DCA Bot {len(self.bots) + 1}",
            status="stopped",
            in_deal=False,
            config=self.current_bot_config.copy(),
            total_pnl=0.0,
            deals_count=0,
        )
        self.bots.append(new_bot)
        self.show_create_wizard = False
        from app.services.email_service import EmailService

        if user:
            email_service = await self.get_state(EmailService)
            email_service.send_bot_notification_email(
                to_email=user["email"],
                bot_name=new_bot["name"],
                message=f"Your new DCA bot for {new_bot['config']['pair']} has been created successfully!",
            )

    @rx.event
    def remove_bot(self, bot_id: str):
        self.bots = [bot for bot in self.bots if bot["id"] != bot_id]

    @rx.event
    def remove_bot_and_redirect(self, bot_id: str):
        self.remove_bot(bot_id)
        return rx.redirect("/bots")

    @rx.event
    def start_bot(self, bot_id: str):
        from app.states.bot_execution_state import BotExecutionState

        for i, bot in enumerate(self.bots):
            if bot["id"] == bot_id:
                self.bots[i]["status"] = "starting"
                break
        return BotExecutionState.start_bot_execution(bot_id)

    @rx.event
    def set_bot_status(self, bot_id: str, status: str):
        for i, bot in enumerate(self.bots):
            if bot["id"] == bot_id:
                self.bots[i]["status"] = cast(BotStatus, status)
                break

    @rx.event
    def update_bot_stats(self, bot_id: str, pnl_delta: float, deals_increment: int):
        for i, bot in enumerate(self.bots):
            if bot["id"] == bot_id:
                self.bots[i]["total_pnl"] += pnl_delta
                self.bots[i]["deals_count"] += deals_increment
                break

    @rx.event
    def pause_bot(self, bot_id: str):
        self.set_bot_status(bot_id, "paused")
        return BotsState.stop_bot(bot_id)

    @rx.event
    def stop_bot(self, bot_id: str):
        from app.states.bot_execution_state import BotExecutionState

        self.set_bot_status(bot_id, "stopped")
        return BotExecutionState.stop_bot_execution(bot_id)