from dataclasses import dataclass


@dataclass
class AppointmentDetail:
    id: int
    service_id: int        # needed for review creation
    service_name: str
    duration_min: int
    price: float
    employee_name: str
    employee_id: int
    scheduled_at: str  # "YYYY-MM-DD HH:MM"
    status: str
    notes: str | None
    salon_id: int | None = None
    salon_name: str | None = None


@dataclass
class EmployeeAppointmentDetail:
    id: int
    service_name: str
    duration_min: int
    price: float
    customer_name: str
    customer_id: int
    scheduled_at: str
    status: str
    notes: str | None
