import reflex as rx
from app.states.auth_state import AuthState
from app.states.sidebar_state import SidebarState


def nav_item(icon: str, text: str, href: str, is_active: bool) -> rx.Component:
    return rx.el.a(
        rx.icon(icon, class_name="w-5 h-5"),
        rx.cond(SidebarState.is_open, rx.el.span(text, class_name="ml-3"), None),
        href=href,
        class_name=rx.cond(
            is_active,
            "flex items-center p-2 text-base font-normal text-white bg-teal-700 rounded-lg",
            "flex items-center p-2 text-base font-normal text-gray-300 rounded-lg hover:bg-gray-700",
        ),
    )


def sidebar() -> rx.Component:
    nav_items = [
        {"icon": "layout-dashboard", "text": "Dashboard", "href": "/"},
        {"icon": "bot", "text": "Bots", "href": "/bots"},
        {"icon": "bar-chart-2", "text": "Analytics", "href": "/analytics"},
        {"icon": "settings-2", "text": "Exchange Settings", "href": "/settings"},
        {"icon": "gem", "text": "Subscription", "href": "/subscription"},
    ]
    return rx.el.aside(
        rx.el.div(
            rx.el.div(
                rx.icon("bar-chart-3", class_name="h-8 w-8 text-teal-400"),
                rx.cond(
                    SidebarState.is_open,
                    rx.el.span(
                        "3CommasClone",
                        class_name="ml-3 text-xl font-semibold text-white",
                    ),
                    None,
                ),
                class_name="flex items-center p-4 border-b border-gray-700",
            ),
            rx.el.nav(
                rx.foreach(
                    nav_items,
                    lambda item: nav_item(
                        item["icon"],
                        item["text"],
                        item["href"],
                        rx.State.router.page.path == item["href"],
                    ),
                ),
                class_name="flex-1 px-3 py-4 space-y-2",
            ),
            rx.cond(
                AuthState.is_logged_in,
                rx.el.div(
                    rx.el.div(
                        rx.image(
                            src=f"https://api.dicebear.com/9.x/initials/svg?seed={AuthState.current_user['username']}",
                            class_name="w-10 h-10 rounded-full",
                        ),
                        rx.cond(
                            SidebarState.is_open,
                            rx.el.div(
                                rx.el.p(
                                    AuthState.current_user["username"],
                                    class_name="text-sm font-semibold text-white",
                                ),
                                rx.el.div(
                                    rx.el.span(
                                        AuthState.current_user["subscription_tier"],
                                        class_name=rx.cond(
                                            AuthState.current_user["subscription_tier"]
                                            == "PRO",
                                            "text-xs font-medium px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-800 border border-yellow-300",
                                            "text-xs font-medium px-2 py-0.5 rounded-full bg-gray-200 text-gray-800 border border-gray-300",
                                        ),
                                    ),
                                    class_name="flex items-center gap-2",
                                ),
                                class_name="ml-3",
                            ),
                            None,
                        ),
                        class_name="flex items-center p-2",
                    ),
                    rx.el.button(
                        rx.icon("log-out", class_name="h-5 w-5"),
                        rx.cond(
                            SidebarState.is_open,
                            rx.el.span("Logout", class_name="ml-3"),
                            None,
                        ),
                        on_click=AuthState.logout,
                        class_name="w-full flex items-center p-2 text-base font-normal text-gray-300 rounded-lg hover:bg-gray-700 mt-2",
                    ),
                    class_name="p-4 border-t border-gray-700",
                ),
                None,
            ),
        ),
        class_name=rx.cond(
            SidebarState.is_open,
            "w-64 bg-gray-800 text-white flex flex-col transition-width duration-300 h-screen",
            "w-20 bg-gray-800 text-white flex flex-col transition-width duration-300 h-screen",
        ),
    )