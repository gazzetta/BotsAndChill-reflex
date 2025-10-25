import reflex as rx
from app.states.reset_password_state import ResetPasswordState


def reset_password_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.el.h2(
                "Reset Your Password", class_name="text-2xl font-bold text-gray-800"
            ),
            rx.el.form(
                rx.el.div(
                    rx.el.label(
                        "New Password",
                        htmlFor="password",
                        class_name="text-sm font-medium text-gray-700",
                    ),
                    rx.el.input(
                        id="password",
                        type="password",
                        name="password",
                        class_name="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-teal-500 focus:border-teal-500 sm:text-sm",
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.label(
                        "Confirm New Password",
                        htmlFor="confirm_password",
                        class_name="text-sm font-medium text-gray-700",
                    ),
                    rx.el.input(
                        id="confirm_password",
                        type="password",
                        name="confirm_password",
                        class_name="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-teal-500 focus:border-teal-500 sm:text-sm",
                    ),
                    class_name="mb-6",
                ),
                rx.cond(
                    ResetPasswordState.message != "",
                    rx.el.div(
                        rx.icon(
                            rx.cond(
                                ResetPasswordState.error,
                                "alert-triangle",
                                "check-circle-2",
                            ),
                            class_name="h-5 w-5 mr-3",
                        ),
                        rx.el.p(ResetPasswordState.message, class_name="text-sm"),
                        class_name=rx.cond(
                            ResetPasswordState.error,
                            "flex items-center bg-red-50 border border-red-200 p-3 rounded-md mb-4 text-red-600",
                            "flex items-center bg-green-50 border border-green-200 p-3 rounded-md mb-4 text-green-600",
                        ),
                    ),
                    None,
                ),
                rx.el.button(
                    "Reset Password",
                    type="submit",
                    is_loading=ResetPasswordState.is_loading,
                    class_name="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500",
                ),
                on_submit=ResetPasswordState.reset_password,
            ),
            class_name="w-full max-w-md p-8 space-y-8 bg-white rounded-lg shadow-lg",
        ),
        class_name="flex items-center justify-center min-h-screen bg-gray-50 font-['Roboto']",
        on_mount=ResetPasswordState.on_load_verify_token,
    )