from dataclasses import dataclass, field


@dataclass
class OrderItem:
    product_id: int
    product_name: str
    quantity: int
    unit_price: float

    @property
    def subtotal(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class Order:
    id: int
    customer_id: int
    total_price: float
    status: str
    payment_method: str
    created_at: str
    items: list[OrderItem] = field(default_factory=list)
