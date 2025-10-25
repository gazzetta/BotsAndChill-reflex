import reflex as rx
from app.states.bot_state import BotsState
from app.states.deal_state import DealState


def config_display_item(label: str, value: rx.Var) -> rx.Component:
    return rx.el.div(
        rx.el.p(label, class_name="text-sm font-medium text-gray-500"),
        rx.el.p(value, class_name="text-sm font-semibold text-gray-800"),
        class_name="flex justify-between py-2 border-b",
    )


def deal_history_table() -> rx.Component:
    return rx.el.div(
        rx.el.h3("Deal History", class_name="text-lg font-bold text-gray-800 mb-4"),
        rx.el.table(
            rx.el.thead(
                rx.el.tr(
                    rx.el.th("Entry Time", class_name="px-4 py-2 text-left"),
                    rx.el.th("Close Time", class_name="px-4 py-2 text-left"),
                    rx.el.th("Realized P/L", class_name="px-4 py-2 text-left"),
                    rx.el.th("Status", class_name="px-4 py-2 text-left"),
                )
            ),
            rx.el.tbody(
                rx.foreach(
                    DealState.bot_deals,
                    lambda deal: rx.el.tr(
                        rx.el.td(
                            deal["entry_time"].to_string(),
                            class_name="border-t px-4 py-2",
                        ),
                        rx.el.td(
                            deal["close_time"].to_string(),
                            class_name="border-t px-4 py-2",
                        ),
                        rx.el.td(
                            f"${deal['realized_pnl'].to_string()}",
                            class_name="border-t px-4 py-2",
                        ),
                        rx.el.td(deal["status"], class_name="border-t px-4 py-2"),
                    ),
                )
            ),
            class_name="w-full text-sm",
        ),
        class_name="bg-white p-6 rounded-xl shadow-md mt-6",
    )


def bot_detail_page() -> rx.Component:
    return rx.el.div(
        rx.cond(
            BotsState.selected_bot,
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.el.h1(
                            BotsState.selected_bot["name"],
                            class_name="text-3xl font-bold text-gray-800",
                        ),
                        rx.el.p(
                            BotsState.selected_bot["config"]["pair"],
                            class_name="text-lg text-gray-500",
                        ),
                    ),
                    rx.el.div(
                        rx.el.button(
                            rx.icon("play", class_name="w-4 h-4"),
                            on_click=lambda: BotsState.start_bot(
                                BotsState.selected_bot["id"]
                            ),
                        ),
                        rx.el.button(
                            rx.icon("pause", class_name="w-4 h-4"),
                            on_click=lambda: BotsState.pause_bot(
                                BotsState.selected_bot["id"]
                            ),
                        ),
                        rx.el.button(
                            rx.icon("trash-2", class_name="w-4 h-4"),
                            on_click=lambda: BotsState.remove_bot_and_redirect(
                                BotsState.selected_bot["id"]
                            ),
                        ),
                        class_name="flex items-center gap-2",
                    ),
                    class_name="flex items-center justify-between mb-6",
                ),
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.el.h3(
                                "Configuration",
                                class_name="text-lg font-bold text-gray-800 mb-2",
                            ),
                            config_display_item(
                                "Base Order Size",
                                BotsState.selected_bot["config"][
                                    "base_order_size"
                                ].to_string(),
                            ),
                            config_display_item(
                                "Safety Order Size",
                                BotsState.selected_bot["config"][
                                    "safety_order_size"
                                ].to_string(),
                            ),
                            config_display_item(
                                "Max Safety Orders",
                                BotsState.selected_bot["config"][
                                    "max_safety_orders"
                                ].to_string(),
                            ),
                            config_display_item(
                                "Price Deviation",
                                f"{BotsState.selected_bot['config']['price_deviation'].to_string()}% ",
                            ),
                            config_display_item(
                                "Take Profit",
                                f"{BotsState.selected_bot['config']['take_profit_percentage'].to_string()}% ",
                            ),
                            class_name="bg-white p-6 rounded-xl shadow-md",
                        )
                    ),
                    rx.el.div(
                        rx.cond(
                            DealState.active_deal,
                            rx.el.div(
                                rx.el.h3(
                                    "Active Deal",
                                    class_name="text-lg font-bold text-gray-800 mb-2",
                                ),
                                config_display_item(
                                    "Average Entry Price",
                                    DealState.active_deal[
                                        "average_entry_price"
                                    ].to_string(),
                                ),
                                config_display_item(
                                    "Total Quantity",
                                    DealState.active_deal["total_quantity"].to_string(),
                                ),
                                config_display_item(
                                    "Unrealized PNL",
                                    DealState.active_deal["unrealized_pnl"].to_string(),
                                ),
                                config_display_item(
                                    "Safety Orders Filled",
                                    DealState.active_deal["filled_safety_orders"]
                                    .length()
                                    .to_string(),
                                ),
                                config_display_item(
                                    "Safety Orders Pending",
                                    DealState.active_deal["pending_safety_orders"]
                                    .length()
                                    .to_string(),
                                ),
                                class_name="bg-white p-6 rounded-xl shadow-md",
                            ),
                            rx.el.div(
                                rx.el.p(
                                    "No active deal for this bot.",
                                    class_name="text-gray-500",
                                ),
                                class_name="flex items-center justify-center h-full bg-white p-6 rounded-xl shadow-md",
                            ),
                        )
                    ),
                    class_name="grid grid-cols-1 md:grid-cols-2 gap-6",
                ),
                deal_history_table(),
            ),
            rx.el.div("Bot not found or loading...", class_name="text-center p-8"),
        ),
        on_mount=[BotsState.get_bot_by_id, DealState.get_deals_for_bot],
    )