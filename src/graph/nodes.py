# src/graph/nodes.py

"""
LangGraph workflow nodes for the Gmail AI Agent.

Nodes:
1) entry_node
   - Initialize state.
   - Create a workflow run in the database.

2) task_router_node
   - Decide which task to run:
     - "process_inbox"
     - "daily_summary"

3) process_inbox_node
   - Call the Groq-based gmail_agent to process the inbox.

4) daily_summary_node
   - Call the Groq-based gmail_agent to generate a daily summary.
"""

from typing import cast

from langchain_core.messages import HumanMessage

from src.agents.gmail_agent import gmail_agent
from src.graph.state_types import AgentState
from database.repositories import (
    create_workflow_run,
    update_workflow_status,
)


def entry_node(state: AgentState) -> AgentState:
    """
    Entry point for the workflow.

    - Ensures basic fields exist in state.
    - Creates a new workflow run in the database.
    - Stores run_id in state for later updates.
    """
    # Ensure log list exists
    state.setdefault("log", [])
    state["log"].append("entry_node: starting")

    # For now, thread_id is None. Later you can tie it to a user/session.
    thread_id = None

    # Create a workflow run record in the database
    run_id = create_workflow_run(thread_id=thread_id, task="unknown")
    state["run_id"] = run_id
    state["log"].append(f"entry_node: created workflow_run run_id={run_id}")

    # If no raw_input was provided, set a default instruction
    if not state.get("raw_input"):
        state["raw_input"] = "Process my inbox."

    return state


def task_router_node(state: AgentState) -> AgentState:
    """
    Decide which task to execute based on the user's input.

    Simple heuristic:
    - If input contains 'summary' or 'daily' → 'daily_summary'
    - Otherwise → 'process_inbox'
    """
    text = (state.get("raw_input") or "").lower()

    if "summary" in text or "daily" in text:
        task = cast(AgentState["task"], "daily_summary")
    else:
        task = cast(AgentState["task"], "process_inbox")

    state["task"] = task
    state.setdefault("log", [])
    state["log"].append(f"task_router_node: task set to '{task}'")

    return state


def process_inbox_node(state: AgentState) -> AgentState:
    """
    Node responsible for inbox processing.

    It calls the Groq-based gmail_agent with a clear instruction:
    - Fetch unread emails.
    - Classify them.
    - Send replies where needed.
    - Apply labels.
    - Return a concise summary of what was done.
    """
    state.setdefault("log", [])
    state["log"].append("process_inbox_node: invoking gmail_agent")

    user_instruction = state.get("raw_input") or ""

    message_content = (
        "Task: process_inbox\n\n"
        "Your job: Process the Gmail inbox. Fetch unread emails, classify them, "
        "ignore spam, apply appropriate labels (e.g., Client, Billing, Personal, Spam), "
        "and generate professional replies where needed.\n\n"
        f"User instruction: {user_instruction}"
    )

    result = gmail_agent.invoke({"messages": [HumanMessage(content=message_content)]})

    state["result"] = result
    state["log"].append("process_inbox_node: gmail_agent finished")

    # Mark workflow as completed in the database
    run_id = state.get("run_id")
    if run_id:
        try:
            update_workflow_status(run_id, "completed", result=result)
            state["log"].append(f"process_inbox_node: workflow_run {run_id} marked as completed")
        except Exception as exc:
            state["log"].append(
                f"process_inbox_node: failed to update workflow status: {exc!r}"
            )

    return state


def daily_summary_node(state: AgentState) -> AgentState:
    """
    Node responsible for generating a daily summary.

    It calls the Groq-based gmail_agent with a clear instruction:
    - Look at today's or recent important emails.
    - Produce a concise summary.
    - Include priorities (High / Medium / Low) where appropriate.
    """
    state.setdefault("log", [])
    state["log"].append("daily_summary_node: invoking gmail_agent")

    user_instruction = state.get("raw_input") or ""

    message_content = (
        "Task: daily_summary\n\n"
        "Your job: Create a concise daily summary of important emails. "
        "Highlight key threads, mention the sender and subject briefly, "
        "and assign a rough priority (High / Medium / Low) where appropriate.\n\n"
        f"User instruction: {user_instruction}"
    )

    result = gmail_agent.invoke({"messages": [HumanMessage(content=message_content)]})

    state["result"] = result
    state["log"].append("daily_summary_node: gmail_agent finished")

    # Mark workflow as completed in the database
    run_id = state.get("run_id")
    if run_id:
        try:
            update_workflow_status(run_id, "completed", result=result)
            state["log"].append(f"daily_summary_node: workflow_run {run_id} marked as completed")
        except Exception as exc:
            state["log"].append(
                f"daily_summary_node: failed to update workflow status: {exc!r}"
            )

    return state
