# src/app/main.py

"""
Application entry point for the Gmail AI Agent.

Responsibilities:
- Initialize the database schema (init_db).
- Build the LangGraph app (build_app).
- Provide a simple CLI-style entry to run the agent once
  with a given user instruction.
"""

import uuid

from database.init_db import init_db
from src.graph.build_graph import build_app
from src.graph.state_types import AgentState


def run_once(user_input: str) -> None:
    """
    Run the Gmail AI Agent workflow once for a single user instruction.

    Args:
        user_input: The natural language instruction for the agent,
                    e.g. "Process my inbox" or
                    "Give me a daily summary of important emails".
    """
    # Ensure database tables are created
    init_db()

    # Build the LangGraph app (with Redis checkpointer attached)
    app = build_app()

    # In LangGraph, "thread_id" is used to identify a workflow thread.
    # For now, generate a random UUID per run.
    thread_id = f"session:{uuid.uuid4()}"

    # Initial workflow state
    initial_state: AgentState = {
        "raw_input": user_input,
    }

    # Invoke the graph
    result_state = app.invoke(
        initial_state,
        config={
            "configurable": {
                "thread_id": thread_id,
            }
        },
    )

    # Extract and print result + log for debugging/demo
    print("\n=== FINAL RESULT ===")
    print(result_state.get("result"))

    print("\n=== WORKFLOW LOG ===")
    log = result_state.get("log") or []
    for line in log:
        print(f"- {line}")


if __name__ == "__main__":
    # Simple demo instruction.
    # Later you can replace this with argparse/CLI or an API layer.
    demo_input = "Process my inbox and reply to important emails."
    run_once(demo_input)
