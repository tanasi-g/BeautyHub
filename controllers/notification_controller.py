from __future__ import annotations
from models.notification import Notification
from services.notification_service import NotificationService

__all__ = ["NotificationController"]


class NotificationController:

    @staticmethod
    def get_for_user(user_id: int) -> list[Notification]:
        return NotificationService.get_for_user(user_id)

    @staticmethod
    def mark_read(notification_id: int) -> None:
        NotificationService.mark_read(notification_id)

    @staticmethod
    def mark_all_read(user_id: int) -> None:
        NotificationService.mark_all_read(user_id)

    @staticmethod
    def count_unread(user_id: int) -> int:
        return NotificationService.count_unread(user_id)
