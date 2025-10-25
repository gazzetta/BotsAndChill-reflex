import reflex as rx
import json
import logging
import os
from typing import TypedDict
from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance import AsyncClient
import asyncio
import re


class APIKeys(TypedDict):
    api_key: str
    secret_key: str


class WalletBalance(TypedDict):
    asset: str
    free: str
    locked: str


class ExchangeState(rx.State):
    api_keys: APIKeys = {"api_key": "", "secret_key": ""}
    has_api_keys: bool = False
    account_balance: list[WalletBalance] = []
    trading_pairs: list[str] = []
    show_secret_key: bool = False
    last_balance_refresh: str = ""

    @rx.var
    def is_testnet(self) -> bool:
        return os.environ.get("BINANCE_TESTNET", "false").lower() == "true"

    @rx.var
    def obfuscated_secret_key(self) -> str:
        secret = self.api_keys.get("secret_key", "")
        if len(secret) > 8:
            return f"{secret[:4]}...{secret[-4:]}"
        return ""

    @rx.event
    def toggle_show_secret_key(self):
        self.show_secret_key = not self.show_secret_key

    @rx.var
    async def filtered_trading_pairs(self) -> list[str]:
        from app.states.bot_state import BotsState

        bots_state = await self.get_state(BotsState)
        search_term = bots_state.pair_search_term.upper()
        stablecoin_pattern = re.compile(".*USDT$|.*USDC$|.*FDUSD$|.*TUSD$")
        stable_pairs = [p for p in self.trading_pairs if stablecoin_pattern.match(p)]
        if not search_term:
            return stable_pairs[:100]
        return [p for p in stable_pairs if search_term in p.upper()][:100]

    @rx.event(background=True)
    async def save_api_keys(self, form_data: dict):
        api_key = form_data.get("api_key", "").strip()
        secret_key = form_data.get("secret_key", "").strip()
        if not api_key or not secret_key:
            yield rx.toast.error("API Key and Secret Key cannot be empty.")
            return
        is_testnet_mode = self.is_testnet
        logging.info(
            f"Attempting to validate keys with Binance. Testnet: {is_testnet_mode}"
        )
        try:
            client = Client(api_key, secret_key, testnet=is_testnet_mode)
            if is_testnet_mode:
                client.API_URL = client.API_TESTNET_URL
            client.get_account()
        except BinanceAPIException as e:
            logging.exception(f"Binance API Error during key validation: {e}")
            async with self:
                self.has_api_keys = False
                self.api_keys = {"api_key": "", "secret_key": ""}
            yield rx.toast.error(
                f"Key Validation Failed: {e.message}. Check permissions and environment (Live vs Testnet).",
                duration=7000,
            )
            return
        except Exception as e:
            logging.exception(f"Unexpected error during key validation: {e}")
            async with self:
                self.has_api_keys = False
                self.api_keys = {"api_key": "", "secret_key": ""}
            yield rx.toast.error(f"An unexpected error occurred: {e}")
            return
        async with self:
            from app.database import crud
            from app.states.auth_state import AuthState

            auth_state = await self.get_state(AuthState)
            if not auth_state.current_user:
                yield rx.toast.error("User not logged in.")
                return
            db = self.get_db()
            try:
                user = crud.get_user_by_email(db, auth_state.current_user["email"])
                if user:
                    crud.update_user_api_keys(
                        db, user.id, api_key=api_key, secret_key=secret_key
                    )
                    self.api_keys = {"api_key": api_key, "secret_key": secret_key}
                    self.has_api_keys = True
                else:
                    yield rx.toast.error("Could not find user to save keys.")
                    return
            finally:
                db.close()
        yield rx.toast.success("API Keys saved and validated successfully!")
        yield ExchangeState.refresh_balances
        yield ExchangeState.fetch_trading_pairs

    @rx.event
    def get_db(self):
        from app.database.database import SessionLocal

        return SessionLocal()

    @rx.event(background=True)
    async def refresh_balances(self):
        if not self.has_api_keys:
            return rx.toast.info("Please save your API keys first.")
        try:
            client = Client(
                self.api_keys["api_key"],
                self.api_keys["secret_key"],
                testnet=self.is_testnet,
            )
            account_info = client.get_account()
            async with self:
                balances = [
                    WalletBalance(**bal)
                    for bal in account_info.get("balances", [])
                    if float(bal.get("free", 0)) > 0 or float(bal.get("locked", 0)) > 0
                ]
                self.account_balance = balances
                from datetime import datetime

                self.last_balance_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return rx.toast.success("Balances refreshed successfully.")
        except Exception as e:
            logging.exception(f"Error refreshing balances: {e}")
            async with self:
                self.account_balance = []
            return rx.toast.error("Failed to refresh balances.")

    @rx.event(background=True)
    async def fetch_trading_pairs(self):
        if not self.has_api_keys:
            return
        try:
            client = Client(
                self.api_keys["api_key"],
                self.api_keys["secret_key"],
                testnet=self.is_testnet,
            )
            exchange_info = client.get_exchange_info()
            pairs = [
                s["symbol"]
                for s in exchange_info["symbols"]
                if s["status"] == "TRADING" and "SPOT" in s["permissions"]
            ]
            async with self:
                self.trading_pairs = sorted(pairs)
        except Exception as e:
            logging.exception(f"Error fetching trading pairs: {e}")

    @rx.event(background=True)
    async def connect_binance_on_load(self):
        from app.database import crud
        from app.states.auth_state import AuthState

        async with self:
            auth_state = await self.get_state(AuthState)
            if not auth_state.current_user:
                return
        db = self.get_db()
        try:
            user = crud.get_user_by_email(db, auth_state.current_user["email"])
            if user and user.encrypted_api_key:
                keys = crud.get_user_api_keys(db, user.id)
                if keys and keys.get("api_key") and keys.get("secret_key"):
                    async with self:
                        self.api_keys = keys
                        self.has_api_keys = True
                    yield ExchangeState.refresh_balances
                    yield ExchangeState.fetch_trading_pairs
                else:
                    async with self:
                        self.has_api_keys = False
        finally:
            db.close()

    @rx.event(background=True)
    async def clear_api_keys(self):
        async with self:
            from app.database import crud
            from app.states.auth_state import AuthState

            self.api_keys = {"api_key": "", "secret_key": ""}
            self.has_api_keys = False
            self.account_balance = []
            self.trading_pairs = []
            self.last_balance_refresh = ""
            auth_state = await self.get_state(AuthState)
            if auth_state.current_user:
                db = self.get_db()
                try:
                    user = crud.get_user_by_email(db, auth_state.current_user["email"])
                    if user:
                        crud.update_user_api_keys(db, user.id, "", "")
                finally:
                    db.close()
        return rx.toast.info("API Keys cleared.")

    async def _get_async_client(self) -> AsyncClient | None:
        api_key = self.api_keys["api_key"]
        secret_key = self.api_keys["secret_key"]
        if not self.has_api_keys or not api_key or (not secret_key):
            logging.error("Cannot create async client, API keys not set or validated.")
            return None
        try:
            is_testnet_mode = (
                os.environ.get("BINANCE_TESTNET", "false").lower() == "true"
            )
            client = await AsyncClient.create(
                api_key, secret_key, testnet=is_testnet_mode
            )
            if is_testnet_mode and hasattr(client, "API_TESTNET_URL"):
                client.API_URL = client.API_TESTNET_URL
            return client
        except Exception as e:
            logging.exception(f"Failed to create async client: {e}")
            return None

    @rx.event
    async def place_market_order(
        self, pair: str, side: str, quantity: float
    ) -> dict | None:
        client = await self._get_async_client()
        if not client:
            return None
        try:
            logging.info(f"Placing market {side} order for {quantity} of {pair}")
            order = await client.create_order(
                symbol=pair, side=side.upper(), type="MARKET", quantity=quantity
            )
            logging.info(f"Order successful: {order}")
            return order
        except BinanceAPIException as e:
            logging.exception(f"Binance API error placing market order: {e}")
            return None
        except Exception as e:
            logging.exception(f"Unexpected error placing market order: {e}")
            return None
        finally:
            if client:
                await client.close_connection()

    @rx.event
    async def place_limit_order(
        self, pair: str, side: str, quantity: float, price: float
    ) -> dict | None:
        client = await self._get_async_client()
        if not client:
            return None
        try:
            logging.info(
                f"Placing limit {side} order for {quantity} of {pair} at price {price}"
            )
            order = await client.create_order(
                symbol=pair,
                side=side.upper(),
                type="LIMIT",
                timeInForce="GTC",
                quantity=quantity,
                price=f"{price:.8f}",
            )
            logging.info(f"Limit order successful: {order}")
            return order
        except BinanceAPIException as e:
            logging.exception(f"Binance API error placing limit order: {e}")
            return None
        except Exception as e:
            logging.exception(f"Unexpected error placing limit order: {e}")
            return None
        finally:
            if client:
                await client.close_connection()

    @rx.event
    async def validate_balance(
        self, asset: str, required_amount: float
    ) -> tuple[bool, float]:
        client = await self._get_async_client()
        if not client:
            return (False, 0.0)
        available_balance = 0.0
        try:
            balance = await client.get_asset_balance(asset=asset)
            if balance:
                available_balance = float(balance["free"])
            if available_balance >= required_amount:
                return (True, available_balance)
            logging.warning(
                f"Insufficient balance for {asset}. Required: {required_amount}, Available: {available_balance}"
            )
            return (False, available_balance)
        except Exception as e:
            logging.exception(f"Error validating balance for {asset}: {e}")
            return (False, available_balance)
        finally:
            if client:
                await client.close_connection()