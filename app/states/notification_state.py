import reflex as rx
from typing import TypedDict, Literal
import time

NotificationType = Literal["info", "success", "warning", "error"]


class Notification(TypedDict):
    id: str
    timestamp: float
    type: NotificationType
    message: str
    is_read: bool


class NotificationState(rx.State):
    notifications: list[Notification] = []

    @rx.var
    def unread_count(self) -> int:
        return sum((1 for n in self.notifications if not n["is_read"]))

    @rx.var
    def recent_notifications(self) -> list[Notification]:
        return sorted(self.notifications, key=lambda n: n["timestamp"], reverse=True)[
            :5
        ]

    @rx.event
    def add_notification(self, message: str, type: NotificationType = "info"):
        new_notification = Notification(
            id=f"notif_{int(time.time() * 1000)}",
            timestamp=time.time(),
            type=type,
            message=message,
            is_read=False,
        )
        self.notifications.insert(0, new_notification)
        if len(self.notifications) > 100:
            self.notifications.pop()

    @rx.event
    def mark_as_read(self, notification_id: str):
        for i, n in enumerate(self.notifications):
            if n["id"] == notification_id:
                self.notifications[i]["is_read"] = True
                break

    @rx.event
    def mark_all_as_read(self):
        for i in range(len(self.notifications)):
            self.notifications[i]["is_read"] = True

    @rx.event
    def clear_all_notifications(self):
        self.notifications = []