import reflex as rx
from typing import TypedDict, cast
import logging
from app.states.bot_state import BotsState, Bot
from app.states.deal_state import DealState, Deal
import csv
import io
import time


class AnalyticsData(TypedDict):
    total_pnl: float
    total_deals: int
    win_rate: float
    total_volume: float
    average_deal_duration: float
    pnl_history: list[dict[str, float | str]]


class AnalyticsState(rx.State):
    analytics_data: AnalyticsData | None = None
    is_loading: bool = False

    @rx.event(background=True)
    async def calculate_analytics(self):
        async with self:
            self.is_loading = True
        try:
            async with self:
                deal_state = await self.get_state(DealState)
                bots_state = await self.get_state(BotsState)
            completed_deals = [
                deal
                for deal in deal_state.deals.values()
                if deal["status"] == "completed" and deal["close_time"]
            ]
            total_pnl = sum((deal["realized_pnl"] for deal in completed_deals))
            total_deals = len(completed_deals)
            profitable_deals = sum(
                (1 for deal in completed_deals if deal["realized_pnl"] > 0)
            )
            win_rate = profitable_deals / total_deals * 100 if total_deals > 0 else 0.0
            total_volume = sum(
                (
                    deal["base_order"]["price"] * deal["base_order"]["quantity"]
                    + sum(
                        (
                            so["price"] * so["quantity"]
                            for so in deal.get("safety_orders", [])
                        )
                    )
                    for deal in completed_deals
                )
            )
            total_duration = sum(
                (
                    cast(float, deal["close_time"]) - deal["entry_time"]
                    for deal in completed_deals
                )
            )
            average_deal_duration = (
                total_duration / total_deals if total_deals > 0 else 0.0
            )
            pnl_history = sorted(
                [
                    {
                        "date": time.strftime(
                            "%Y-%m-%d", time.gmtime(cast(float, d["close_time"]))
                        ),
                        "pnl": d["realized_pnl"],
                    }
                    for d in completed_deals
                ],
                key=lambda x: x["date"],
            )
            cumulative_pnl_history = []
            cumulative_pnl = 0
            if pnl_history:
                from itertools import groupby

                for date, group in groupby(pnl_history, key=lambda x: x["date"]):
                    daily_pnl = sum((item["pnl"] for item in group))
                    cumulative_pnl += daily_pnl
                    cumulative_pnl_history.append(
                        {"date": date, "pnl": round(cumulative_pnl, 2)}
                    )
            async with self:
                self.analytics_data = {
                    "total_pnl": round(total_pnl, 2),
                    "total_deals": total_deals,
                    "win_rate": round(win_rate, 2),
                    "total_volume": round(total_volume, 2),
                    "average_deal_duration": round(average_deal_duration / 60, 2),
                    "pnl_history": cumulative_pnl_history,
                }
                self.is_loading = False
        except Exception as e:
            logging.exception(f"Error calculating analytics: {e}")
            async with self:
                self.is_loading = False

    @rx.event(background=True)
    async def export_deals_csv(self):
        async with self:
            deal_state = await self.get_state(DealState)
            deals = list(deal_state.deals.values())
        if not deals:
            return rx.toast.info("No deals to export.")
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            ["Deal ID", "Bot ID", "Status", "Entry Time", "Close Time", "Realized PNL"]
        )
        for deal in deals:
            writer.writerow(
                [
                    deal["deal_id"],
                    deal["bot_id"],
                    deal["status"],
                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(deal["entry_time"])),
                    time.strftime(
                        "%Y-%m-%d %H:%M:%S",
                        time.gmtime(cast(float, deal["close_time"])),
                    )
                    if deal["close_time"]
                    else "N/A",
                    deal["realized_pnl"],
                ]
            )
        csv_data = output.getvalue()
        return rx.download(data=csv_data.encode("utf-8"), filename="deals_export.csv")