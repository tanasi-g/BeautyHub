from dataclasses import dataclass


@dataclass
class Service:
    id: int
    name: str
    description: str | None
    duration_min: int
    price: float
    is_active: bool
