# CustomerComplaintAgent

## Purpose

This project is a purposely simple Python sample for learning how an AI agent and
an agent harness work together.

> [!WARNING]
> This is an experimental project and should not be considered production-ready.

It is not intended to be a real-life reusable agent framework, production email
system, CRM integration, or complete customer service automation. The code is
small on purpose so the main concepts are visible:

- an agent proposes structured decisions
- a harness owns the loop, validation, tool execution, and state changes
- tools provide controlled access to data and model-backed checks
- deterministic business rules stay outside the LLM
- an LLM-backed agent can use the same harness contract as a deterministic agent

The sample domain is customer email handling. Some emails are complaints about
orders, and others are compliments from happy customers.

## Setup

Create and populate the local development environment:

```powershell
.\scripts\setup-dev.ps1
```

The project expects Python 3.11 and uses a local `.venv` directory.

## Run Checks

Run formatting, linting, type checking, and unit tests:

```powershell
.\scripts\check.ps1
```

## Run The CLI

Handle one email and print the final run result as JSON:

```powershell
.\.venv\Scripts\python.exe -m customer_complaint_agent --email-id E001
```

The CLI also accepts `--email_id`.

You can edit `data/emails.json` or files under `data/attachments` and rerun the
same command to observe how the final decision changes.

## Run OpenAI Integration Tests

OpenAI-backed integration tests are skipped unless explicitly enabled by the
integration script:

```powershell
.\scripts\check-integration.ps1
```

These tests require `OPENAI_API_KEY` to be available in the environment and may
make paid model calls.

## Project Layout

- `src/customer_complaint_agent/agents`: deterministic and LLM-backed agents
- `src/customer_complaint_agent/harness`: agent loop, validation, tracing, tools
- `src/customer_complaint_agent/runtime`: runtime wiring for this sample app
- `src/customer_complaint_agent/domain`: JSON-backed data access, tools, policy
- `src/customer_complaint_agent/shared`: shared contracts and state types
- `src/customer_complaint_agent/infrastructure`: OpenAI client implementation
- `tests`: unit tests
- `integration_tests`: OpenAI-backed integration tests

## Architecture

The architectural explanation is available in the `ARCHITECTURE.md` document.

## Third-Party Notices

This project has a direct runtime dependency on the `openai` Python package (Apache-2.0). See the package's PyPI license metadata for full license and notice terms.

## License

GNU General Public License v3.0. See the `LICENSE` file for details.
