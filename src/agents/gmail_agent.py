# src/agents/gmail_agent.py

"""
Groq-based Gmail AI Agent

This module creates a React-style LLM agent using:
- Groq LLM (ChatGroq)
- Registered tools (gmail_tools)
- A well-defined system prompt

The agent will be used inside LangGraph nodes for:
- Inbox processing
- Daily summaries
"""

from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq

from src.app.config import settings
from src.tools.gmail_tools import (
    fetch_unread_emails,
    send_reply,
    apply_label,
)

# ---------------------------------------------------------
# SYSTEM PROMPT (English Only)
# ---------------------------------------------------------
SYSTEM_PROMPT = """
You are a Gmail Automation AI Agent.

Your responsibilities:
- Process Gmail inbox intelligently.
- Identify important emails.
- Apply correct labels.
- Generate professional replies when appropriate.
- Ignore spam.
- Create concise daily summaries.

Agent Requirements:
1. Understand the user's instruction clearly.
2. Pick the correct tool when needed.
3. Use tools ONLY when necessary.
4. Carefully analyze the output of each tool call.
5. Always return a clean, concise final result.
6. Do not hallucinate tool usage; only use the provided tools.

Tasks you can perform:
- process_inbox → Fetch unread emails, classify them, reply, label.
- daily_summary → Produce a summary of today’s important emails.
"""

# ---------------------------------------------------------
# Groq LLM Client Configuration
# ---------------------------------------------------------
llm = ChatGroq(
    groq_api_key=settings.GROQ_API_KEY,
    model="openai/gpt-oss-120b",   # Recommended Groq model
    temperature=0.0,              # Agent should be deterministic
)

# ---------------------------------------------------------
# Register Tools
# ---------------------------------------------------------
TOOLS = [
    fetch_unread_emails,
    send_reply,
    apply_label,
]

# ---------------------------------------------------------
# Create the React Agent
# ---------------------------------------------------------
gmail_agent = create_react_agent(
    model=llm,
    tools=TOOLS,
    prompt=SYSTEM_PROMPT,
    name="gmail_agent",
)
