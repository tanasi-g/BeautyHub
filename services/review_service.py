from __future__ import annotations
from repositories.review_repository import ReviewRepository
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
        rating: int,
        comment: str | None,
    ) -> None:
        """Βασική ροή βήματα 5–9."""

        # βήμα 2 — έλεγχος ότι το ραντεβού έχει ολοκληρωθεί (alt flow 1)
        appts = AppointmentRepository.get_by_customer(customer_id)
        appt  = next((a for a in appts if a.id == appointment_id), None)
        if not appt:
            raise ReviewError("Το ραντεβού δεν βρέθηκε.")
        if appt.status != "done":
            raise ReviewError(
                "Μπορείτε να αξιολογήσετε μόνο ολοκληρωμένα ραντεβού."
            )

        # έλεγχος διπλής αξιολόγησης
        if ReviewRepository.exists_for_appointment(appointment_id):
            raise ReviewError("Έχετε ήδη αξιολογήσει αυτό το ραντεβού.")

        # βήμα 5 — εγκυρότητα βαθμολογίας (alt flow 3)
        if not (1 <= rating <= 5):
            raise ReviewError("Επιλέξτε βαθμολογία από 1 έως 5 αστέρια.")

        # βήματα 8–9 — δημιουργία αξιολόγησης + ειδοποίηση
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

    @staticmethod
    def exists_for_appointment(appointment_id: int) -> bool:
        return ReviewRepository.exists_for_appointment(appointment_id)
