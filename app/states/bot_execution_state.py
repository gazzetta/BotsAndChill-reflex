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
            balance_ok = await exchange_state.validate_balance(
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
            filled_price = float(order_result["fills"][0]["price"])
            filled_qty = float(order_result["executedQty"])
            base_order = Order(
                order_id=str(order_result["orderId"]),
                timestamp=order_result["transactTime"] / 1000,
                side="buy",
                price=filled_price,
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
                    message=f"A new deal has been started for pair {bot['config']['pair']}. Base order filled at {filled_price}.",
                )
        return True

    async def _check_bot_strategy(self, bot_id: str, current_price: float):
        async with self:
            deal_state = await self.get_state(DealState)
            deal = deal_state.get_active_deal(bot_id)
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
                bots_state.update_bot_stats(bot_id, realized_pnl, 1)
                bots_state.set_bot_status(bot_id, "stopped")
                logging.info(f"Deal for bot {bot_id} closed with PNL: {realized_pnl}")
                auth_state = await self.get_state(AuthState)
                if auth_state.current_user:
                    email_service = await self.get_state(EmailService)
                    email_service.send_bot_notification_email(
                        to_email=auth_state.current_user["email"],
                        bot_name=bot["name"],
                        message=f"Take profit target hit! Deal closed with a profit of {realized_pnl:.2f} USDT.",
                    )
                yield BotExecutionState.stop_bot_execution(bot_id)
            else:
                logging.error(
                    f"Take profit sell order failed for bot {bot_id}: {sell_order}"
                )
                bots_state.set_bot_status(bot_id, "error")

    async def _check_safety_orders(self, bot_id: str, deal: Deal, current_price: float):
        bots_state = await self.get_state(BotsState)
        bot = next((b for b in bots_state.bots if b["id"] == bot_id), None)
        if not bot:
            return
        config = bot["config"]
        num_safety_orders = len(deal["safety_orders"])
        if num_safety_orders >= config["max_safety_orders"]:
            return
        last_price = (
            deal["safety_orders"][-1]["price"]
            if deal["safety_orders"]
            else deal["base_order"]["price"]
        )
        price_deviation_needed = (
            config["price_deviation"]
            * config["safety_order_step_scale"] ** num_safety_orders
        )
        trigger_price = last_price * (1 - price_deviation_needed / 100)
        if current_price <= trigger_price:
            logging.info(
                f"Safety order condition met for bot {bot_id} at price {current_price}."
            )
            bots_state.set_bot_status(bot_id, "placing_order")
            exchange_state = await self.get_state(ExchangeState)
            safety_order_usdt = (
                config["safety_order_size"]
                * config["safety_order_volume_scale"] ** num_safety_orders
            )
            balance_ok = await exchange_state.validate_balance(
                "USDT", safety_order_usdt
            )
            if not balance_ok:
                logging.error(f"Insufficient balance for safety order on bot {bot_id}")
                bots_state.set_bot_status(bot_id, "monitoring")
                return
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
                deal_state = await self.get_state(DealState)
                deal_state.add_safety_order(bot_id, safety_order)
                bots_state.set_bot_status(bot_id, "in_position")
                logging.info(
                    f"Successfully placed safety order {num_safety_orders + 1} for bot {bot_id}."
                )
                auth_state = await self.get_state(AuthState)
                if auth_state.current_user:
                    email_service = await self.get_state(EmailService)
                    email_service.send_bot_notification_email(
                        to_email=auth_state.current_user["email"],
                        bot_name=bot["name"],
                        message=f"Safety order #{num_safety_orders + 1} filled for {bot['config']['pair']} at price {filled_price}.",
                    )
            else:
                logging.error(f"Safety order failed for bot {bot_id}: {so_result}")
                bots_state.set_bot_status(bot_id, "monitoring")