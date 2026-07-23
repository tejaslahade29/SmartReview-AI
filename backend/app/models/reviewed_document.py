import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ReviewedDocument(Base):
    """A generated, review-annotated copy of a Document. Never overwrites
    the original file or a prior reviewed version — each generation adds
    a new row with an incrementing `version` scoped to `document_id`.
    """

    __tablename__ = "reviewed_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"))

    version: Mapped[int] = mapped_column(Integer)
    storage_path: Mapped[str] = mapped_column(String(500))
    comment_count: Mapped[int] = mapped_column(Integer, default=0)
    highlight_count: Mapped[int] = mapped_column(Integer, default=0)
    tracked_change_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship()  # noqa: F821
    review: Mapped["Review"] = relationship()  # noqa: F821
