import reflex as rx
from app.states.auth_state import AuthState
from app.states.bot_state import BotsState
from app.states.polar_state import PolarState
from app.states.exchange_state import ExchangeState
from app.components.dashboard.create_bot_wizard import create_bot_wizard


def status_badge(status: rx.Var[str]) -> rx.Component:
    return rx.el.span(
        status,
        class_name=rx.match(
            status,
            (
                "active",
                "px-2 py-1 text-xs font-medium text-white bg-green-600 rounded-full",
            ),
            (
                "paused",
                "px-2 py-1 text-xs font-medium text-white bg-yellow-600 rounded-full",
            ),
            (
                "monitoring",
                "px-2 py-1 text-xs font-medium text-white bg-blue-600 rounded-full",
            ),
            (
                "starting",
                "px-2 py-1 text-xs font-medium text-white bg-blue-400 rounded-full animate-pulse",
            ),
            (
                "stopped",
                "px-2 py-1 text-xs font-medium text-white bg-gray-600 rounded-full",
            ),
            (
                "error",
                "px-2 py-1 text-xs font-medium text-white bg-red-600 rounded-full",
            ),
            "px-2 py-1 text-xs font-medium text-white bg-gray-500 rounded-full",
        ),
    )


def bot_card(bot: rx.Var[dict], **props) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h3(bot["name"], class_name="text-lg font-semibold text-gray-800"),
            status_badge(bot["status"]),
            class_name="flex items-center justify-between",
        ),
        rx.el.div(
            rx.el.p(
                bot["config"]["pair"], class_name="text-sm font-medium text-gray-600"
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.p("Total P/L", class_name="text-xs text-gray-500"),
                    rx.el.p(
                        f"${bot['total_pnl'].to_string()}",
                        class_name="font-semibold",
                        color=rx.cond(
                            bot["total_pnl"] >= 0, "text-green-600", "text-red-600"
                        ),
                    ),
                ),
                rx.el.div(
                    rx.el.p("Deals", class_name="text-xs text-gray-500"),
                    rx.el.p(bot["deals_count"], class_name="font-semibold"),
                ),
                class_name="flex gap-4 text-sm",
            ),
            class_name="mt-4 flex items-center justify-between",
        ),
        rx.el.div(
            rx.el.a(
                rx.icon("settings", class_name="w-4 h-4 mr-2"),
                "View",
                href=f"/bots/{bot['id']}",
                class_name="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon("play", class_name="w-4 h-4"),
                    on_click=lambda: BotsState.start_bot(bot["id"]),
                    class_name="p-1.5 text-gray-500 hover:text-green-600 hover:bg-gray-100 rounded-md",
                ),
                rx.el.button(
                    rx.icon("pause", class_name="w-4 h-4"),
                    on_click=lambda: BotsState.pause_bot(bot["id"]),
                    class_name="p-1.5 text-gray-500 hover:text-yellow-600 hover:bg-gray-100 rounded-md",
                ),
                rx.el.button(
                    rx.icon("trash-2", class_name="w-4 h-4"),
                    on_click=lambda: BotsState.remove_bot(bot["id"]),
                    class_name="p-1.5 text-gray-500 hover:text-red-600 hover:bg-gray-100 rounded-md",
                ),
                class_name="flex items-center gap-1",
            ),
            class_name="mt-4 flex items-center justify-between border-t border-gray-200 pt-4",
        ),
        class_name="bg-white p-4 rounded-lg shadow-md hover:shadow-lg transition-shadow",
        **props,
    )


def upgrade_dialog() -> rx.Component:
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.trigger(rx.el.div()),
        rx.radix.primitives.dialog.content(
            rx.radix.primitives.dialog.title("Upgrade to PRO"),
            rx.radix.primitives.dialog.description(
                "You've reached the bot limit for the FREE plan. Upgrade to PRO to create more bots and unlock powerful features."
            ),
            rx.el.ul(
                rx.el.li("Up to 5 active bots"),
                rx.el.li("Advanced DCA settings"),
                rx.el.li("Priority support"),
                class_name="list-disc list-inside my-4 text-sm text-gray-600",
            ),
            rx.el.div(
                rx.radix.primitives.dialog.close(
                    rx.el.button(
                        "Maybe Later",
                        class_name="px-4 py-2 bg-gray-200 text-gray-800 rounded-md",
                    )
                ),
                rx.el.button(
                    "Upgrade Now ($10/mo)",
                    on_click=PolarState.create_checkout_session,
                    is_loading=PolarState.is_loading,
                    class_name="px-4 py-2 bg-teal-600 text-white rounded-md",
                ),
                class_name="flex justify-end gap-4 mt-4",
            ),
        ),
        open=BotsState.show_upgrade_dialog,
        on_open_change=BotsState.set_show_upgrade_dialog,
    )


def bots_page() -> rx.Component:
    return rx.el.div(
        upgrade_dialog(),
        create_bot_wizard(),
        rx.el.div(
            rx.el.div(
                rx.el.h1("My Bots", class_name="text-3xl font-bold text-gray-800"),
                rx.el.div(
                    rx.el.p(
                        f"{BotsState.bots.length()} / {rx.cond(AuthState.current_user['subscription_tier'] == 'PRO', '5', '1')} Bots",
                        class_name="text-sm font-medium text-gray-500",
                    ),
                    class_name="px-3 py-1.5 bg-gray-100 rounded-lg border",
                ),
                class_name="flex items-center gap-4",
            ),
            rx.el.button(
                rx.icon("circle_plus", class_name="w-5 h-5 mr-2"),
                "Create Bot",
                on_click=BotsState.open_create_wizard,
                class_name="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500",
            ),
            class_name="flex items-center justify-between mb-6",
        ),
        rx.cond(
            BotsState.bots.length() > 0,
            rx.el.div(
                rx.foreach(BotsState.bots, lambda bot: bot_card(bot, key=bot["id"])),
                class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",
            ),
            rx.el.div(
                rx.icon("bot", class_name="w-16 h-16 text-gray-300"),
                rx.el.h2(
                    "No Bots Yet", class_name="mt-4 text-xl font-semibold text-gray-700"
                ),
                rx.el.p(
                    "Click 'Create Bot' to get started.",
                    class_name="mt-1 text-sm text-gray-500",
                ),
                class_name="flex flex-col items-center justify-center text-center p-8 bg-white rounded-lg shadow-md",
            ),
        ),
        on_mount=[AuthState.check_login, ExchangeState.fetch_trading_pairs],
    )