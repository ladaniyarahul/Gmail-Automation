# src/graph/build_graph.py

"""
Builds the LangGraph workflow for the Gmail AI Agent.

Graph structure:
    entry_node       -> initializes workflow_run and state
        ↓
    task_router_node -> decides between 'process_inbox' and 'daily_summary'
        ↓
    process_inbox_node OR daily_summary_node
        ↓
       END

A Redis-based checkpointer is attached so that workflow state
can be persisted and recovered across steps/runs.
"""

from langgraph.graph import StateGraph, END

from src.graph.state_types import AgentState
from src.graph.nodes import (
    entry_node,
    task_router_node,
    process_inbox_node,
    daily_summary_node,
)
from database.redis_client import get_redis_client

# NOTE:
# Make sure you have langgraph[redis] or the appropriate extra installed.
try:
    from langgraph.checkpoint.redis import RedisCheckpointer  # verify import path with docs if needed
except Exception:  # pragma: no cover - optional dependency
    # Fallback to an in-memory checkpointer if Redis support isn't installed
    from langgraph.checkpoint.memory import InMemorySaver as MemoryCheckpointer
    RedisCheckpointer = None


def build_app():
    """
    Build and compile the LangGraph app with Redis checkpointer.

    Returns:
        A compiled LangGraph app that you can invoke with:
            app.invoke(initial_state, config={"configurable": {"thread_id": "some-id"}})
    """
    # Initialize Redis client for checkpointing (if available)
    redis_client = get_redis_client()
    if RedisCheckpointer is not None:
        checkpointer = RedisCheckpointer(redis_client)
    else:
        # Use a simple in-memory checkpointer when Redis backend is not installed
        checkpointer = MemoryCheckpointer()

    # Create a state graph with the AgentState schema
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("entry", entry_node)
    graph.add_node("task_router", task_router_node)
    graph.add_node("process_inbox", process_inbox_node)
    graph.add_node("daily_summary", daily_summary_node)

    # Set entry point
    graph.set_entry_point("entry")

    # Simple linear edge: entry -> task_router
    graph.add_edge("entry", "task_router")

    # Conditional routing from task_router based on state["task"]
    def route_by_task(state: AgentState) -> str:
        task = state.get("task")
        if task == "daily_summary":
            return "daily_summary"
        # Default to process_inbox
        return "process_inbox"

    graph.add_conditional_edges(
        "task_router",
        route_by_task,
        {
            "process_inbox": "process_inbox",
            "daily_summary": "daily_summary",
        },
    )

    # Both final nodes lead to END
    graph.add_edge("process_inbox", END)
    graph.add_edge("daily_summary", END)

    # Compile with Redis checkpointer
    app = graph.compile(checkpointer=checkpointer)
    return app
