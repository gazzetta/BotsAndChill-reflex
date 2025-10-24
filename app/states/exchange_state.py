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
    api_keys_json: str = rx.LocalStorage(name="binance_api_keys")
    is_connected: bool = False
    connection_message: str = ""
    account_balance: list[WalletBalance] = []
    trading_pairs: list[str] = []
    show_secret_key: bool = False

    @rx.var
    def is_testnet(self) -> bool:
        return os.environ.get("BINANCE_TESTNET", "false").lower() == "true"

    @rx.var
    def api_keys(self) -> APIKeys:
        if self.api_keys_json:
            try:
                return APIKeys(**json.loads(self.api_keys_json))
            except (json.JSONDecodeError, TypeError) as e:
                logging.exception(f"Error decoding API keys: {e}")
                return {"api_key": "", "secret_key": ""}
        return {"api_key": "", "secret_key": ""}

    @rx.var
    def obfuscated_secret_key(self) -> str:
        secret = self.api_keys.get("secret_key", "")
        if len(secret) > 8:
            return f"{secret[:4]}...{secret[-4:]}"
        return ""

    @rx.event
    def toggle_show_secret_key(self):
        self.show_secret_key = not self.show_secret_key

    @rx.event
    def save_api_keys(self, form_data: dict):
        api_key = form_data.get("api_key", "").strip()
        secret_key = form_data.get("secret_key", "").strip()
        if not api_key or not secret_key:
            self.connection_message = "API Key and Secret Key cannot be empty."
            self.is_connected = False
            return
        keys = {"api_key": api_key, "secret_key": secret_key}
        self.api_keys_json = json.dumps(keys)
        return ExchangeState.test_connection

    @rx.event(background=True)
    async def test_connection(self):
        if not self.api_keys_json:
            async with self:
                self.is_connected = False
                self.connection_message = "API keys not set."
            return
        try:
            client = Client(
                self.api_keys["api_key"],
                self.api_keys["secret_key"],
                testnet=self.is_testnet,
            )
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
                self.api_keys_json = ""
        except Exception as e:
            logging.exception(f"Unexpected connection error: {e}")
            async with self:
                self.is_connected = False
                self.connection_message = f"An unexpected error occurred: {e}"
                self.api_keys_json = ""

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

    @rx.event
    def connect_binance_on_load(self):
        if self.api_keys_json:
            return ExchangeState.test_connection

    @rx.event
    def clear_api_keys(self):
        self.api_keys_json = ""
        self.is_connected = False
        self.connection_message = "API keys cleared."
        self.account_balance = []
        self.trading_pairs = []
        return rx.redirect("/settings")

    async def _get_async_client(self) -> AsyncClient | None:
        if not self.is_connected or not self.api_keys_json:
            logging.error("Cannot create async client, not connected or keys not set.")
            return None
        try:
            return await AsyncClient.create(
                self.api_keys["api_key"],
                self.api_keys["secret_key"],
                testnet=self.is_testnet,
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
    async def validate_balance(self, asset: str, required_amount: float) -> bool:
        client = await self._get_async_client()
        if not client:
            return False
        try:
            balance = await client.get_asset_balance(asset=asset)
            if balance and float(balance["free"]) >= required_amount:
                return True
            logging.warning(
                f"Insufficient balance for {asset}. Required: {required_amount}, Available: {(balance['free'] if balance else '0')}"
            )
            return False
        except Exception as e:
            logging.exception(f"Error validating balance for {asset}: {e}")
            return False
        finally:
            if client:
                await client.close_connection()