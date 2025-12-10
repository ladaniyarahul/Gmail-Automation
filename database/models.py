# database/python/models.py

"""
Yahan saare ORM models define honge.
Abhi ke liye:
- WorkflowRun   -> har run / flow ka record
- EmailLog      -> har email pe kya action hua
- DailySummary  -> daily summary text store
"""

from datetime import datetime, date
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Text, JSON, Date
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


def _uuid_str() -> str:
    """Simple helper: UUID ko string form me generate kare."""
    return str(uuid4())


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    run_id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=_uuid_str,
    )
    thread_id = Column(String, nullable=True)
    task = Column(String, nullable=True)          # process_inbox / daily_summary
    status = Column(String, nullable=False, default="running")  # running/completed/failed
    started_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    finished_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    result = Column(JSON, nullable=True)          # final summary / meta info


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=_uuid_str,
    )
    message_id = Column(String, nullable=True)    # Gmail message id
    thread_id = Column(String, nullable=True)     # Gmail thread id
    subject = Column(Text, nullable=True)
    sender = Column(String, nullable=True)
    action = Column(String, nullable=True)        # reply / label / spam / ignore
    label_applied = Column(String, nullable=True) # Billing / Client / etc.
    reply_text = Column(Text, nullable=True)      # if reply sent
    processed_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )


class DailySummary(Base):
    __tablename__ = "daily_summaries"

    id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=_uuid_str,
    )
    summary_date = Column(
        Date,
        nullable=False,
        default=date.today,
    )
    summary_text = Column(Text, nullable=False)   # LLM generated summary
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
