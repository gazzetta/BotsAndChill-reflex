import reflex as rx


def overview_card(icon: str, title: str, value: rx.Var, color: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name=f"h-7 w-7 {color}"),
            class_name="p-3 bg-gray-100 rounded-lg",
        ),
        rx.el.div(
            rx.el.p(title, class_name="text-sm font-medium text-gray-500"),
            rx.el.p(value, class_name="text-2xl font-bold text-gray-800"),
            class_name="mt-2",
        ),
        class_name="bg-white p-6 rounded-xl shadow-[0_1px_3px_rgba(0,0,0,0.12)] hover:shadow-[0_4px_8px_rgba(0,0,0,0.15)] transition-shadow duration-300",
    )