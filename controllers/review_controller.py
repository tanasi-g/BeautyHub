from __future__ import annotations
from services.review_service import ReviewService
from services.errors import ReviewError

__all__ = ["ReviewController", "ReviewError"]


class ReviewController:

    @staticmethod
    def submit(
        appointment_id: int,
        customer_id: int,
        employee_id: int,
        service_id: int,
        service_name: str,
        rating: int | None,
        comment: str | None,
        salon_id: int | None = None,
        salon_rating: int | None = None,
        salon_comment: str | None = None,
        salon_name: str | None = None,
    ) -> None:
        ReviewService.submit(
            appointment_id=appointment_id,
            customer_id=customer_id,
            employee_id=employee_id,
            service_id=service_id,
            service_name=service_name,
            rating=rating,
            comment=comment,
            salon_id=salon_id,
            salon_rating=salon_rating,
            salon_comment=salon_comment,
            salon_name=salon_name,
        )

    @staticmethod
    def exists_for_appointment(appointment_id: int) -> bool:
        return ReviewService.exists_for_appointment(appointment_id)

    @staticmethod
    def salon_exists_for_appointment(appointment_id: int) -> bool:
        return ReviewService.salon_exists_for_appointment(appointment_id)
