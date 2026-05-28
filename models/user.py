from dataclasses import dataclass


@dataclass
class User:
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    phone: str | None
    role_name: str        # 'admin' | 'employee' | 'customer'
    role_display: str     # 'Διαχειριστής' | 'Υπάλληλος' | 'Πελάτης'
    is_active: bool
    salon_id: int | None = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self) -> bool:
        return self.role_name == "admin"

    @property
    def is_employee(self) -> bool:
        return self.role_name == "employee"

    @property
    def is_customer(self) -> bool:
        return self.role_name == "customer"
