# Architecture

## Design Goal

This project demonstrates the shape of a small agentic system without using an
agent framework.

The central learning goal is to separate these responsibilities:

- the **agent** decides what should happen next
- the **harness** controls whether and how that decision is applied
- the **runtime** wires concrete dependencies together for this application
- the **domain** contains business data, tools, reducers, and policy rules
- the **shared** package contains contracts used across those boundaries

The sample is intentionally small. It is not trying to become a reusable
framework. The code favors explicit contracts and readable flow over generic
abstractions.

## Package Responsibilities

### `agents`

The `agents` package contains configured decision-making actors.

Current agents include:

- `DeterministicComplaintAgent`
- `DeterministicComplimentAgent`
- `LlmComplaintAgent`

Agents do not execute tools directly and do not mutate goal state directly. They
return structured decisions to the harness.

### `harness`

The `harness` package runs the agent loop.

It is responsible for:

- creating the per-turn `AgentRequest`
- asking the agent for a decision
- validating the decision
- applying accepted state updates
- executing requested tools through `ToolExecutor`
- appending `ToolResult` values to `GoalState`
- applying reducers after tool execution
- enforcing maximum agent turns
- returning a sanitized `RunResult`

The harness does not know the details of customer complaints, compliments, refund
policy, or OpenAI.

### `runtime`

The `runtime` package wires this sample application together.

It chooses:

- the store
- settings
- model clients
- the agent registry
- the agent router
- the tool registry for the selected agent
- the initial goal state

The runtime is application-specific. It is the place where generic harness
contracts meet this particular email-handling sample.

### `domain`

The `domain` package contains business-facing code:

- JSON-backed data access through `Store`
- entity types such as `Email`, `Order`, `Product`, and `Customer`
- tools such as `get_email`, `verify_damaged_product`, and
  `evaluate_refund_policy`
- reducers that extract entity references from tool results
- deterministic refund policy logic

The domain package does not depend on the harness or agents.

### `shared`

The `shared` package contains contracts and value types used across packages:

- `Agent`, `AgentRequest`, `AgentDecision`
- `ActionDecision` and `FinalDecision`
- `GoalState`, `ToolResult`, `Claim`, and `Fact`
- `Tool`, `ToolRegistry`, and `ToolRuntime`
- `ModelClient`, `ModelClientRegistry`, and model call budgeting
- validation and reducer protocols
- shared vocabulary such as completion types and state update operations

## Agent, Harness, And Runtime

The runtime starts the work. It loads enough information to route the email to an
agent, creates the allowed tool registry for that agent, and calls the harness.

The harness then owns the run.

The agent only receives an `AgentRequest`, which contains:

- the current `GoalState`
- the `ToolRegistry` available to that agent

The agent returns an `AgentDecision`. The harness validates and processes that
decision. This design keeps the agent expressive while keeping execution under
harness control.

## Goal State

`GoalState` is harness-owned state for one run.

It contains:

- `goal_id`
- `status`
- `root_entity`
- known entity references
- prior tool results
- recorded claims
- recorded facts
- outputs
- final results

Agents can request state changes through structured `StateUpdate` values, but
the harness decides whether to apply them.

Reducers can also update goal state after tool execution. For example, when a
tool result contains an `Order`, an order reducer can record the order entity
reference in `GoalState.entities`.

## Agent Decisions

Agents return one of two concrete decision types.

### `ActionDecision`

An `ActionDecision` asks the harness to call a tool:

```python
ActionDecision(
    tool_name="get_email",
    arguments={"email_id": "E001"},
    reason="Need to inspect the email.",
)
```

The harness validates the tool request, executes the tool, records the
`ToolResult`, applies reducers, and continues the loop.

### `FinalDecision`

A `FinalDecision` asks the harness to complete the goal:

```python
FinalDecision(
    completion_type="done",
    details={
        "refund_decision": "refund",
        "reason_code": "damaged_cheap_item",
    },
    reason="Refund policy evaluation is complete.",
)
```

The harness validates the decision, records a `GoalResult`, and returns a public
`RunResult`.

## Agent Loop

The harness loop is intentionally simple:

