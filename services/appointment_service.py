from __future__ import annotations
from datetime import datetime, timedelta

from models.appointment import AppointmentDetail, EmployeeAppointmentDetail
from models.service import Service
from repositories.appointment_repository import AppointmentRepository
from repositories.notification_repository import NotificationRepository
from repositories.service_repository import ServiceRepository
from services.errors import AppointmentError

_WORK_START = 9   # 09:00
_WORK_END   = 18  # 18:00 (last slot must finish by 18:00)
_SLOT_MIN   = 30  # minutes between slot starts


class AppointmentService:

    @staticmethod
    def get_active_services() -> list[Service]:
        return [s for s in ServiceRepository.get_all() if s.is_active]

    @staticmethod
    def get_employees() -> list[dict]:
        """Returns all active employees + the «any» sentinel at the front."""
        employees = AppointmentRepository.get_all_employees()
        return [{"id": None, "name": "Οποιοσδήποτε διαθέσιμος"}] + employees

    @staticmethod
    def get_available_slots(
        date_str: str,
        service_id: int,
        employee_id: int | None,
    ) -> list[dict]:
        """
        Returns a list of dicts {time_str, employee_id, employee_name} for slots
        that are free on the given date for the given service/employee.
        date_str: "YYYY-MM-DD"
        employee_id=None means «any available».
        """
        service = ServiceRepository.get_by_id(service_id)
        if not service:
            raise AppointmentError("Η υπηρεσία δεν βρέθηκε.")

        employees: list[dict]
        if employee_id is not None:
            emp_rows = AppointmentRepository.get_all_employees()
            match = next((e for e in emp_rows if e["id"] == employee_id), None)
            if not match:
                raise AppointmentError("Ο υπάλληλος δεν βρέθηκε.")
            employees = [match]
        else:
            employees = AppointmentRepository.get_all_employees()

        available: list[dict] = []
        slot_start = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=_WORK_START, minute=0, second=0
        )
        work_end = slot_start.replace(hour=_WORK_END)

        while slot_start + timedelta(minutes=service.duration_min) <= work_end:
            slot_end = slot_start + timedelta(minutes=service.duration_min)
            start_iso = slot_start.strftime("%Y-%m-%d %H:%M")
            end_iso   = slot_end.strftime("%Y-%m-%d %H:%M")

            for emp in employees:
                if not AppointmentRepository.has_overlap(emp["id"], start_iso, end_iso):
                    available.append({
                        "time_str":     slot_start.strftime("%H:%M"),
                        "start_iso":    start_iso,
                        "employee_id":  emp["id"],
                        "employee_name": emp["name"],
                    })
                    break  # first free employee per slot is enough when «any»

            slot_start += timedelta(minutes=_SLOT_MIN)

        return available

    @staticmethod
    def create_appointment(
        customer_id: int,
        employee_id: int,
        service_id: int,
        start_iso: str,
        notes: str | None = None,
    ) -> int:
        service = ServiceRepository.get_by_id(service_id)
        if not service:
            raise AppointmentError("Η υπηρεσία δεν βρέθηκε.")

        end_dt  = datetime.strptime(start_iso, "%Y-%m-%d %H:%M") + timedelta(minutes=service.duration_min)
        end_iso = end_dt.strftime("%Y-%m-%d %H:%M")

        if AppointmentRepository.has_overlap(employee_id, start_iso, end_iso):
            raise AppointmentError(
                "Η επιλεγμένη ώρα δεν είναι πλέον διαθέσιμη. "
                "Παρακαλώ επιλέξτε άλλη ώρα."
            )

        appt_id = AppointmentRepository.create(
            customer_id=customer_id,
            employee_id=employee_id,
            service_id=service_id,
            scheduled_at=start_iso,
            notes=notes,
        )

        # step 9 — notify the customer
        NotificationRepository.create(
            customer_id,
            f"Το ραντεβού σας για «{service.name}» "
            f"την {start_iso} καταχωρήθηκε επιτυχώς.",
        )

        return appt_id

    @staticmethod
    def count() -> int:
        return AppointmentRepository.count()

    @staticmethod
    def get_all() -> list[dict]:
        return AppointmentRepository.get_all()

    @staticmethod
    def get_by_customer(customer_id: int) -> list[AppointmentDetail]:
        return AppointmentRepository.get_by_customer(customer_id)

    # ---------------------------------------------------------------- employee actions (UC 2.3)

    @staticmethod
    def get_by_employee(employee_id: int) -> list[EmployeeAppointmentDetail]:
        return AppointmentRepository.get_by_employee(employee_id)

    @staticmethod
    def accept_appointment(appt_id: int, employee_id: int) -> None:
        appts = AppointmentRepository.get_by_employee(employee_id)
        appt = next((a for a in appts if a.id == appt_id), None)
        if not appt:
            raise AppointmentError("Το ραντεβού δεν βρέθηκε.")
        if appt.status != "pending":
            raise AppointmentError("Μόνο εκκρεμείς αιτήσεις μπορούν να γίνουν αποδεκτές.")

        AppointmentRepository.set_status(appt_id, "confirmed")

        NotificationRepository.create(
            appt.customer_id,
            f"Το ραντεβού σας για «{appt.service_name}» "
            f"την {appt.scheduled_at} επιβεβαιώθηκε από τον κομμωτή.",
        )

    @staticmethod
    def reject_appointment(appt_id: int, employee_id: int, reason: str) -> None:
        appts = AppointmentRepository.get_by_employee(employee_id)
        appt = next((a for a in appts if a.id == appt_id), None)
        if not appt:
            raise AppointmentError("Το ραντεβού δεν βρέθηκε.")
        if appt.status not in ("pending", "confirmed"):
            raise AppointmentError("Αυτό το ραντεβού δεν μπορεί να απορριφθεί.")

        AppointmentRepository.set_status(appt_id, "cancelled")

        msg = f"Το ραντεβού σας για «{appt.service_name}» την {appt.scheduled_at} απορρίφθηκε."
        if reason.strip():
            msg += f" Λόγος: {reason.strip()}"
        NotificationRepository.create(appt.customer_id, msg)

    @staticmethod
    def get_available_slots_for_reschedule(
        date_str: str,
        employee_id: int,
        duration_min: int,
        exclude_appt_id: int,
    ) -> list[dict]:
        """Like get_available_slots but for a fixed employee and excludes the appointment being rescheduled."""
        slot_start = datetime.strptime(date_str, "%Y-%m-%d").replace(
            hour=_WORK_START, minute=0, second=0
        )
        work_end = slot_start.replace(hour=_WORK_END)
        available: list[dict] = []
        while slot_start + timedelta(minutes=duration_min) <= work_end:
            slot_end  = slot_start + timedelta(minutes=duration_min)
            start_iso = slot_start.strftime("%Y-%m-%d %H:%M")
            end_iso   = slot_end.strftime("%Y-%m-%d %H:%M")
            if not AppointmentRepository.has_overlap_excluding(employee_id, start_iso, end_iso, exclude_appt_id):
                available.append({
                    "time_str":     slot_start.strftime("%H:%M"),
                    "start_iso":    start_iso,
                    "employee_id":  employee_id,
                    "employee_name": "",
                })
            slot_start += timedelta(minutes=_SLOT_MIN)
        return available

    @staticmethod
    def customer_cancel_appointment(appt_id: int, customer_id: int) -> None:
        appts = AppointmentRepository.get_by_customer(customer_id)
        appt  = next((a for a in appts if a.id == appt_id), None)
        if not appt:
            raise AppointmentError("Το ραντεβού δεν βρέθηκε.")
        if appt.status not in ("pending", "confirmed"):
            raise AppointmentError("Αυτό το ραντεβού δεν μπορεί να ακυρωθεί.")
        AppointmentRepository.set_status(appt_id, "cancelled")
        NotificationRepository.create(
            appt.employee_id,
            f"Ο πελάτης ακύρωσε το ραντεβού για «{appt.service_name}» "
            f"την {appt.scheduled_at}.",
        )

    @staticmethod
    def customer_reschedule_appointment(
        appt_id: int, customer_id: int, new_scheduled_at: str
    ) -> None:
        appts = AppointmentRepository.get_by_customer(customer_id)
        appt  = next((a for a in appts if a.id == appt_id), None)
        if not appt:
            raise AppointmentError("Το ραντεβού δεν βρέθηκε.")
        if appt.status not in ("pending", "confirmed"):
            raise AppointmentError("Αυτό το ραντεβού δεν μπορεί να αναπρογραμματιστεί.")
        try:
            new_dt = datetime.strptime(new_scheduled_at, "%Y-%m-%d %H:%M")
        except ValueError:
            raise AppointmentError("Μη έγκυρη μορφή ημερομηνίας/ώρας.")
        end_iso = (new_dt + timedelta(minutes=appt.duration_min)).strftime("%Y-%m-%d %H:%M")
        if AppointmentRepository.has_overlap_excluding(appt.employee_id, new_scheduled_at, end_iso, appt_id):
            raise AppointmentError(
                "Η επιλεγμένη ώρα δεν είναι πλέον διαθέσιμη. "
                "Παρακαλώ επιλέξτε άλλη ώρα."
            )
        AppointmentRepository.reschedule(appt_id, new_scheduled_at)
        NotificationRepository.create(
            appt.employee_id,
            f"Ο πελάτης ζήτησε αλλαγή ραντεβού για «{appt.service_name}» "
            f"στις {new_scheduled_at}. Παρακαλώ επιβεβαιώστε.",
        )

    @staticmethod
    def complete_appointment(appt_id: int, employee_id: int) -> None:
        appts = AppointmentRepository.get_by_employee(employee_id)
        appt  = next((a for a in appts if a.id == appt_id), None)
        if not appt:
            raise AppointmentError("Το ραντεβού δεν βρέθηκε.")
        if appt.status != "confirmed":
            raise AppointmentError(
                "Μόνο επιβεβαιωμένα ραντεβού μπορούν να ολοκληρωθούν."
            )

        AppointmentRepository.set_status(appt_id, "done")

        NotificationRepository.create(
            appt.customer_id,
            f"Το ραντεβού σας για «{appt.service_name}» ολοκληρώθηκε. "
            f"Μπορείτε τώρα να αξιολογήσετε την υπηρεσία!",
        )

    @staticmethod
    def reschedule_appointment(
        appt_id: int, employee_id: int, new_scheduled_at: str
    ) -> None:
        appts = AppointmentRepository.get_by_employee(employee_id)
        appt = next((a for a in appts if a.id == appt_id), None)
        if not appt:
            raise AppointmentError("Το ραντεβού δεν βρέθηκε.")
        if appt.status not in ("pending", "confirmed"):
            raise AppointmentError("Αυτό το ραντεβού δεν μπορεί να αναπρογραμματιστεί.")

        # validate format
        try:
            new_dt = datetime.strptime(new_scheduled_at, "%Y-%m-%d %H:%M")
        except ValueError:
            raise AppointmentError("Μη έγκυρη μορφή ημερομηνίας/ώρας.")

        end_iso = (new_dt + timedelta(minutes=appt.duration_min)).strftime("%Y-%m-%d %H:%M")

        if AppointmentRepository.has_overlap_excluding(employee_id, new_scheduled_at, end_iso, appt_id):
            raise AppointmentError(
                "Η νέα ώρα επικαλύπτεται με άλλο ραντεβού σας. "
                "Παρακαλώ επιλέξτε άλλη ώρα."
            )

        AppointmentRepository.reschedule(appt_id, new_scheduled_at)

        NotificationRepository.create(
            appt.customer_id,
            f"Το ραντεβού σας για «{appt.service_name}» "
            f"μετατέθηκε στις {new_scheduled_at}. "
            f"Παρακαλώ επιβεβαιώστε ή απορρίψτε την αλλαγή.",
        )
