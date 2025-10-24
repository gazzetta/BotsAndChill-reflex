import reflex as rx


def verify_email_page() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Verifying your email...",
                    class_name="text-2xl font-bold text-gray-800",
                ),
                rx.el.p(
                    "Please wait while we confirm your email address.",
                    class_name="text-gray-500 mt-2",
                ),
                rx.spinner(class_name="mt-6 text-teal-500 w-12 h-12"),
                class_name="text-center",
            ),
            class_name="w-full max-w-md p-8 space-y-8 bg-white rounded-lg shadow-lg",
        ),
        class_name="flex items-center justify-center min-h-screen bg-gray-50 font-['Roboto']",
    )