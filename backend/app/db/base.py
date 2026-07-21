from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models.

    Imported by Alembic's env.py so autogenerate can see every model —
    new model modules must be imported here as they're added.
    """
