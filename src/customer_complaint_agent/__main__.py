"""Run the customer email agent as a Python module."""

from customer_complaint_agent.cli import main

if __name__ == "__main__":
    exit_code = main()
    raise SystemExit(exit_code)
