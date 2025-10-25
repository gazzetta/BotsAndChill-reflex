import reflex as rx
import json
import logging
import os
from typing import TypedDict
from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance import AsyncClient
import asyncio


class APIKeys(TypedDict):
    api_key: str
    secret_key: str


class WalletBalance(TypedDict):
    asset: str
    free: str
    locked: str


class ExchangeState(rx.State):
    api_keys: APIKeys = {"api_key": "", "secret_key": ""}
    is_connected: bool = False
    connection_message: str = ""
    account_balance: list[WalletBalance] = []
    trading_pairs: list[str] = []
    show_secret_key: bool = False

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

    @rx.event(background=True)
    async def save_api_keys(self, form_data: dict):
        api_key = form_data.get("api_key", "").strip()
        secret_key = form_data.get("secret_key", "").strip()
        if not api_key or not secret_key:
            async with self:
                self.connection_message = "API Key and Secret Key cannot be empty."
                self.is_connected = False
            return
        try:
            client = Client(api_key, secret_key, testnet=self.is_testnet)
            client.get_account()
        except BinanceAPIException as e:
            logging.exception(f"Binance API Error during key validation: {e}")
            async with self:
                self.is_connected = False
                self.connection_message = f"Connection failed: {e.message}"
                self.api_keys = {"api_key": "", "secret_key": ""}
            return
        except Exception as e:
            logging.exception(f"Unexpected error during key validation: {e}")
            async with self:
                self.is_connected = False
                self.connection_message = f"An unexpected error occurred: {e}"
                self.api_keys = {"api_key": "", "secret_key": ""}
            return
        async with self:
            from app.database import crud
            from app.states.auth_state import AuthState

            auth_state = await self.get_state(AuthState)
            if not auth_state.current_user:
                self.connection_message = "User not logged in."
                return
            db = self.get_db()
            try:
                user = crud.get_user_by_email(db, auth_state.current_user["email"])
                if user:
                    crud.update_user_api_keys(
                        db, user.id, api_key=api_key, secret_key=secret_key
                    )
                    self.api_keys = {"api_key": api_key, "secret_key": secret_key}
                    self.is_connected = True
                    self.connection_message = (
                        "Successfully connected and saved API keys."
                    )
                    account_info = client.get_account()
                    balances = [
                        WalletBalance(**bal)
                        for bal in account_info.get("balances", [])
                        if float(bal.get("free", 0)) > 0
                        or float(bal.get("locked", 0)) > 0
                    ]
                    self.account_balance = balances
                else:
                    self.connection_message = "Could not find user to save keys."
            finally:
                db.close()
        yield ExchangeState.fetch_trading_pairs

    @rx.event
    def get_db(self):
        from app.database.database import SessionLocal

        return SessionLocal()

    @rx.event(background=True)
    async def test_connection(self):
        api_key = self.api_keys["api_key"]
        secret_key = self.api_keys["secret_key"]
        if not api_key or not secret_key:
            async with self:
                self.is_connected = False
                self.connection_message = "API keys not set."
            return
        try:
            client = Client(api_key, secret_key, testnet=self.is_testnet)
            account_info = client.get_account()
            async with self:
                self.is_connected = True
                self.connection_message = "Successfully connected to Binance."
                balances = [
                    WalletBalance(**bal)
                    for bal in account_info.get("balances", [])
                    if float(bal.get("free", 0)) > 0 or float(bal.get("locked", 0)) > 0
                ]
                self.account_balance = balances
            yield ExchangeState.fetch_trading_pairs
        except BinanceAPIException as e:
            logging.exception(f"Binance API Error: {e}")
            async with self:
                self.is_connected = False
                self.connection_message = f"Connection failed: {e.message}"
                self.api_keys = {"api_key": "", "secret_key": ""}
        except Exception as e:
            logging.exception(f"Unexpected connection error: {e}")
            async with self:
                self.is_connected = False
                self.connection_message = f"An unexpected error occurred: {e}"
                self.api_keys = {"api_key": "", "secret_key": ""}

    @rx.event(background=True)
    async def fetch_trading_pairs(self):
        if not self.is_connected:
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
            async with self:
                self.connection_message = f"Failed to fetch trading pairs: {e}"

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
                if keys:
                    async with self:
                        self.api_keys = keys
                    await self.test_connection()
        finally:
            db.close()

    @rx.event(background=True)
    async def clear_api_keys(self):
        async with self:
            from app.database import crud
            from app.states.auth_state import AuthState

            self.api_keys = {"api_key": "", "secret_key": ""}
            self.is_connected = False
            self.connection_message = "API keys cleared."
            self.account_balance = []
            self.trading_pairs = []
            auth_state = await self.get_state(AuthState)
            if auth_state.current_user:
                db = self.get_db()
                try:
                    user = crud.get_user_by_email(db, auth_state.current_user["email"])
                    if user:
                        crud.update_user_api_keys(db, user.id, "", "")
                finally:
                    db.close()
        return rx.redirect("/settings")

    async def _get_async_client(self) -> AsyncClient | None:
        api_key = self.api_keys["api_key"]
        secret_key = self.api_keys["secret_key"]
        if not self.is_connected or not api_key or (not secret_key):
            logging.error("Cannot create async client, not connected or keys not set.")
            return None
        try:
            return await AsyncClient.create(
                api_key, secret_key, testnet=self.is_testnet
            )
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