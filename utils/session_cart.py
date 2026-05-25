from __future__ import annotations
from dataclasses import dataclass


@dataclass
class CartLine:
    product_id: int
    name: str
    price: float
    quantity: int

    @property
    def subtotal(self) -> float:
        return self.price * self.quantity


class SessionCart:
    _lines: dict[int, CartLine] = {}

    @classmethod
    def add(cls, product_id: int, name: str, price: float, qty: int = 1) -> None:
        if product_id in cls._lines:
            cls._lines[product_id].quantity += qty
        else:
            cls._lines[product_id] = CartLine(product_id, name, price, qty)

    @classmethod
    def remove(cls, product_id: int) -> None:
        cls._lines.pop(product_id, None)

    @classmethod
    def set_quantity(cls, product_id: int, qty: int) -> None:
        if product_id not in cls._lines:
            return
        if qty <= 0:
            cls.remove(product_id)
        else:
            cls._lines[product_id].quantity = qty

    @classmethod
    def get_lines(cls) -> list[CartLine]:
        return list(cls._lines.values())

    @classmethod
    def clear(cls) -> None:
        cls._lines.clear()

    @classmethod
    def total(cls) -> float:
        return sum(line.subtotal for line in cls._lines.values())

    @classmethod
    def count(cls) -> int:
        return sum(line.quantity for line in cls._lines.values())

    @classmethod
    def is_empty(cls) -> bool:
        return not cls._lines
