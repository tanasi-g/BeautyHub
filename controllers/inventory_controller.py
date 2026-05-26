from __future__ import annotations
from models.inventory import Inventory
from services.inventory_service import InventoryService
from services.errors import InventoryError  # re-exported για τα views

__all__ = ["InventoryController", "InventoryError"]


class InventoryController:

    @staticmethod
    def start_full_inventory() -> Inventory:
        return InventoryService.start_full_inventory()

    @staticmethod
    def start_partial_inventory(filter_kw: str) -> Inventory:
        return InventoryService.start_partial_inventory(filter_kw)

    @staticmethod
    def save_draft(inv_id: int, actual_qtys: dict[int, int]) -> None:
        InventoryService.save_draft(inv_id, actual_qtys)

    @staticmethod
    def complete_inventory(inv_id: int, actual_qtys: dict[int, int]) -> Inventory:
        return InventoryService.complete_inventory(inv_id, actual_qtys)

    @staticmethod
    def cancel_inventory(inv_id: int) -> None:
        InventoryService.cancel_inventory(inv_id)

    @staticmethod
    def get_all() -> list[Inventory]:
        return InventoryService.get_all()

    @staticmethod
    def get_draft() -> Inventory | None:
        return InventoryService.get_draft()
