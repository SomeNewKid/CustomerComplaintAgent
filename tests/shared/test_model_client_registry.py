from customer_complaint_agent.shared.model import (
    BudgetedModelClient,
    ModelCallBudget,
    ModelClientRegistration,
    ModelClientRegistry,
    ModelRequest,
    ModelResponse,
)


class _FakeModelClient:
    def __init__(self, name: str) -> None:
        self.name = name

    def complete(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(data={"client": self.name})


def test_model_client_registry_gets_client_by_name() -> None:
    client = _FakeModelClient("text")
    registry = ModelClientRegistry(
        clients=(
            ModelClientRegistration(
                name="text",
                client=client,
                is_text_enabled=True,
                is_vision_enabled=False,
                is_paid=False,
            ),
        )
    )

    assert registry.get_by_name("text") is client


def test_model_client_registry_returns_none_for_unknown_client_name() -> None:
    registry = ModelClientRegistry(clients=())

    assert registry.get_by_name("missing") is None


def test_model_client_registry_prefers_free_text_client() -> None:
    paid_client = _FakeModelClient("paid")
    free_client = _FakeModelClient("free")
    registry = ModelClientRegistry(
        clients=(
            ModelClientRegistration(
                name="paid",
                client=paid_client,
                is_text_enabled=True,
                is_vision_enabled=False,
                is_paid=True,
            ),
            ModelClientRegistration(
                name="free",
                client=free_client,
                is_text_enabled=True,
                is_vision_enabled=False,
                is_paid=False,
            ),
        )
    )

    assert registry.get_text_client() is free_client


def test_model_client_registry_returns_paid_text_client_when_free_not_preferred() -> (
    None
):
    paid_client = _FakeModelClient("paid")
    free_client = _FakeModelClient("free")
    registry = ModelClientRegistry(
        model_call_budget=ModelCallBudget(max_paid_model_calls=1),
        clients=(
            ModelClientRegistration(
                name="paid",
                client=paid_client,
                is_text_enabled=True,
                is_vision_enabled=False,
                is_paid=True,
            ),
            ModelClientRegistration(
                name="free",
                client=free_client,
                is_text_enabled=True,
                is_vision_enabled=False,
                is_paid=False,
            ),
        ),
    )

    client = registry.get_text_client(prefer_free=False)

    assert isinstance(client, BudgetedModelClient)
    assert client.client is paid_client


def test_model_client_registry_gets_vision_client() -> None:
    text_client = _FakeModelClient("text")
    vision_client = _FakeModelClient("vision")
    registry = ModelClientRegistry(
        model_call_budget=ModelCallBudget(max_paid_model_calls=1),
        clients=(
            ModelClientRegistration(
                name="text",
                client=text_client,
                is_text_enabled=True,
                is_vision_enabled=False,
                is_paid=False,
            ),
            ModelClientRegistration(
                name="vision",
                client=vision_client,
                is_text_enabled=True,
                is_vision_enabled=True,
                is_paid=True,
            ),
        ),
    )

    client = registry.get_vision_client()

    assert isinstance(client, BudgetedModelClient)
    assert client.client is vision_client


def test_model_client_registry_returns_none_when_capability_is_missing() -> None:
    registry = ModelClientRegistry(
        clients=(
            ModelClientRegistration(
                name="text",
                client=_FakeModelClient("text"),
                is_text_enabled=True,
                is_vision_enabled=False,
                is_paid=False,
            ),
        )
    )

    assert registry.get_vision_client() is None


def test_model_client_registry_rejects_duplicate_client_names() -> None:
    client = _FakeModelClient("client")

    try:
        ModelClientRegistry(
            clients=(
                ModelClientRegistration(
                    name="client",
                    client=client,
                    is_text_enabled=True,
                    is_vision_enabled=False,
                    is_paid=False,
                ),
                ModelClientRegistration(
                    name="client",
                    client=client,
                    is_text_enabled=True,
                    is_vision_enabled=True,
                    is_paid=True,
                ),
            )
        )
    except ValueError as error:
        assert str(error) == "Duplicate model client name: client"
    else:
        raise AssertionError(
            "Expected duplicate model client name to raise ValueError."
        )


def test_paid_model_client_records_paid_call() -> None:
    budget = ModelCallBudget(max_paid_model_calls=1)
    client = _FakeModelClient("paid")
    registry = ModelClientRegistry(
        model_call_budget=budget,
        clients=(
            ModelClientRegistration(
                name="paid",
                client=client,
                is_text_enabled=True,
                is_vision_enabled=False,
                is_paid=True,
            ),
        ),
    )
    budgeted_client = registry.get_by_name("paid")

    assert budgeted_client is not None
    response = budgeted_client.complete(_model_request())

    assert response == ModelResponse(data={"client": "paid"})
    assert budget.paid_model_call_count == 1


def test_paid_model_client_raises_error_when_paid_call_limit_is_exceeded() -> None:
    registry = ModelClientRegistry(
        model_call_budget=ModelCallBudget(max_paid_model_calls=0),
        clients=(
            ModelClientRegistration(
                name="paid",
                client=_FakeModelClient("paid"),
                is_text_enabled=True,
                is_vision_enabled=False,
                is_paid=True,
            ),
        ),
    )
    client = registry.get_by_name("paid")

    assert client is not None

    try:
        client.complete(_model_request())
    except RuntimeError as error:
        assert str(error) == "Paid model call limit exceeded."
    else:
        raise AssertionError("Expected paid model call limit to raise RuntimeError.")


def test_paid_model_client_requires_model_call_budget() -> None:
    registry = ModelClientRegistry(
        clients=(
            ModelClientRegistration(
                name="paid",
                client=_FakeModelClient("paid"),
                is_text_enabled=True,
                is_vision_enabled=False,
                is_paid=True,
            ),
        ),
    )

    try:
        registry.get_by_name("paid")
    except RuntimeError as error:
        assert str(error) == "Paid model client requires a model call budget."
    else:
        raise AssertionError("Expected paid model client to require a budget.")


def _model_request() -> ModelRequest:
    return ModelRequest(
        system_prompt="Respond with structured data.",
        user_prompt="Use the fake model.",
        input_data={},
    )
