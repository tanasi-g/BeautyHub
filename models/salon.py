from dataclasses import dataclass


@dataclass
class Salon:
    id: int
    name: str
    address: str
    city: str
    phone: str | None
    email: str | None
    is_active: bool
    owner_id: int | None = None
    owner_name: str | None = None
