from __future__ import annotations
from dataclasses import dataclass


@dataclass
class SalonReview:
    id:             int
    appointment_id: int
    customer_id:    int
    salon_id:       int
    rating:         int         # 1 – 5
    comment:        str | None
    created_at:     str
