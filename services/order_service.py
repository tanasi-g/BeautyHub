"""
OrderService — επιχειρηματική λογική για δημιουργία / ακύρωση παραγγελιών e-shop.
"""
from models.order import Order
from repositories.order_repository import OrderRepository
from repositories.product_repository import ProductRepository
from services.errors import OrderError, RefundError
from utils.session_cart import SessionCart, CartLine


class OrderService:

    # ---------------------------------------------------------------- UC 2.9
    @staticmethod
    def check_stock(lines: list[CartLine]) -> list[str]:
        """Επιστρέφει λίστα προϊόντων με ανεπαρκές απόθεμα. Κενό = όλα OK."""
        problems: list[str] = []
        for line in lines:
            available = ProductRepository.get_stock(line.product_id)
            if available < line.quantity:
                problems.append(
                    f"{line.name}  (ζητάτε {line.quantity}, διαθέσιμα {available})"
                )
        return problems

    @staticmethod
    def create_order(customer_id: int, payment_method: str = 'cod') -> Order:
        lines = SessionCart.get_lines()
        if not lines:
            raise OrderError("Το καλάθι είναι άδειο.")

        problems = OrderService.check_stock(lines)
        if problems:
            raise OrderError("Μη επαρκές απόθεμα για κάποια προϊόντα.")

        total = SessionCart.total()
        order_id = OrderRepository.create(customer_id, total, payment_method)

        OrderRepository.add_items(order_id, [
            {
                "product_id":   line.product_id,
                "product_name": line.name,
                "quantity":     line.quantity,
                "unit_price":   line.price,
            }
            for line in lines
        ])

        for line in lines:
            ProductRepository.reduce_stock(line.product_id, line.quantity)

        SessionCart.clear()

        return OrderRepository.get_by_id(order_id)

    # ---------------------------------------------------------------- UC 2.10
    @staticmethod
    def cancel_order(order_id: int, customer_id: int) -> None:
        # step 3 — έλεγχος αν μπορεί να ακυρωθεί
        order = OrderRepository.get_by_id(order_id)
        if order is None or order.customer_id != customer_id:
            raise OrderError("Η παραγγελία δεν βρέθηκε.")

        if order.status != 'pending':
            # alt flow 1
            raise OrderError(
                "Η παραγγελία δεν μπορεί να ακυρωθεί "
                f"(κατάσταση: {_STATUS_LABELS.get(order.status, order.status)})."
            )

        # step 4 — αλλαγή κατάστασης
        try:
            OrderRepository.cancel(order_id)
        except Exception as exc:
            # alt flow 2
            raise OrderError(f"Αποτυχία αλλαγής κατάστασης: {exc}") from exc

        # step 6 — επιστροφή αποθέματος (πριν το refund για ατομικότητα)
        for item in order.items:
            ProductRepository.restore_stock(item.product_id, item.quantity)

        # step 5 — επιστροφή χρημάτων αν έχει πληρωθεί ηλεκτρονικά
        if order.payment_method == 'card':
            try:
                _process_refund(order)
            except Exception as exc:
                # alt flow 3 — ακύρωση επιτυχής, refund απέτυχε
                raise RefundError(
                    f"Η ακύρωση ολοκληρώθηκε, αλλά η αυτόματη επιστροφή χρημάτων "
                    f"απέτυχε ({exc}). Επικοινωνήστε μαζί μας για επιστροφή {order.total_price:.2f} €."
                ) from exc


def _process_refund(order: Order) -> None:
    """Σε πραγματικό σύστημα: κλήση payment gateway API."""
    pass  # για αντικαταβολή δεν απαιτείται


_STATUS_LABELS = {
    'pending':   'Σε εκκρεμότητα',
    'completed': 'Ολοκληρωμένη',
    'cancelled': 'Ακυρωμένη',
}
