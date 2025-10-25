import reflex as rx
from app.states.auth_state import AuthState
from app.states.sidebar_state import SidebarState
from app.states.notification_state import NotificationState
from app.states.exchange_state import ExchangeState


def notification_item(notification: rx.Var[dict]) -> rx.Component:
    return rx.el.div(
        rx.el.p(notification["message"], class_name="text-sm"),
        rx.el.p(
            notification["timestamp"].to_string(),
            class_name="text-xs text-gray-400 mt-1",
        ),
        class_name="p-2 border-b hover:bg-gray-50",
    )


def testnet_banner() -> rx.Component:
    return rx.cond(
        ExchangeState.is_testnet,
        rx.el.div(
            rx.icon("flask-round", class_name="h-4 w-4 mr-2"),
            rx.el.p(
                "Testnet Mode Active - All trades are on the Binance Spot Test Network.",
                class_name="text-sm font-medium",
            ),
            class_name="flex items-center justify-center w-full bg-yellow-300 text-yellow-800 p-2",
        ),
        None,
    )


def app_bar() -> rx.Component:
    return rx.el.header(
        testnet_banner(),
        rx.el.div(
            rx.el.button(
                rx.icon("menu", class_name="h-6 w-6"),
                on_click=SidebarState.toggle_sidebar,
                class_name="p-2 rounded-md text-gray-500 hover:bg-gray-100",
            ),
            rx.el.div(
                rx.el.p(
                    "Welcome back, ",
                    rx.el.span(
                        AuthState.current_user["username"], class_name="font-semibold"
                    ),
                    "!",
                    class_name="text-sm text-gray-600",
                ),
                class_name="flex-1",
            ),
            rx.el.div(
                rx.radix.dropdown_menu.root(
                    rx.radix.dropdown_menu.trigger(
                        rx.el.button(
                            rx.icon("bell", class_name="h-6 w-6"),
                            rx.cond(
                                NotificationState.unread_count > 0,
                                rx.el.span(
                                    NotificationState.unread_count,
                                    class_name="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-xs text-white",
                                ),
                                None,
                            ),
                            class_name="relative p-2 rounded-full text-gray-500 hover:bg-gray-100",
                        )
                    ),
                    rx.radix.dropdown_menu.content(
                        rx.el.div(
                            rx.el.h3("Notifications", class_name="font-semibold p-2"),
                            rx.el.button(
                                "Mark all as read",
                                on_click=NotificationState.mark_all_as_read,
                                class_name="text-xs text-teal-600 hover:underline",
                            ),
                            class_name="flex justify-between items-center border-b",
                        ),
                        rx.foreach(
                            NotificationState.recent_notifications, notification_item
                        ),
                        rx.cond(
                            NotificationState.notifications.length() == 0,
                            rx.el.p(
                                "No new notifications",
                                class_name="text-sm text-gray-500 p-4 text-center",
                            ),
                            None,
                        ),
                    ),
                ),
                rx.el.a(
                    rx.icon("settings", class_name="h-6 w-6"),
                    href="/settings",
                    class_name="p-2 block rounded-full text-gray-500 hover:bg-gray-100",
                ),
            ),
            class_name="flex items-center space-x-2",
        ),
        class_name="flex items-center justify-between h-16 px-4 bg-white/70 backdrop-blur-md border-b border-gray-200 shadow-sm sticky top-0 z-40",
    )