from __future__ import annotations
from models.appointment import AppointmentDetail, EmployeeAppointmentDetail
from models.service import Service
from services.appointment_service import AppointmentService
from services.errors import AppointmentError  

__all__ = ["AppointmentController", "AppointmentError"]


class AppointmentController:

    @staticmethod
    def get_active_services() -> list[Service]:
        return AppointmentService.get_active_services()

    @staticmethod
    def get_employees() -> list[dict]:
        return AppointmentService.get_employees()

    @staticmethod
    def get_available_slots(
        date_str: str,
        service_id: int,
        employee_id: int | None,
    ) -> list[dict]:
        return AppointmentService.get_available_slots(date_str, service_id, employee_id)

    @staticmethod
    def create_appointment(
        customer_id: int,
        employee_id: int,
        service_id: int,
        start_iso: str,
        notes: str | None = None,
    ) -> int:
        return AppointmentService.create_appointment(
            customer_id, employee_id, service_id, start_iso, notes
        )

    @staticmethod
    def count() -> int:
        return AppointmentService.count()

    @staticmethod
    def get_all() -> list[dict]:
        return AppointmentService.get_all()

    @staticmethod
    def get_by_customer(customer_id: int) -> list[AppointmentDetail]:
        return AppointmentService.get_by_customer(customer_id)

    # ---------------------------------------------------------------- UC 2.3 — employee actions

    @staticmethod
    def get_by_employee(employee_id: int) -> list[EmployeeAppointmentDetail]:
        return AppointmentService.get_by_employee(employee_id)

    @staticmethod
    def accept_appointment(appt_id: int, employee_id: int) -> None:
        AppointmentService.accept_appointment(appt_id, employee_id)

    @staticmethod
    def reject_appointment(appt_id: int, employee_id: int, reason: str) -> None:
        AppointmentService.reject_appointment(appt_id, employee_id, reason)

    @staticmethod
    def complete_appointment(appt_id: int, employee_id: int) -> None:
        AppointmentService.complete_appointment(appt_id, employee_id)

    @staticmethod
    def reschedule_appointment(
        appt_id: int, employee_id: int, new_scheduled_at: str
    ) -> None:
        AppointmentService.reschedule_appointment(appt_id, employee_id, new_scheduled_at)

    # ---------------------------------------------------------------- UC 2.12 — customer modification

    @staticmethod
    def get_available_slots_for_reschedule(
        date_str: str, employee_id: int, duration_min: int, exclude_appt_id: int
    ) -> list[dict]:
        return AppointmentService.get_available_slots_for_reschedule(
            date_str, employee_id, duration_min, exclude_appt_id
        )

    @staticmethod
    def customer_cancel_appointment(appt_id: int, customer_id: int) -> None:
        AppointmentService.customer_cancel_appointment(appt_id, customer_id)

    @staticmethod
    def customer_reschedule_appointment(
        appt_id: int, customer_id: int, new_scheduled_at: str
    ) -> None:
        AppointmentService.customer_reschedule_appointment(appt_id, customer_id, new_scheduled_at)
