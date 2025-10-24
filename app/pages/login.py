import reflex as rx
from app.states.auth_state import AuthState


def login_form() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Sign in to your account", class_name="text-2xl font-bold text-gray-800"
        ),
        rx.el.p(
            "Enter your credentials to access your account",
            class_name="text-gray-500 mt-2",
        ),
        rx.el.form(
            rx.el.div(
                rx.el.label(
                    "Email",
                    htmlFor="email",
                    class_name="text-sm font-medium text-gray-700",
                ),
                rx.el.input(
                    id="email",
                    type="email",
                    name="email",
                    placeholder="m@example.com",
                    class_name="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-teal-500 focus:border-teal-500 sm:text-sm",
                ),
                class_name="mb-4",
            ),
            rx.el.div(
                rx.el.label(
                    "Password",
                    htmlFor="password",
                    class_name="text-sm font-medium text-gray-700",
                ),
                rx.el.input(
                    id="password",
                    type="password",
                    name="password",
                    class_name="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-teal-500 focus:border-teal-500 sm:text-sm",
                ),
                class_name="mb-6",
            ),
            rx.cond(
                AuthState.login_error != "",
                rx.el.div(
                    rx.icon("badge_alert", class_name="h-5 w-5 text-red-500 mr-3"),
                    rx.el.p(AuthState.login_error, class_name="text-sm text-red-600"),
                    class_name="flex items-center bg-red-50 border border-red-200 p-3 rounded-md mb-4",
                ),
                None,
            ),
            rx.el.button(
                "Sign In",
                type="submit",
                class_name="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500",
            ),
            on_submit=AuthState.login,
        ),
        rx.el.p(
            "Don't have an account? ",
            rx.el.a(
                "Sign up",
                href="/register",
                class_name="font-medium text-teal-600 hover:text-teal-500",
            ),
            class_name="mt-6 text-center text-sm text-gray-600",
        ),
        class_name="w-full max-w-md p-8 space-y-8 bg-white rounded-lg shadow-lg",
    )


def login_page() -> rx.Component:
    return rx.el.main(
        login_form(),
        class_name="flex items-center justify-center min-h-screen bg-gray-50 font-['Roboto']",
    )