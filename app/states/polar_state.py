import reflex as rx
import os
import logging
from typing import TypedDict, cast
from polar_sdk import Polar, models
from app.states.auth_state import AuthState, User

logging.basicConfig(level=logging.INFO)


class Subscription(TypedDict):
    id: str
    status: str
    current_period_end: str
    cancel_at_period_end: bool
    product_name: str


class PolarState(rx.State):
    is_loading: bool = False
    subscription_active: bool = False
    current_subscription: models.Subscription | None = None
    polar_products: list[models.Product] = []

    def _get_polar_client(self) -> Polar | None:
        token = os.getenv("POLAR_ACCESS_TOKEN")
        if not token:
            logging.error("POLAR_ACCESS_TOKEN environment variable not set.")
            return None
        return Polar(token=token)

    @rx.var
    def pro_product(self) -> models.Product | None:
        return next((p for p in self.polar_products if p.name == "PRO"), None)

    @rx.var
    def subscription_renewal_date(self) -> str:
        if self.current_subscription and self.current_subscription.current_period_end:
            return self.current_subscription.current_period_end.strftime("%Y-%m-%d")
        return ""

    @rx.event(background=True)
    async def on_load_subscription_status(self):
        async with self:
            auth_state = await self.get_state(AuthState)
            if not auth_state.current_user:
                return
            user_email = auth_state.current_user["email"]
        polar = self._get_polar_client()
        if not polar:
            return
        try:
            async with polar:
                products_response = await polar.products.list(is_recurring=True)
                async with self:
                    self.polar_products = products_response.items or []
                subs_response = await polar.subscriptions.list(
                    customer_email=user_email
                )
                active_sub = next(
                    (
                        s
                        for s in subs_response.items
                        if s.status == models.SubscriptionStatus.ACTIVE
                    ),
                    None,
                )
                async with self:
                    auth_state = await self.get_state(AuthState)
                    if active_sub:
                        self.subscription_active = True
                        self.current_subscription = active_sub
                        if auth_state.current_user["subscription_tier"] != "PRO":
                            auth_state.set_user_tier("PRO")
                    else:
                        self.subscription_active = False
                        self.current_subscription = None
                        if auth_state.current_user["subscription_tier"] != "FREE":
                            auth_state.set_user_tier("FREE")
        except Exception as e:
            logging.exception(f"Error fetching Polar data: {e}")

    @rx.event(background=True)
    async def create_checkout_session(self):
        async with self:
            if self.is_loading:
                return
            self.is_loading = True
        try:
            async with self:
                auth_state = await self.get_state(AuthState)
                user = cast(User, auth_state.current_user)
            polar = self._get_polar_client()
            if not polar or not self.pro_product:
                async with self:
                    self.is_loading = False
                return rx.toast.error("Subscription service is not configured.")
            async with polar:
                checkout_session = await polar.checkout.create(
                    product_id=self.pro_product.id,
                    success_url=f"{self.router.page.full_raw_url}",
                    customer_email=user.get("email"),
                )
                async with self:
                    self.is_loading = False
                return rx.redirect(checkout_session.url)
        except Exception as e:
            logging.exception(f"Error creating checkout session: {e}")
            async with self:
                self.is_loading = False
            return rx.toast.error("Could not create checkout session.")

    @rx.event(background=True)
    async def get_customer_portal_url(self):
        try:
            async with self:
                auth_state = await self.get_state(AuthState)
                user = cast(User, auth_state.current_user)
            polar = self._get_polar_client()
            if not polar or not user.get("email"):
                return rx.toast.error("Service not available.")
            async with polar:
                portal_session = await polar.customer_portal.create(
                    customer_email=user["email"]
                )
                return rx.redirect(portal_session.url)
        except Exception as e:
            logging.exception(f"Error creating customer portal session: {e}")
            return rx.toast.error("Could not open customer portal.")

    @rx.event(background=True)
    async def handle_webhook(self, payload: bytes, headers: dict) -> dict:
        secret = os.getenv("POLAR_WEBHOOK_SECRET")
        if not secret:
            logging.error("POLAR_WEBHOOK_SECRET not set.")
            return {"body": "Webhook secret not configured", "status_code": 500}
        polar = self._get_polar_client()
        if not polar:
            return {"body": "Polar client not configured", "status_code": 500}
        try:
            event = polar.webhooks.parse(payload, headers, secret)
            logging.info(f"Received Polar webhook: {event.type}")
            if (
                event.type == "subscription.created"
                or event.type == "subscription.updated"
            ):
                subscription = cast(models.Subscription, event.payload)
                customer_email = subscription.customer_email
                async with self:
                    auth_state = await self.get_state(AuthState)
                    new_tier: Literal["PRO", "FREE"] = "FREE"
                    if subscription.status == models.SubscriptionStatus.ACTIVE:
                        new_tier = "PRO"
                    auth_state.set_user_tier_by_email(customer_email, new_tier)
                    logging.info(f"Updated user {customer_email} to tier {new_tier}")
            return {"body": "OK", "status_code": 200}
        except Exception as e:
            logging.exception(f"Error processing webhook: {e}")
            return {"body": "Error processing webhook", "status_code": 400}