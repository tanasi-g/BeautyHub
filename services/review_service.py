from __future__ import annotations
from repositories.review_repository import ReviewRepository
from repositories.salon_review_repository import SalonReviewRepository
from repositories.appointment_repository import AppointmentRepository
from repositories.notification_repository import NotificationRepository
from services.errors import ReviewError


class ReviewService:

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
        """Υποβολή αξιολόγησης κομμωτή ή/και κομμωτηρίου."""

        # έλεγχος ότι το ραντεβού έχει ολοκληρωθεί
        appts = AppointmentRepository.get_by_customer(customer_id)
        appt  = next((a for a in appts if a.id == appointment_id), None)
        if not appt:
            raise ReviewError("Το ραντεβού δεν βρέθηκε.")
        if appt.status != "done":
            raise ReviewError(
                "Μπορείτε να αξιολογήσετε μόνο ολοκληρωμένα ραντεβού."
            )

        emp_already   = ReviewRepository.exists_for_appointment(appointment_id)
        salon_already = SalonReviewRepository.exists_for_appointment(appointment_id)

        wants_emp   = rating is not None
        wants_salon = salon_rating is not None and salon_id is not None

        if not wants_emp and not wants_salon:
            raise ReviewError(
                "Επιλέξτε τουλάχιστον μία βαθμολογία (κομμωτή ή κομμωτηρίου)."
            )

        if wants_emp and emp_already:
            raise ReviewError("Έχετε ήδη αξιολογήσει τον κομμωτή για αυτό το ραντεβού.")
        if wants_salon and salon_already:
            raise ReviewError("Έχετε ήδη αξιολογήσει το κομμωτήριο για αυτό το ραντεβού.")

        if wants_emp and not (1 <= rating <= 5):
            raise ReviewError("Επιλέξτε βαθμολογία κομμωτή από 1 έως 5 αστέρια.")
        if wants_salon and not (1 <= salon_rating <= 5):
            raise ReviewError("Επιλέξτε βαθμολογία κομμωτηρίου από 1 έως 5 αστέρια.")

        if wants_emp:
            ReviewRepository.create(
                appointment_id=appointment_id,
                customer_id=customer_id,
                employee_id=employee_id,
                service_id=service_id,
                rating=rating,
                comment=comment or None,
            )

            stars = "★" * rating + "☆" * (5 - rating)
            NotificationRepository.create(
                employee_id,
                f"Νέα αξιολόγηση για «{service_name}»: {stars} ({rating}/5)"
                + (f" — {comment.strip()}" if comment and comment.strip() else ""),
            )

        if wants_salon:
            SalonReviewRepository.create(
                appointment_id=appointment_id,
                customer_id=customer_id,
                salon_id=salon_id,
                rating=salon_rating,
                comment=salon_comment or None,
            )

            stars = "★" * salon_rating + "☆" * (5 - salon_rating)
            label = salon_name or "το κομμωτήριο"
            note  = (
                f"Νέα αξιολόγηση για «{label}»: {stars} ({salon_rating}/5)"
                + (f" — {salon_comment.strip()}"
                   if salon_comment and salon_comment.strip() else "")
            )
            # ειδοποίηση στον ιδιοκτήτη του κομμωτηρίου, αν υπάρχει
            from repositories.salon_repository import SalonRepository
            salon = SalonRepository.get_by_id(salon_id)
            if salon and getattr(salon, "owner_id", None):
                NotificationRepository.create(salon.owner_id, note)

    @staticmethod
    def exists_for_appointment(appointment_id: int) -> bool:
        return ReviewRepository.exists_for_appointment(appointment_id)

    @staticmethod
    def salon_exists_for_appointment(appointment_id: int) -> bool:
        return SalonReviewRepository.exists_for_appointment(appointment_id)
