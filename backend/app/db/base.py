"""SQLAlchemy declarative base — models register themselves via app.models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for every ORM model in the project."""

    pass

# NOTE: do NOT import model modules here — that creates a circular import
# (models/*.py import Base from this file). Model registration lives in
# app/models/__init__.py; alembic's env.py imports that package explicitly.
