import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))

    agreement_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20))
    model_used: Mapped[str] = mapped_column(String(100))
    party_mapping: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    findings: Mapped[list["ReviewFinding"]] = relationship(
        back_populates="review", cascade="all, delete-orphan"
    )


class ReviewFinding(Base):
    __tablename__ = "review_findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"))
    paragraph_id: Mapped[str] = mapped_column(ForeignKey("document_paragraphs.id", ondelete="CASCADE"))

    finding_id: Mapped[str] = mapped_column(String(100))
    issue_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(20))
    explanation: Mapped[str] = mapped_column(Text)
    suggested_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    review: Mapped["Review"] = relationship(back_populates="findings")
