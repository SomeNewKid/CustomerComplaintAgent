"""In-memory access to customer email sample data."""

import json
from pathlib import Path
from typing import Any, TypeVar

from .entities import Customer, Email, Order, Product

_Record = TypeVar("_Record")


class Store:
    """Lookup facade for customer email sample data."""

    def __init__(self, data_dir: Path | None = None) -> None:
        """Load customer email sample data from JSON files."""
        if data_dir is None:
            data_dir = Path(__file__).resolve().parents[3] / "data"

        self._emails = _load_records(
            data_dir / "emails.json",
            Email,
            "email_id",
        )
        self._customers = _load_records(
            data_dir / "customers.json",
            Customer,
            "customer_id",
        )
        self._orders = _load_records(
            data_dir / "orders.json",
            Order,
            "order_id",
        )
        self._products = _load_records(
            data_dir / "products.json",
            Product,
            "product_id",
        )

    def get_email(self, email_id: str) -> Email | None:
        """Return an email by ID, if one is loaded."""
        return self._emails.get(email_id)

    def get_customer(self, customer_id: str) -> Customer | None:
        """Return a customer by ID, if one is loaded."""
        return self._customers.get(customer_id)

    def get_order(self, order_id: str) -> Order | None:
        """Return an order by ID, if one is loaded."""
        return self._orders.get(order_id)

    def get_product(self, product_id: str) -> Product | None:
        """Return a product by ID, if one is loaded."""
        return self._products.get(product_id)


def _load_records(
    path: Path,
    entity_type: type[_Record],
    id_field: str,
) -> dict[str, _Record]:
    """Load a JSON array into records keyed by ID."""
    with path.open(encoding="utf-8") as data_file:
        rows: list[dict[str, Any]] = json.load(data_file)

    records = [entity_type(**row) for row in rows]
    return {str(getattr(record, id_field)): record for record in records}
