"""Importing this package registers every ORM model on Base.metadata.

New model modules must be imported here as they're added — Alembic's
env.py relies on this for autogenerate to see the full schema.
"""

from app.models.document import (  # noqa: F401
    Document,
    DocumentParagraph,
    DocumentSection,
    DocumentTable,
)
