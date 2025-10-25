import reflex as rx
from typing import TypedDict, Literal
import time

OrderType = Literal["base", "safety", "take_profit"]
OrderStatus = Literal["new", "filled", "partial", "canceled", "error"]
DealStatus = Literal["active", "completed", "canceled"]


class Order(TypedDict):
    order_id: str
    timestamp: float
    side: Literal["buy", "sell"]
    price: float
    quantity: float
    order_type: OrderType
    status: OrderStatus


class Deal(TypedDict):
    deal_id: str
    bot_id: str
    status: DealStatus
    entry_time: float
    close_time: float | None
    base_order: Order
    filled_safety_orders: list[Order]
    pending_safety_orders: list[Order]
    take_profit_order: Order | None
    average_entry_price: float
    total_quantity: float
    unrealized_pnl: float
    realized_pnl: float


class DealState(rx.State):
    deals: dict[str, Deal] = {}
    active_deal: Deal | None = None
    bot_deals: list[Deal] = []

    @rx.event
    def get_deals_for_bot(self):
        bot_id = self.router.page.params.get("bot_id", None)
        if bot_id:
            self.bot_deals = sorted(
                [d for d in self.deals.values() if d["bot_id"] == bot_id],
                key=lambda d: d["entry_time"],
                reverse=True,
            )
            self.active_deal = next(
                (d for d in self.bot_deals if d["status"] == "active"), None
            )

    @rx.event
    def get_active_deal_for_bot_id(self, bot_id: str) -> Deal | None:
        return self.deals.get(bot_id)

    def _calculate_average_entry(self, deal: Deal) -> tuple[float, float]:
        all_orders = [deal["base_order"]] + deal["filled_safety_orders"]
        total_cost = sum((o["price"] * o["quantity"] for o in all_orders))
        total_quantity = sum((o["quantity"] for o in all_orders))
        if total_quantity == 0:
            return (0.0, 0.0)
        return (total_cost / total_quantity, total_quantity)

    @rx.event
    def create_deal(self, bot_id: str, base_order: Order):
        deal_id = f"deal_{bot_id}_{int(time.time())}"
        new_deal = Deal(
            deal_id=deal_id,
            bot_id=bot_id,
            status="active",
            entry_time=base_order["timestamp"],
            close_time=None,
            base_order=base_order,
            filled_safety_orders=[],
            pending_safety_orders=[],
            take_profit_order=None,
            average_entry_price=base_order["price"],
            total_quantity=base_order["quantity"],
            unrealized_pnl=0.0,
            realized_pnl=0.0,
        )
        self.deals[bot_id] = new_deal

    @rx.event
    def add_pending_safety_order(self, bot_id: str, safety_order: Order):
        if bot_id not in self.deals or self.deals[bot_id]["status"] != "active":
            return
        self.deals[bot_id]["pending_safety_orders"].append(safety_order)

    @rx.event
    def safety_order_filled(
        self, bot_id: str, filled_order_id: str, fill_price: float, fill_qty: float
    ):
        if bot_id not in self.deals or self.deals[bot_id]["status"] != "active":
            return
        deal = self.deals[bot_id]
        order_to_move = None
        for i, order in enumerate(deal["pending_safety_orders"]):
            if order["order_id"] == filled_order_id:
                order_to_move = deal["pending_safety_orders"].pop(i)
                break
        if order_to_move:
            order_to_move["status"] = "filled"
            order_to_move["price"] = fill_price
            order_to_move["quantity"] = fill_qty
            deal["filled_safety_orders"].append(order_to_move)
            avg_price, total_quantity = self._calculate_average_entry(deal)
            deal["average_entry_price"] = avg_price
            deal["total_quantity"] = total_quantity
            self.deals[bot_id] = deal

    @rx.event
    def update_unrealized_pnl(self, bot_id: str, current_price: float):
        if bot_id not in self.deals:
            return
        deal = self.deals[bot_id]
        pnl = (current_price - deal["average_entry_price"]) * deal["total_quantity"]
        deal["unrealized_pnl"] = pnl
        self.deals[bot_id] = deal

    @rx.event
    def set_take_profit_order(self, bot_id: str, take_profit_order: Order):
        if bot_id not in self.deals:
            return
        self.deals[bot_id]["take_profit_order"] = take_profit_order

    @rx.event
    def close_deal(self, bot_id: str, realized_pnl: float):
        if bot_id not in self.deals:
            return
        deal = self.deals[bot_id]
        deal["status"] = "completed"
        deal["realized_pnl"] = realized_pnl
        deal["close_time"] = time.time()
        self.deals[bot_id] = deal