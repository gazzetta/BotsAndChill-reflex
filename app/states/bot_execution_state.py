import reflex as rx
import asyncio
import logging
from typing import cast
from binance import AsyncClient, BinanceSocketManager
from app.states.bot_state import BotsState, Bot
from app.states.exchange_state import ExchangeState
from app.states.deal_state import DealState, Order, OrderStatus, Deal
from contextlib import AsyncExitStack
from app.services.email_service import EmailService
from app.states.auth_state import AuthState


class BotExecutionState(rx.State):
    active_sockets: dict[str, AsyncExitStack] = {}
    bot_prices: dict[str, float] = {}
    order_monitoring_task: asyncio.Task | None = None

    @rx.event(background=True)
    async def poll_balances_for_pending_orders(self):
        while True:
            bots_to_check = []
            async with self:
                bots_state = await self.get_state(BotsState)
                bots_to_check = [
                    bot
                    for bot in bots_state.bots
                    if bot["status"] == "waiting_for_balance"
                ]
            if bots_to_check:
                logging.info(
                    f"Polling balances for {len(bots_to_check)} bots waiting for funds."
                )
                for bot in bots_to_check:
                    await self._check_safety_orders(
                        bot["id"], self.bot_prices.get(bot["id"], 0.0), is_retry=True
                    )
            await asyncio.sleep(60)

    @rx.event(background=True)
    async def start_bot_execution(self, bot_id: str):
        async with self:
            bots_state = await self.get_state(BotsState)
            bot = next((b for b in bots_state.bots if b["id"] == bot_id), None)
            if not bot:
                logging.error(f"Bot {bot_id} not found to start execution.")
                return
            exchange_state = await self.get_state(ExchangeState)
            if not exchange_state.is_connected:
                logging.error(f"Cannot start bot {bot_id}, Binance not connected.")
                bots_state = await self.get_state(BotsState)
                bots_state.set_bot_status(bot_id, "error")
                return
            client = await AsyncClient.create(
                exchange_state.api_keys["api_key"],
                exchange_state.api_keys["secret_key"],
            )
            bsm = BinanceSocketManager(client)
            trade_socket = bsm.trade_socket(bot["config"]["pair"])
            self.active_sockets[bot_id] = trade_socket
            bots_state = await self.get_state(BotsState)
            bots_state.set_bot_status(bot_id, "starting")
            base_order_placed = await self._place_base_order(bot_id)
            if not base_order_placed:
                logging.error(f"Failed to place base order for bot {bot_id}. Halting.")
                async with self:
                    bots_state = await self.get_state(BotsState)
                    bots_state.set_bot_status(bot_id, "error")
                return
            async with self:
                bots_state = await self.get_state(BotsState)
                bots_state.set_bot_status(bot_id, "monitoring")
            if not self.order_monitoring_task or self.order_monitoring_task.done():
                task = asyncio.create_task(self._monitor_open_orders())
                async with self:
                    self.order_monitoring_task = task
            if not self.active_sockets:
                yield BotExecutionState.poll_balances_for_pending_orders
        logging.info(
            f"Starting trade socket for bot {bot_id} on pair {bot['config']['pair']}"
        )
        try:
            async with trade_socket as ts:
                while True:
                    if bot_id not in self.active_sockets:
                        logging.info(
                            f"Socket for bot {bot_id} closed, exiting listener."
                        )
                        break
                    res = await ts.recv()
                    if res and res.get("e") == "error":
                        logging.error(
                            f"WebSocket error for bot {bot_id}: {res.get('m')}"
                        )
                        async with self:
                            bots_state = await self.get_state(BotsState)
                            bots_state.set_bot_status(bot_id, "error")
                        break
                    if res and "p" in res:
                        price = float(res["p"])
                        async with self:
                            self.bot_prices[bot_id] = price
                        await self._check_bot_strategy(bot_id, price)
                    await asyncio.sleep(0.1)
        except Exception as e:
            logging.exception(f"Exception in trade socket for bot {bot_id}: {e}")
            async with self:
                bots_state = await self.get_state(BotsState)
                bots_state.set_bot_status(bot_id, "error")
        finally:
            logging.info(f"Closing connection for bot {bot_id}")
            await client.close_connection()
            async with self:
                if bot_id in self.active_sockets:
                    del self.active_sockets[bot_id]

    @rx.event(background=True)
    async def stop_bot_execution(self, bot_id: str):
        async with self:
            if bot_id in self.active_sockets:
                del self.active_sockets[bot_id]
            if bot_id in self.bot_prices:
                del self.bot_prices[bot_id]
        logging.info(f"Stopped execution and cleaned up for bot {bot_id}.")

    async def _place_base_order(self, bot_id: str) -> bool:
        async with self:
            bots_state = await self.get_state(BotsState)
            bot = next((b for b in bots_state.bots if b["id"] == bot_id), None)
            if not bot:
                return False
            exchange_state = await self.get_state(ExchangeState)
            pair_info = bot["config"]["pair"]
            base_currency = "USDT"
            required_usdt = bot["config"]["base_order_size"]
            balance_ok, _ = await exchange_state.validate_balance(
                base_currency, required_usdt
            )
            if not balance_ok:
                bots_state.set_bot_status(bot_id, "error")
                logging.error(f"Bot {bot_id} has insufficient USDT for base order.")
                return False
            order_result = await exchange_state.place_market_order(
                pair=pair_info, side="BUY", quantity=required_usdt
            )
            if not order_result or order_result["status"] != "FILLED":
                bots_state.set_bot_status(bot_id, "error")
                logging.error(f"Base order failed for bot {bot_id}: {order_result}")
                return False
            base_order_price = float(order_result["fills"][0]["price"])
            filled_qty = float(order_result["executedQty"])
            base_order = Order(
                order_id=str(order_result["orderId"]),
                timestamp=order_result["transactTime"] / 1000,
                side="buy",
                price=base_order_price,
                quantity=filled_qty,
                order_type="base",
                status="filled",
            )
            deal_state = await self.get_state(DealState)
            deal_state.create_deal(bot_id, base_order)
            bots_state.set_bot_status(bot_id, "in_position")
            logging.info(
                f"Successfully placed base order and created deal for bot {bot_id}"
            )
            auth_state = await self.get_state(AuthState)
            if auth_state.current_user:
                email_service = await self.get_state(EmailService)
                email_service.send_bot_notification_email(
                    to_email=auth_state.current_user["email"],
                    bot_name=bot["name"],
                    message=f"A new deal has been started for pair {bot['config']['pair']}. Base order filled at {base_order_price}.",
                )
            config = bot["config"]
            for i in range(config["immediate_safety_orders"]):
                deviation = (
                    config["price_deviation"] * config["safety_order_step_scale"] ** i
                )
                limit_price = base_order_price * (1 - deviation / 100)
                so_quantity_usdt = (
                    config["safety_order_size"]
                    * config["safety_order_volume_scale"] ** i
                )
                so_quantity_asset = so_quantity_usdt / limit_price
                so_result = await exchange_state.place_limit_order(
                    pair=config["pair"],
                    side="BUY",
                    quantity=so_quantity_asset,
                    price=limit_price,
                )
                if not so_result:
                    bots_state.set_bot_status(bot_id, "error")
                    logging.error(
                        f"Failed to place immediate safety order #{i + 1} for bot {bot_id}"
                    )
                    return False
                safety_order = Order(
                    order_id=str(so_result["orderId"]),
                    timestamp=so_result["transactTime"] / 1000,
                    side="buy",
                    price=float(so_result["price"]),
                    quantity=float(so_result["origQty"]),
                    order_type="safety",
                    status="new",
                )
                deal_state.add_pending_safety_order(bot_id, safety_order)
                logging.info(
                    f"Successfully placed immediate safety order #{i + 1} for bot {bot_id} at price {limit_price}"
                )
        return True

    async def _check_bot_strategy(self, bot_id: str, current_price: float):
        async with self:
            bots_state = await self.get_state(BotsState)
            bot = next((b for b in bots_state.bots if b["id"] == bot_id), None)
            if not bot or bot["status"] in ["paused", "stopped", "error", "closing"]:
                return
            deal_state = await self.get_state(DealState)
            deal = deal_state.get_active_deal(bot_id)
            if bot["status"] == "waiting_for_balance":
                return
            if not deal or deal["status"] != "active":
                return
            deal_state.update_unrealized_pnl(bot_id, current_price)
            await self._check_take_profit(bot_id, deal, current_price)
            await self._check_safety_orders(bot_id, deal, current_price)

    async def _check_take_profit(self, bot_id: str, deal: Deal, current_price: float):
        bots_state = await self.get_state(BotsState)
        bot = next((b for b in bots_state.bots if b["id"] == bot_id), None)
        if not bot:
            return
        profit_target = bot["config"]["take_profit_percentage"]
        unrealized_pnl_percentage = (
            deal["unrealized_pnl"]
            / (deal["average_entry_price"] * deal["total_quantity"])
            * 100
        )
        if unrealized_pnl_percentage >= profit_target:
            logging.info(
                f"Take profit target hit for bot {bot_id}. Attempting to close deal."
            )
            bots_state.set_bot_status(bot_id, "closing")
            exchange_state = await self.get_state(ExchangeState)
            sell_order = await exchange_state.place_market_order(
                pair=bot["config"]["pair"], side="SELL", quantity=deal["total_quantity"]
            )
            if sell_order and sell_order["status"] == "FILLED":
                realized_pnl = (
                    float(sell_order["fills"][0]["price"]) - deal["average_entry_price"]
                ) * deal["total_quantity"]
                deal_state = await self.get_state(DealState)
                deal_state.close_deal(bot_id, realized_pnl)
                bots_state = await self.get_state(BotsState)
                bots_state.update_bot_stats(bot_id, realized_pnl, 1)
                logging.info(f"Deal for bot {bot_id} closed with PNL: {realized_pnl}")
                auth_state = await self.get_state(AuthState)
                if auth_state.current_user:
                    email_service = await self.get_state(EmailService)
                    email_service.send_bot_notification_email(
                        to_email=auth_state.current_user["email"],
                        bot_name=bot["name"],
                        message=f"Take profit target hit! Deal closed with a profit of {realized_pnl:.2f} USDT. Starting new cycle.",
                    )
                bots_state.set_bot_status(bot_id, "starting")
                base_order_placed = await self._place_base_order(bot_id)
                if not base_order_placed:
                    logging.error(f"Failed to restart bot {bot_id} after take profit.")
                    bots_state.set_bot_status(bot_id, "error")
                    yield BotExecutionState.stop_bot_execution(bot_id)
                else:
                    logging.info(
                        f"Bot {bot_id} successfully restarted for a new cycle."
                    )
                    bots_state.set_bot_status(bot_id, "monitoring")
            else:
                logging.error(
                    f"Take profit sell order failed for bot {bot_id}: {sell_order}"
                )
                bots_state.set_bot_status(bot_id, "error")

    async def _check_safety_orders(
        self, bot_id: str, deal_or_price: Deal | float, is_retry: bool = False
    ):
        bots_state = await self.get_state(BotsState)
        bot = next((b for b in bots_state.bots if b["id"] == bot_id), None)
        deal_state = await self.get_state(DealState)
        deal = (
            deal_state.get_active_deal(bot_id)
            if not is_retry
            else deal_state.deals.get(bot_id)
        )
        if not bot or not deal:
            return
        current_price = cast(float, deal_or_price)
        config = bot["config"]
        num_safety_orders = len(deal["safety_orders"])
        if num_safety_orders >= config["max_safety_orders"]:
            return
        price_should_trigger = False
        if not is_retry:
            cumulative_deviation = config["price_deviation"]
            for i in range(num_safety_orders):
                cumulative_deviation += config["price_deviation"] * config[
                    "safety_order_step_scale"
                ] ** (i + 1)
            trigger_price = deal["base_order"]["price"] * (
                1 - cumulative_deviation / 100
            )
            price_should_trigger = current_price <= trigger_price
        if price_should_trigger or is_retry:
            if not is_retry:
                logging.info(
                    f"Safety order condition met for bot {bot_id} at price {current_price}."
                )
                bots_state.set_bot_status(bot_id, "placing_order")
            exchange_state = await self.get_state(ExchangeState)
            safety_order_usdt = (
                config["safety_order_size"]
                * config["safety_order_volume_scale"] ** num_safety_orders
            )
            balance_ok, _ = await exchange_state.validate_balance(
                "USDT", safety_order_usdt
            )
            if not balance_ok:
                if bot["status"] != "waiting_for_balance":
                    logging.warning(
                        f"Insufficient balance for safety order on bot {bot_id}. Entering waiting state."
                    )
                    bots_state.set_bot_status(bot_id, "waiting_for_balance")
                    auth_state = await self.get_state(AuthState)
                    if auth_state.current_user:
                        email_service = await self.get_state(EmailService)
                        email_service.send_bot_notification_email(
                            to_email=auth_state.current_user["email"],
                            bot_name=bot["name"],
                            message=f"Your bot is paused due to insufficient USDT balance to place a safety order. It will resume automatically when funds are available.",
                        )
                else:
                    logging.info(f"Still waiting for balance for bot {bot_id}...")
                return
            if bot["status"] == "waiting_for_balance":
                logging.info(
                    f"Balance detected for bot {bot_id}. Retrying safety order."
                )
            so_result = await exchange_state.place_market_order(
                pair=config["pair"], side="BUY", quantity=safety_order_usdt
            )
            if so_result and so_result["status"] == "FILLED":
                filled_price = float(so_result["fills"][0]["price"])
                filled_qty = float(so_result["executedQty"])
                safety_order = Order(
                    order_id=str(so_result["orderId"]),
                    timestamp=so_result["transactTime"] / 1000,
                    side="buy",
                    price=filled_price,
                    quantity=filled_qty,
                    order_type="safety",
                    status="filled",
                )
                deal_state.add_pending_safety_order(bot_id, safety_order)
                bots_state.set_bot_status(bot_id, "in_position")
                logging.info(
                    f"Successfully placed safety order {num_safety_orders + 1} for bot {bot_id}."
                )
                auth_state = await self.get_state(AuthState)
                if auth_state.current_user:
                    email_service = await self.get_state(EmailService)
                    message = f"Safety order #{num_safety_orders + 1} placed for {bot['config']['pair']} at price {filled_price}."
                    email_service.send_bot_notification_email(
                        to_email=auth_state.current_user["email"],
                        bot_name=bot["name"],
                        message=message,
                    )
            else:
                logging.error(f"Safety order failed for bot {bot_id}: {so_result}")
                bots_state.set_bot_status(bot_id, "error")

    async def _monitor_open_orders(self):
        while True:
            await asyncio.sleep(5)
            async with self:
                bots_state = await self.get_state(BotsState)
                deal_state = await self.get_state(DealState)
                exchange_state = await self.get_state(ExchangeState)
                active_bots = [
                    b
                    for b in bots_state.bots
                    if b["status"] in ["monitoring", "in_position"]
                ]
                if not active_bots or not exchange_state.is_connected:
                    continue
                client = await exchange_state._get_async_client()
                if not client:
                    continue
            try:
                for bot in active_bots:
                    deal = deal_state.deals.get(bot["id"])
                    if (
                        not deal
                        or deal["status"] != "active"
                        or (not deal["pending_safety_orders"])
                    ):
                        continue
                    for so in list(deal["pending_safety_orders"]):
                        try:
                            order_status = await client.get_order(
                                symbol=bot["config"]["pair"], orderId=so["order_id"]
                            )
                            if order_status["status"] == "FILLED":
                                logging.info(
                                    f"Safety order {so['order_id']} for bot {bot['id']} has been filled."
                                )
                                async with self:
                                    deal_state = await self.get_state(DealState)
                                    deal_state.safety_order_filled(
                                        bot_id=bot["id"],
                                        filled_order_id=so["order_id"],
                                        fill_price=float(order_status["price"]),
                                        fill_qty=float(order_status["executedQty"]),
                                    )
                                    await self._place_next_safety_order(bot["id"])
                        except BinanceAPIException as e:
                            if e.code == -2013:
                                logging.warning(
                                    f"Order {so['order_id']} not found on exchange, likely canceled or expired. Removing from pending."
                                )
                                async with self:
                                    deal_state = await self.get_state(DealState)
                                    deal_state.deals[bot["id"]][
                                        "pending_safety_orders"
                                    ] = [
                                        pso
                                        for pso in deal_state.deals[bot["id"]][
                                            "pending_safety_orders"
                                        ]
                                        if pso["order_id"] != so["order_id"]
                                    ]
                            else:
                                logging.exception(
                                    f"Error checking order status for {so['order_id']}: {e}"
                                )
                        except Exception as e:
                            logging.exception(
                                f"Unexpected error checking order status for {so['order_id']}: {e}"
                            )
            finally:
                if client:
                    await client.close_connection()

    async def _place_next_safety_order(self, bot_id: str):
        async with self:
            bots_state = await self.get_state(BotsState)
            bot = next((b for b in bots_state.bots if b["id"] == bot_id), None)
            deal_state = await self.get_state(DealState)
            deal = deal_state.deals.get(bot_id)
            if not bot or not deal or deal["status"] != "active":
                return
            config = bot["config"]
            total_sos_placed = len(deal["filled_safety_orders"]) + len(
                deal["pending_safety_orders"]
            )
            if total_sos_placed >= config["max_safety_orders"]:
                logging.info(f"Max safety orders reached for bot {bot_id}")
                return
            last_price = deal["average_entry_price"]
            next_so_num = total_sos_placed
            deviation = (
                config["price_deviation"]
                * config["safety_order_step_scale"] ** next_so_num
            )
            limit_price = last_price * (1 - deviation / 100)
            so_quantity_usdt = (
                config["safety_order_size"]
                * config["safety_order_volume_scale"] ** next_so_num
            )
            so_quantity_asset = so_quantity_usdt / limit_price
            exchange_state = await self.get_state(ExchangeState)
            so_result = await exchange_state.place_limit_order(
                pair=config["pair"],
                side="BUY",
                quantity=so_quantity_asset,
                price=limit_price,
            )
            if so_result:
                safety_order = Order(
                    order_id=str(so_result["orderId"]),
                    timestamp=so_result["transactTime"] / 1000,
                    side="buy",
                    price=float(so_result["price"]),
                    quantity=float(so_result["origQty"]),
                    order_type="safety",
                    status="new",
                )
                deal_state.add_pending_safety_order(bot_id, safety_order)
                logging.info(
                    f"Placed rolling safety order #{next_so_num + 1} for bot {bot_id}."
                )
            else:
                logging.error(f"Failed to place rolling safety order for bot {bot_id}.")