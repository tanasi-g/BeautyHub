from models.order import Order
from repositories.order_repository import OrderRepository
from services.order_service import OrderService
from services.errors import OrderError, RefundError  # re-exported για τα views
from utils.session_cart import SessionCart, CartLine

__all__ = ["OrderController", "OrderError", "RefundError"]


class OrderController:

    # ---------------------------------------------------------------- cart
    @staticmethod
    def get_cart_lines() -> list[CartLine]:
        return SessionCart.get_lines()

    @staticmethod
    def cart_total() -> float:
        return SessionCart.total()

    @staticmethod
    def cart_is_empty() -> bool:
        return SessionCart.is_empty()

    @staticmethod
    def add_to_cart(product_id: int, name: str, price: float, qty: int = 1) -> None:
        SessionCart.add(product_id, name, price, qty)

    @staticmethod
    def set_quantity(product_id: int, qty: int) -> None:
        SessionCart.set_quantity(product_id, qty)

    @staticmethod
    def clear_cart() -> None:
        SessionCart.clear()

    # ---------------------------------------------------------------- create order (UC 2.9)
    @staticmethod
    def check_stock() -> list[str]:
        return OrderService.check_stock(SessionCart.get_lines())

    @staticmethod
    def create_order(customer_id: int, payment_method: str = 'cod') -> Order:
        return OrderService.create_order(customer_id, payment_method)

    @staticmethod
    def get_orders(customer_id: int) -> list[Order]:
        return OrderRepository.get_by_customer(customer_id)

    # ---------------------------------------------------------------- cancel order (UC 2.10)
    @staticmethod
    def cancel_order(order_id: int, customer_id: int) -> None:
        OrderService.cancel_order(order_id, customer_id)
