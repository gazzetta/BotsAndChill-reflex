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
                    default_value=ExchangeState.api_keys.get("api_key", ""),
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
                        default_value=ExchangeState.api_keys.get("secret_key", ""),
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
                "Save & Connect",
                type="submit",
                class_name="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500",
            ),
            on_submit=ExchangeState.save_api_keys,
        ),
        class_name="p-6 bg-white rounded-lg shadow-md",
    )


def connection_status() -> rx.Component:
    return rx.el.div(
        rx.el.h2("Connection Status", class_name="text-xl font-bold text-gray-800"),
        rx.el.div(
            rx.el.div(
                rx.icon(
                    rx.cond(ExchangeState.is_connected, "check-circle-2", "x-circle"),
                    class_name="h-6 w-6",
                ),
                rx.el.p(
                    rx.cond(ExchangeState.is_connected, "Connected", "Not Connected"),
                    class_name="font-semibold",
                ),
                class_name=rx.cond(
                    ExchangeState.is_connected,
                    "flex items-center gap-2 text-green-600",
                    "flex items-center gap-2 text-red-600",
                ),
            ),
            rx.el.p(
                ExchangeState.connection_message,
                class_name="text-sm text-gray-500 mt-1",
            ),
            class_name="mt-2",
        ),
        rx.cond(
            ExchangeState.is_connected,
            rx.el.button(
                "Disconnect",
                on_click=ExchangeState.clear_api_keys,
                class_name="mt-4 w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500",
            ),
            None,
        ),
        class_name="p-6 bg-white rounded-lg shadow-md mt-6",
    )


def wallet_balances() -> rx.Component:
    return rx.el.div(
        rx.el.h2("Wallet Balances", class_name="text-xl font-bold text-gray-800 mb-4"),
        rx.cond(
            ExchangeState.is_connected,
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
                class_name="bg-white rounded-lg shadow-md p-6 mt-6",
            ),
            rx.el.div(
                rx.el.p(
                    "Connect to Binance to see your wallet balances.",
                    class_name="text-gray-500",
                ),
                class_name="bg-white rounded-lg shadow-md p-6 mt-6 text-center",
            ),
        ),
    )


def settings_page() -> rx.Component:
    return rx.el.div(
        rx.el.h1(
            "Exchange Settings", class_name="text-3xl font-bold text-gray-800 mb-6"
        ),
        rx.el.div(
            rx.el.div(api_key_form(), connection_status(), class_name="space-y-6"),
            wallet_balances(),
            class_name="grid grid-cols-1 lg:grid-cols-2 gap-6",
        ),
        on_mount=ExchangeState.connect_binance_on_load,
    )