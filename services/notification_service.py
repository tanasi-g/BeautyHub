from __future__ import annotations
from models.notification import Notification
from repositories.notification_repository import NotificationRepository


class NotificationService:

    @staticmethod
    def get_for_user(user_id: int) -> list[Notification]:
        return NotificationRepository.get_by_user(user_id)

    @staticmethod
    def mark_read(notification_id: int) -> None:
        NotificationRepository.mark_read(notification_id)

    @staticmethod
    def mark_all_read(user_id: int) -> None:
        NotificationRepository.mark_all_read(user_id)

    @staticmethod
    def count_unread(user_id: int) -> int:
        return NotificationRepository.count_unread(user_id)
