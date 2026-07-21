from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models.

    Models import Base from here, so this module must not import models
    itself (that would be circular). Alembic's env.py imports app.models
    (see its __init__.py) to populate Base.metadata before reading it.
    """
