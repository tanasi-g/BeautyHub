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
        rating: int,
        comment: str | None,
    ) -> None:
        ReviewService.submit(
            appointment_id=appointment_id,
            customer_id=customer_id,
            employee_id=employee_id,
            service_id=service_id,
            service_name=service_name,
            rating=rating,
            comment=comment,
        )

    @staticmethod
    def exists_for_appointment(appointment_id: int) -> bool:
        return ReviewService.exists_for_appointment(appointment_id)
