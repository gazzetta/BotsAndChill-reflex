import reflex as rx
from app.states.analytics_state import AnalyticsState
from app.states.bot_state import BotsState


def analytics_stat_card(
    title: str, value: rx.Var, icon: str, unit: str = ""
) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-7 w-7 text-gray-500"),
            class_name="p-3 bg-gray-100 rounded-lg",
        ),
        rx.el.div(
            rx.el.p(title, class_name="text-sm font-medium text-gray-500"),
            rx.el.p(
                value,
                rx.el.span(unit, class_name="text-lg ml-1"),
                class_name="text-2xl font-bold text-gray-800",
            ),
        ),
        class_name="bg-white p-6 rounded-xl shadow-md flex items-center gap-4",
    )


def pnl_chart() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Cumulative P/L Over Time",
            class_name="text-xl font-bold text-gray-800 mb-4",
        ),
        rx.recharts.line_chart(
            rx.recharts.cartesian_grid(stroke_dasharray="3 3"),
            rx.recharts.x_axis(data_key="date"),
            rx.recharts.y_axis(),
            rx.recharts.tooltip(),
            rx.recharts.line(data_key="pnl", stroke="#14b8a6", name="Cumulative P/L"),
            data=AnalyticsState.analytics_data["pnl_history"],
            height=300,
        ),
        rx.el.div(
            rx.el.div(
                rx.el.div(class_name="w-3 h-3 rounded-full bg-[#14b8a6]"),
                rx.el.p("Cumulative P/L", class_name="text-sm text-gray-600"),
                class_name="flex items-center gap-2",
            ),
            class_name="flex justify-center mt-2",
        ),
        class_name="bg-white p-6 rounded-xl shadow-md",
    )


def bot_performance_table() -> rx.Component:
    columns = [
        {"key": "name", "label": "Bot Name"},
        {"key": "pair", "label": "Pair"},
        {"key": "status", "label": "Status"},
        {"key": "total_pnl", "label": "Total P/L"},
        {"key": "deals_count", "label": "Deals"},
    ]
    return rx.el.div(
        rx.el.h2("Bot Performance", class_name="text-xl font-bold text-gray-800 mb-4"),
        rx.el.table(
            rx.el.thead(
                rx.el.tr(
                    rx.foreach(
                        columns,
                        lambda col: rx.el.th(
                            col["label"], class_name="px-4 py-2 text-left"
                        ),
                    ),
                    class_name="bg-gray-50",
                )
            ),
            rx.el.tbody(
                rx.foreach(
                    BotsState.bots,
                    lambda bot: rx.el.tr(
                        rx.el.td(bot["name"], class_name="border-t px-4 py-2"),
                        rx.el.td(
                            bot["config"]["pair"], class_name="border-t px-4 py-2"
                        ),
                        rx.el.td(bot["status"], class_name="border-t px-4 py-2"),
                        rx.el.td(
                            f"${bot['total_pnl'].to_string()}",
                            class_name="border-t px-4 py-2",
                        ),
                        rx.el.td(bot["deals_count"], class_name="border-t px-4 py-2"),
                        class_name="hover:bg-gray-50",
                    ),
                )
            ),
            class_name="w-full text-sm",
        ),
        class_name="bg-white p-6 rounded-xl shadow-md overflow-x-auto",
    )


def analytics_page() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h1(
                "Analytics Dashboard", class_name="text-3xl font-bold text-gray-800"
            ),
            rx.el.button(
                rx.icon("download", class_name="w-4 h-4 mr-2"),
                "Export Deals (CSV)",
                on_click=AnalyticsState.export_deals_csv,
                class_name="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-teal-600 hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500",
            ),
            class_name="flex items-center justify-between mb-6",
        ),
        rx.cond(
            AnalyticsState.is_loading,
            rx.el.div(
                rx.spinner(class_name="text-teal-500"),
                class_name="flex justify-center items-center h-64",
            ),
            rx.cond(
                AnalyticsState.analytics_data,
                rx.el.div(
                    rx.el.div(
                        analytics_stat_card(
                            "Total P/L",
                            AnalyticsState.analytics_data["total_pnl"],
                            "dollar-sign",
                            unit="$",
                        ),
                        analytics_stat_card(
                            "Total Deals",
                            AnalyticsState.analytics_data["total_deals"],
                            "check_check",
                        ),
                        analytics_stat_card(
                            "Win Rate",
                            AnalyticsState.analytics_data["win_rate"],
                            "percent",
                            unit="%",
                        ),
                        analytics_stat_card(
                            "Avg. Deal Duration",
                            AnalyticsState.analytics_data["average_deal_duration"],
                            "clock",
                            unit="min",
                        ),
                        class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6",
                    ),
                    pnl_chart(),
                    bot_performance_table(),
                    class_name="space-y-6",
                ),
                rx.el.div(
                    rx.icon("bar-chart-2", class_name="w-16 h-16 text-gray-300"),
                    rx.el.h2(
                        "No Data Yet",
                        class_name="mt-4 text-xl font-semibold text-gray-700",
                    ),
                    rx.el.p(
                        "Complete some deals to see your analytics.",
                        class_name="mt-1 text-sm text-gray-500",
                    ),
                    class_name="flex flex-col items-center justify-center text-center p-8 bg-white rounded-lg shadow-md",
                ),
            ),
        ),
        on_mount=AnalyticsState.calculate_analytics,
    )