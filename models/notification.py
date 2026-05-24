from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Notification:
    id:         int
    user_id:    int
    message:    str
    is_read:    bool
    created_at: str
