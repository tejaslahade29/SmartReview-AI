import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20))

    section_count: Mapped[int] = mapped_column(Integer, default=0)
    table_count: Mapped[int] = mapped_column(Integer, default=0)
    paragraph_count: Mapped[int] = mapped_column(Integer, default=0)
    word_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sections: Mapped[list["DocumentSection"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="DocumentSection.order_index"
    )
    tables: Mapped[list["DocumentTable"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="DocumentTable.order_index"
    )
    paragraphs: Mapped[list["DocumentParagraph"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="DocumentParagraph.order_index"
    )


class DocumentSection(Base):
    __tablename__ = "document_sections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    order_index: Mapped[int] = mapped_column(Integer)
    start_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    document: Mapped["Document"] = relationship(back_populates="sections")


class DocumentTable(Base):
    __tablename__ = "document_tables"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    section_id: Mapped[str | None] = mapped_column(
        ForeignKey("document_sections.id", ondelete="SET NULL"), nullable=True
    )
    order_index: Mapped[int] = mapped_column(Integer)
    row_count: Mapped[int] = mapped_column(Integer)
    col_count: Mapped[int] = mapped_column(Integer)

    document: Mapped["Document"] = relationship(back_populates="tables")


class DocumentParagraph(Base):
    __tablename__ = "document_paragraphs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    section_id: Mapped[str | None] = mapped_column(
        ForeignKey("document_sections.id", ondelete="SET NULL"), nullable=True
    )
    table_id: Mapped[str | None] = mapped_column(
        ForeignKey("document_tables.id", ondelete="CASCADE"), nullable=True
    )

    location: Mapped[str] = mapped_column(String(20))
    paragraph_type: Mapped[str] = mapped_column(String(20))
    order_index: Mapped[int] = mapped_column(Integer)

    row_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    col_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    heading_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    list_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    style_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    text: Mapped[str] = mapped_column(Text)
    runs: Mapped[list] = mapped_column(JSON, default=list)

    document: Mapped["Document"] = relationship(back_populates="paragraphs")
