import reflex as rx
from app.states.bot_state import BotsState
from app.states.exchange_state import ExchangeState


def wizard_step(
    step_number: int, title: str, is_active: bool, children
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.span(
                    step_number,
                    class_name=rx.cond(
                        is_active,
                        "flex items-center justify-center w-8 h-8 rounded-full bg-teal-600 text-white font-bold",
                        "flex items-center justify-center w-8 h-8 rounded-full bg-gray-200 text-gray-600 font-bold",
                    ),
                ),
                rx.el.h3(
                    title,
                    class_name=rx.cond(
                        is_active,
                        "ml-4 text-lg font-semibold text-gray-800",
                        "ml-4 text-lg font-medium text-gray-500",
                    ),
                ),
                class_name="flex items-center",
            ),
            class_name="flex items-center justify-between",
        ),
        rx.cond(is_active, rx.el.div(children, class_name="mt-4 p-4 border-t"), None),
    )


def config_input_field(
    label: str, name: str, value: rx.Var, type: str = "number"
) -> rx.Component:
    return rx.el.div(
        rx.el.p(label, class_name="block text-sm font-medium text-gray-700"),
        rx.el.input(
            type=type,
            name=name,
            id=name,
            on_change=lambda value: BotsState.update_bot_config_field(name, value),
            class_name="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-teal-500 focus:border-teal-500 sm:text-sm",
            default_value=value.to_string(),
        ),
    )


def create_bot_wizard() -> rx.Component:
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.content(
            rx.radix.primitives.dialog.title("Create a New DCA Bot"),
            rx.el.form(
                wizard_step(
                    1,
                    "Trading Pair",
                    True,
                    rx.el.div(
                        rx.el.p(
                            "Search Pair",
                            class_name="block text-sm font-medium text-gray-700",
                        ),
                        rx.el.div(
                            rx.el.input(
                                placeholder="E.g., BTCUSDT",
                                name="pair_search_input",
                                class_name="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-teal-500 focus:border-teal-500 sm:text-sm rounded-md",
                                default_value=BotsState.current_bot_config["pair"],
                                on_key_down=BotsState.set_pair_search_term.debounce(
                                    300
                                ),
                                on_focus=lambda: BotsState.set_show_pair_dropdown(True),
                            ),
                            rx.cond(
                                BotsState.show_pair_dropdown,
                                rx.el.div(
                                    rx.foreach(
                                        ExchangeState.filtered_trading_pairs,
                                        lambda pair: rx.el.div(
                                            pair,
                                            on_mouse_down=[
                                                lambda: BotsState.update_bot_config_pair(
                                                    pair
                                                ),
                                                lambda: BotsState.set_show_pair_dropdown(
                                                    False
                                                ),
                                            ],
                                            class_name="px-3 py-2 hover:bg-gray-100 cursor-pointer text-sm",
                                        ),
                                    ),
                                    class_name="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto",
                                ),
                                None,
                            ),
                            class_name="relative",
                            on_mouse_leave=lambda: BotsState.set_show_pair_dropdown(
                                False
                            ),
                        ),
                    ),
                ),
                wizard_step(
                    2,
                    "Order Sizes",
                    True,
                    rx.el.div(
                        config_input_field(
                            "Base Order Size (USDT)",
                            "base_order_size",
                            BotsState.current_bot_config["base_order_size"],
                        ),
                        config_input_field(
                            "Safety Order Size (USDT)",
                            "safety_order_size",
                            BotsState.current_bot_config["safety_order_size"],
                        ),
                        class_name="grid grid-cols-2 gap-4",
                    ),
                ),
                wizard_step(
                    3,
                    "Safety Orders Strategy",
                    True,
                    rx.el.div(
                        config_input_field(
                            "Max Safety Orders",
                            "max_safety_orders",
                            BotsState.current_bot_config["max_safety_orders"],
                            type="number",
                        ),
                        config_input_field(
                            "Price Deviation (%)",
                            "price_deviation",
                            BotsState.current_bot_config["price_deviation"],
                        ),
                        config_input_field(
                            "Safety Order Volume Scale",
                            "safety_order_volume_scale",
                            BotsState.current_bot_config["safety_order_volume_scale"],
                        ),
                        config_input_field(
                            "Safety Order Price Deviation Scale",
                            "safety_order_step_scale",
                            BotsState.current_bot_config["safety_order_step_scale"],
                        ),
                        class_name="grid grid-cols-2 gap-4",
                    ),
                ),
                wizard_step(
                    4,
                    "Immediate Safety Orders",
                    True,
                    rx.el.div(
                        config_input_field(
                            "Immediate Safety Orders",
                            "immediate_safety_orders",
                            BotsState.current_bot_config["immediate_safety_orders"],
                            type="number",
                        ),
                        rx.el.p(
                            "These orders will be placed as limit orders immediately when the bot starts.",
                            class_name="text-xs text-gray-500 mt-1 col-span-2",
                        ),
                        rx.el.div(
                            rx.el.p(
                                "Required USDT to start:", class_name="font-medium"
                            ),
                            rx.el.p(
                                f"${BotsState.required_balance.to_string()}",
                                class_name="font-bold text-teal-600",
                            ),
                            class_name="mt-2 p-2 bg-gray-50 rounded-md flex justify-between items-center text-sm",
                        ),
                    ),
                ),
                wizard_step(
                    5,
                    "Take Profit",
                    True,
                    config_input_field(
                        "Take Profit Percentage (%)",
                        "take_profit_percentage",
                        BotsState.current_bot_config["take_profit_percentage"],
                    ),
                ),
                rx.el.div(
                    rx.el.button(
                        "Cancel",
                        on_click=BotsState.close_create_wizard,
                        class_name="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300",
                        type="button",
                    ),
                    rx.el.button(
                        "Create Bot",
                        type="submit",
                        class_name="px-4 py-2 bg-teal-600 text-white rounded-md hover:bg-teal-700",
                    ),
                    class_name="flex justify-end gap-4 mt-6",
                ),
                on_submit=lambda form_data: BotsState.add_bot(form_data),
                reset_on_submit=True,
                class_name="space-y-4",
            ),
        ),
        open=BotsState.show_create_wizard,
        on_open_change=BotsState.set_show_create_wizard,
    )