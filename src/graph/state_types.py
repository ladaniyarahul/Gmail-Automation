# src/graph/state_types.py

"""
Yahan hum AgentState define kar rahe hain jo LangGraph workflow
ke andar shared state ka structure decide karega.

Ye state har node ke beech pass hota rahega.
"""

from typing import TypedDict, List, Literal, Any, Optional


class AgentState(TypedDict, total=False):
    # ---- Input side ----
    raw_input: Optional[str]          # User ka original instruction (Hinglish allowed)

    # ---- Task understanding ----
    task: Literal["process_inbox", "daily_summary"]  # router decide karega

    # ---- Workflow metadata ----
    run_id: Optional[str]             # DB workflow_runs table ka id
    # future: user_id, session_id, etc. yahan aa sakte hain

    # ---- Operational data ----
    emails: list                      # fetched emails list (agar kabhi state me rakhna ho)
    result: Any                       # final LLM/agent ka output (summary, report, etc.)

    # ---- Debug / tracing ----
    log: List[str]                    # nodes apne steps yahan append karenge
