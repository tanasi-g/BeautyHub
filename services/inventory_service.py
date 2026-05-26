from __future__ import annotations
from models.inventory import Inventory
from repositories.inventory_repository import InventoryRepository
from repositories.product_repository import ProductRepository
from services.errors import InventoryError


class InventoryService:

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def _collect_products(filter_kw: str | None) -> list[dict]:
        """Επιστρέφει ενεργά προϊόντα που πληρούν το κριτήριο (ή όλα αν None)."""
        products = [p for p in ProductRepository.get_all() if p.is_active]
        if filter_kw:
            kw = filter_kw.strip().lower()
            products = [
                p for p in products
                if kw in p.name.lower() or kw in (p.description or "").lower()
            ]
        return [{"id": p.id, "name": p.name, "stock": p.stock} for p in products]

    @staticmethod
    def _cancel_any_draft() -> None:
        draft = InventoryRepository.get_draft()
        if draft:
            InventoryRepository.cancel(draft.id)

    # ---------------------------------------------------------------- start
    @staticmethod
    def start_full_inventory() -> Inventory:
        """Βασική ροή βήμα 2 — πλήρης απογραφή όλων των ενεργών προϊόντων."""
        products = InventoryService._collect_products(None)
        if not products:
            raise InventoryError("Δεν βρέθηκαν προϊόντα στην αποθήκη.")
        InventoryService._cancel_any_draft()
        inv_id = InventoryRepository.create("full", None)
        lines  = InventoryRepository.add_lines(inv_id, products)
        return InventoryRepository.get_by_id(inv_id)

    @staticmethod
    def start_partial_inventory(filter_kw: str) -> Inventory:
        """Εναλλακτική ροή 1 — μερική απογραφή με κριτήριο λέξης-κλειδί."""
        if not filter_kw.strip():
            raise InventoryError("Εισάγετε κριτήριο αναζήτησης.")
        products = InventoryService._collect_products(filter_kw)
        if not products:
            raise InventoryError(
                f"Δεν βρέθηκαν προϊόντα για το κριτήριο «{filter_kw.strip()}»."
            )
        InventoryService._cancel_any_draft()
        inv_id = InventoryRepository.create("partial", filter_kw.strip())
        InventoryRepository.add_lines(inv_id, products)
        return InventoryRepository.get_by_id(inv_id)

    # ---------------------------------------------------------------- progress
    @staticmethod
    def save_draft(inv_id: int, actual_qtys: dict[int, int]) -> None:
        """Εναλλακτική ροή 2 — προσωρινή αποθήκευση χωρίς ενημέρωση stocks."""
        InventoryRepository.update_lines(inv_id, actual_qtys)
        # status παραμένει 'draft'

    @staticmethod
    def complete_inventory(inv_id: int, actual_qtys: dict[int, int]) -> Inventory:
        """Βασική ροή βήματα 7–9 — ολοκλήρωση και ενημέρωση stocks."""
        InventoryRepository.update_lines(inv_id, actual_qtys)
        InventoryRepository.finalize(inv_id)
        return InventoryRepository.get_by_id(inv_id)

    @staticmethod
    def cancel_inventory(inv_id: int) -> None:
        """Εναλλακτική ροή 3 — ακύρωση χωρίς ενημέρωση stocks."""
        InventoryRepository.cancel(inv_id)

    # ---------------------------------------------------------------- query
    @staticmethod
    def get_all() -> list[Inventory]:
        return InventoryRepository.get_all()

    @staticmethod
    def get_draft() -> Inventory | None:
        return InventoryRepository.get_draft()
