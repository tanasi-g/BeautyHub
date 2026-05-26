from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class InventoryLine:
    id:           int
    inventory_id: int
    product_id:   int
    product_name: str
    system_qty:   int   # ποσότητα συστήματος κατά την έναρξη
    actual_qty:   int   # ποσότητα που μέτρησε ο διαχειριστής
    deviation:    int   # actual_qty − system_qty


@dataclass
class Inventory:
    id:           int
    status:       str          # 'draft' | 'completed' | 'cancelled'
    inv_type:     str          # 'full' | 'partial'
    filter_kw:    str | None
    created_at:   str
    completed_at: str | None
    lines:        list[InventoryLine] = field(default_factory=list)
