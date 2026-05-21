"""Domain entities for customer email data."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    """A customer email submitted for agent processing."""

    email_id: str
    customer_id: str | None
    order_id: str | None
    message: str
    attachment: str | None
    status: str


@dataclass(frozen=True)
class Customer:
    """A customer who placed one or more orders."""

    customer_id: str
    name: str
    email: str


@dataclass(frozen=True)
class Order:
    """A customer order record."""

    order_id: str
    customer_id: str
    product_id: str
    order_date: str
    promised_delivery_date: str
    actual_delivery_date: str
    status: str
    refunded: bool


@dataclass(frozen=True)
class Product:
    """A product available in the sample data."""

    product_id: str
    name: str
    category: str
    price: float
