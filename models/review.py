from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Review:
    id:             int
    appointment_id: int
    customer_id:    int
    employee_id:    int
    service_id:     int
    rating:         int         # 1 – 5
    comment:        str | None
    created_at:     str
