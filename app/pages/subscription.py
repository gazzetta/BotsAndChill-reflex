import reflex as rx
from app.states.auth_state import AuthState
from app.states.polar_state import PolarState


def benefit_item(icon: str, text: str) -> rx.Component:
    return rx.el.li(
        rx.icon(icon, class_name="h-6 w-6 text-teal-500"),
        rx.el.span(text, class_name="text-gray-700"),
        class_name="flex items-center space-x-3",
    )


def subscription_page() -> rx.Component:
    return rx.el.div(
        rx.el.h1("Subscription", class_name="text-3xl font-bold text-gray-800 mb-6"),
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Your Current Plan", class_name="text-xl font-bold text-gray-800"
                ),
                rx.el.div(
                    rx.el.span(
                        AuthState.current_user["subscription_tier"],
                        class_name="px-3 py-1 text-lg font-semibold rounded-full",
                        color=rx.cond(
                            AuthState.current_user["subscription_tier"] == "PRO",
                            "#ca8a04",
                            "#4b5563",
                        ),
                        background_color=rx.cond(
                            AuthState.current_user["subscription_tier"] == "PRO",
                            "#fef9c3",
                            "#f3f4f6",
                        ),
                    ),
                    class_name="mt-4",
                ),
                rx.cond(
                    PolarState.subscription_active,
                    rx.el.div(
                        rx.cond(
                            PolarState.subscription_renewal_date != "",
                            rx.el.p(
                                f"Renews on: {PolarState.subscription_renewal_date}",
                                class_name="text-sm text-gray-500 mt-2",
                            ),
                            None,
                        ),
                        rx.el.button(
                            "Manage Subscription",
                            on_click=PolarState.get_customer_portal_url,
                            is_loading=PolarState.is_loading,
                            class_name="mt-4 w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-600 hover:bg-gray-700",
                        ),
                    ),
                    rx.el.p(
                        "Upgrade to PRO to unlock more features!",
                        class_name="text-sm text-gray-500 mt-2",
                    ),
                ),
                class_name="p-6 bg-white rounded-lg shadow-md",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.h3("PRO Plan", class_name="text-2xl font-bold text-gray-800"),
                    rx.el.p(
                        rx.el.span("$10", class_name="text-4xl font-extrabold"),
                        "/month",
                        class_name="text-gray-500",
                    ),
                    class_name="flex items-baseline justify-between",
                ),
                rx.el.ul(
                    benefit_item("bot", "Run up to 5 bots simultaneously"),
                    benefit_item(
                        "sliders-horizontal", "Advanced DCA strategies & settings"
                    ),
                    benefit_item("shield-check", "Priority support"),
                    benefit_item(
                        "sparkles", "Early access to new features like Grid Bots"
                    ),
                    class_name="mt-6 space-y-4",
                ),
                rx.cond(
                    ~PolarState.subscription_active,
                    rx.el.button(
                        "Upgrade to PRO",
                        on_click=PolarState.create_checkout_session,
                        is_loading=PolarState.is_loading,
                        class_name="mt-8 w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-lg font-medium text-white bg-teal-600 hover:bg-teal-700",
                    ),
                    rx.el.div(
                        rx.el.p(
                            "You are already a PRO member!",
                            class_name="text-center font-semibold text-green-600",
                        ),
                        class_name="mt-8 p-3 bg-green-50 rounded-md",
                    ),
                ),
                class_name="p-6 bg-white rounded-lg shadow-md border-2 border-teal-500",
            ),
            class_name="grid grid-cols-1 lg:grid-cols-2 gap-8",
        ),
        on_mount=[AuthState.check_login, PolarState.on_load_subscription_status],
    )