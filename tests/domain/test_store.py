from customer_complaint_agent.domain.store import Store


def test_get_email_returns_email_by_id() -> None:
    store = Store()

    email = store.get_email("E001")

    assert email is not None
    assert email.email_id == "E001"


def test_get_order_returns_order_by_id() -> None:
    store = Store()

    order = store.get_order("O001")

    assert order is not None
    assert order.order_id == "O001"


def test_get_product_returns_product_by_id() -> None:
    store = Store()

    product = store.get_product("P001")

    assert product is not None
    assert product.product_id == "P001"


def test_get_customer_returns_customer_by_id() -> None:
    store = Store()

    customer = store.get_customer("C001")

    assert customer is not None
    assert customer.customer_id == "C001"
