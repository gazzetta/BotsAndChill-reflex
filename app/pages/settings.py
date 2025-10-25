import reflex as rx
from app.states.exchange_state import ExchangeState


def api_key_form() -> rx.Component:
    return rx.el.div(
        rx.el.h2("Binance API Keys", class_name="text-xl font-bold text-gray-800"),
        rx.el.p(
            "Securely connect your Binance account to enable trading.",
            class_name="text-gray-500 mt-1",
        ),
        rx.el.form(
            rx.el.div(
                rx.el.label(
                    "API Key",
                    htmlFor="api_key",
                    class_name="text-sm font-medium text-gray-700",
                ),
                rx.el.input(
                    id="api_key",
                    name="api_key",
                    default_value=ExchangeState.api_keys["api_key"],
                    class_name="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-teal-500 focus:border-teal-500",
                ),
                class_name="mb-4",
            ),
            rx.el.div(
                rx.el.label(
                    "Secret Key",
                    htmlFor="secret_key",
                    class_name="text-sm font-medium text-gray-700",
                ),
                rx.el.div(
                    rx.el.input(
                        id="secret_key",
                        name="secret_key",
                        type=rx.cond(ExchangeState.show_secret_key, "text", "password"),
                        default_value=ExchangeState.api_keys["secret_key"],
                        class_name="block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-teal-500 focus:border-teal-500",
                    ),
                    rx.el.button(
                        rx.icon(
                            rx.cond(ExchangeState.show_secret_key, "eye-off", "eye"),
                            class_name="h-5 w-5",
                        ),
                        on_click=ExchangeState.toggle_show_secret_key,
                        type="button",
                        class_name="absolute inset-y-0 right-0 px-3 flex items-center text-gray-500",
                    ),
                    class_name="mt-1 relative",
                ),
                class_name="mb-6",
            ),
            rx.el.button(
                "Save API Keys",
                type="submit",
                class_name="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500",
            ),
            on_submit=ExchangeState.save_api_keys,
        ),
        rx.el.button(
            rx.icon("trash-2", class_name="w-4 h-4 mr-2"),
            "Clear API Keys",
            on_click=ExchangeState.clear_api_keys,
            class_name="mt-4 w-full flex justify-center py-2 px-4 border border-red-300 rounded-md shadow-sm text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500",
        ),
        class_name="p-6 bg-white rounded-lg shadow-md",
    )


def wallet_balances() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h2("Wallet Balances", class_name="text-xl font-bold text-gray-800"),
            rx.el.button(
                rx.icon("refresh-cw", class_name="w-4 h-4 mr-2"),
                "Refresh",
                on_click=ExchangeState.refresh_balances,
                class_name="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-teal-600 hover:bg-teal-700",
            ),
            class_name="flex justify-between items-center mb-2",
        ),
        rx.cond(
            ExchangeState.last_balance_refresh != "",
            rx.el.p(
                f"Last updated: {ExchangeState.last_balance_refresh}",
                class_name="text-xs text-gray-500 mb-4",
            ),
            None,
        ),
        rx.cond(
            ExchangeState.has_api_keys,
            rx.el.div(
                rx.el.div(
                    rx.el.div("Asset", class_name="font-semibold"),
                    rx.el.div("Available", class_name="font-semibold text-right"),
                    rx.el.div("Locked", class_name="font-semibold text-right"),
                    class_name="grid grid-cols-3 gap-4 p-2 border-b font-medium text-sm text-gray-600",
                ),
                rx.el.div(
                    rx.foreach(
                        ExchangeState.account_balance,
                        lambda balance: rx.el.div(
                            rx.el.div(
                                rx.image(
                                    src=f"https://api.dicebear.com/9.x/icons/svg?seed={balance['asset']}",
                                    class_name="w-6 h-6 mr-2",
                                ),
                                rx.text(balance["asset"]),
                                class_name="flex items-center",
                            ),
                            rx.text(balance["free"], class_name="text-right"),
                            rx.text(balance["locked"], class_name="text-right"),
                            class_name="grid grid-cols-3 gap-4 p-2 text-sm",
                        ),
                    ),
                    class_name="max-h-96 overflow-y-auto",
                ),
            ),
            rx.el.div(
                rx.icon("key-round", class_name="h-12 w-12 text-gray-300"),
                rx.el.p(
                    "Save your API keys to see wallet balances.",
                    class_name="text-gray-500 mt-4",
                ),
                class_name="text-center flex flex-col items-center justify-center p-8",
            ),
        ),
        class_name="bg-white rounded-lg shadow-md p-6",
    )


def settings_page() -> rx.Component:
    return rx.el.div(
        rx.el.h1(
            "Exchange Settings", class_name="text-3xl font-bold text-gray-800 mb-6"
        ),
        rx.el.div(
            api_key_form(),
            wallet_balances(),
            class_name="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start",
        ),
        on_mount=ExchangeState.connect_binance_on_load,
    )