1. Build an `AgentRequest`.
2. Ask the agent to decide.
3. Validate the decision with harness rules.
4. Validate registered tool access when needed.
5. Validate with agent-specific rules.
6. Apply accepted state updates.
7. If final, record the result and stop.
8. If action, execute the tool, record the result, apply reducers, and continue.
9. Stop with failure if `max_agent_turns` is reached.

The loop is the main place where the distinction between the agent and harness is
visible. The agent proposes; the harness controls.

## Tools

Tools are ordinary Python objects implementing the shared `Tool` protocol.

A tool receives:

- a `ToolRequest`, which contains the arguments requested by the agent
- a `ToolRuntime`, which contains harness-provided runtime services such as
  settings and model clients

A tool returns a `ToolResult`.

The harness executes tools through `ToolExecutor`, not by letting the agent call
tools directly.

## Tool Registry

`ToolRegistry` is a typed collection of tools available to one agent run.

The runtime creates the registry after routing the email to an agent. This means
new tools do not automatically become available to every agent. The runtime must
explicitly include a tool in the selected agent's registry.

## Reducers

Reducers update harness-owned state from tool results.

For example:

- `EmailEntityReducer` records an email reference
- `OrderEntityReducer` records an order reference
- `ProductEntityReducer` records a product reference
- `CustomerEntityReducer` records a customer reference

Reducers are supplied by the agent through `get_state_reducers()`. The harness
applies them after a tool result is appended to `GoalState.tool_results`.

This keeps state mutation controlled by the harness while still letting each
agent choose which domain-specific reductions apply to its workflow.

## State Updates And Validation

An agent decision may include `state_updates`.

Currently supported operations are:

- `add_claim`
- `add_fact`

Harness-level validation checks the shape of state updates. For example,
`add_claim` must include a non-empty `claim_type` and a `data` dictionary.

Agent-level validation checks vocabulary. For example, `SkillStateUpdateRule`
checks that a claim type or fact type is allowed by the agent's skill.

The validation order is deliberate:

1. generic harness rules
2. registered tool rule
3. agent-specific rules

If harness validation fails, agent-specific validation is not run.

## Skills

An `AgentSkill` packages LLM-facing guidance and vocabulary for an agent
capability.

A skill can define:

- the goal
- agent-specific instructions
- allowed claim types
- allowed fact types
- final detail fields and allowed values

The LLM prompt builder uses the skill to explain what the model should do. The
agent's validation rules use the same skill to reject unsupported state update
vocabulary.

This keeps prompt guidance and validation vocabulary aligned.

## Deterministic Business Rules

Refund policy is implemented in the domain package, not inside the harness and
not as free-form LLM reasoning.

The refund policy is represented by:

- `RefundFacts`
- `RefundDecision`
- `RefundPolicy`
- `EvaluateRefundPolicyTool`

The complaint agent gathers the facts needed by the policy and calls the policy
tool. The final refund decision comes from deterministic domain logic.

This demonstrates an important agentic pattern: not every step needs an LLM.

## Model Client Boundary

OpenAI-specific code is isolated behind the shared `ModelClient` protocol.

The runtime provides a `ModelClientRegistry`. Agents and tools request model
clients by capability, such as text or vision, rather than constructing OpenAI
clients directly.

Paid model calls are controlled by `ModelCallBudget` and `BudgetedModelClient`.

Unit tests use fake model clients. Integration tests use the real OpenAI client
and are guarded by `check-integration.ps1`.

## Deterministic And LLM Agents

The deterministic complaint agent and the LLM complaint agent use the same
harness contract.

Both return:

- `ActionDecision`
- `FinalDecision`
- optional `state_updates`

The harness does not need to know whether a decision came from deterministic
Python code or an LLM-backed agent. This is the main proof that the harness is
properly separated from agent implementation details.

## Testing Strategy

The project uses several layers of testing:

- domain unit tests for store, tools, reducers, and refund policy
- harness unit tests for validation, tool execution, and agent loop behavior
- agent unit tests for deterministic and LLM-backed decisions
- runtime tests for end-to-end email handling with fake model clients
- infrastructure tests for OpenAI response parsing
- integration tests for real OpenAI text and vision calls

Normal checks run with:

```powershell
.\scripts\check.ps1
```

OpenAI integration tests run with:

```powershell
.\scripts\check-integration.ps1
```

The integration script enables `RUN_OPENAI_INTEGRATION_TESTS` only for that run.
