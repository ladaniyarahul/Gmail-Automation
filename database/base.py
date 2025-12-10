# database/python/base.py

"""
Yeh file Postgres ke saath SQLAlchemy ka core setup rakhti hai:
- engine  -> DB connection
- SessionLocal -> DB sessions banane ke liye
- Base -> saare ORM models isse inherit karenge
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from configs.settings import *

# Postgres engine (sync)
engine = create_engine(
    POSTGRES_DNS,
    echo=False,        # debug ke liye True kar sakte ho
    future=True,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

# Base class for ORM models
Base = declarative_base()
