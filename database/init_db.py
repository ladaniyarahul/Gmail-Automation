# database/python/init_db.py

"""
Is file ka kaam sirf itna hai:
- saare models import karo
- Base.metadata.create_all() se tables create kara do

Isko app startup pe ek baar call kar dena.
"""

from .base import Base, engine
from . import models  # noqa: F401  # models import karna zaroori hai taaki tables register ho jayein


def init_db() -> None:
    """
    Postgres me saare ORM models ke tables create karega.
    Agar table already exist karte hain to safe hai (re-create nahi karega).
    """
    Base.metadata.create_all(bind=engine)
