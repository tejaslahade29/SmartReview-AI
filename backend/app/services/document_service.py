"""Orchestrates upload validation, parsing, storage, and persistence.

Parsing (document_parser) and storage (file_storage) stay independent of
each other and of the database — this module is the only place that wires
them together and talks to SQLAlchemy.
"""

from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.exceptions import FileTooLargeError, NotFoundError, UnsupportedFileTypeError
from app.models.document import Document, DocumentParagraph, DocumentSection, DocumentTable
from app.models.review import Review
from app.models.reviewed_document import ReviewedDocument
from app.services import file_storage
from app.services.document_parser import ParsedDocument, parse_docx

_DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def validate_upload(filename: str, content: bytes) -> None:
    settings = get_settings()

    if not filename.lower().endswith(".docx"):
        raise UnsupportedFileTypeError("Only .docx files are supported.")

    max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_size_bytes:
        raise FileTooLargeError(
            f"File exceeds the maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )


def _persist_parsed_document(
    db: Session, document: Document, parsed: ParsedDocument
) -> Document:
    section_id_by_index: dict[int, str] = {}
    for parsed_section in parsed.sections:
        section = DocumentSection(
            document_id=document.id,
            order_index=parsed_section.order_index,
            start_type=parsed_section.start_type,
        )
        db.add(section)
        db.flush()
        section_id_by_index[parsed_section.order_index] = section.id

    table_id_by_index: dict[int, str] = {}
    for parsed_table in parsed.tables:
        table = DocumentTable(
            document_id=document.id,
            section_id=section_id_by_index.get(parsed_table.section_index)
            if parsed_table.section_index is not None
            else None,
            order_index=parsed_table.order_index,
            row_count=parsed_table.row_count,
            col_count=parsed_table.col_count,
        )
        db.add(table)
        db.flush()
        table_id_by_index[parsed_table.order_index] = table.id

    for sequence_index, parsed_paragraph in enumerate(parsed.paragraphs):
        db.add(
            DocumentParagraph(
                document_id=document.id,
                section_id=section_id_by_index.get(parsed_paragraph.section_index)
                if parsed_paragraph.section_index is not None
                else None,
                table_id=table_id_by_index.get(parsed_paragraph.table_index)
                if parsed_paragraph.table_index is not None
                else None,
                location=parsed_paragraph.location.value,
                paragraph_type=parsed_paragraph.paragraph_type.value,
                order_index=parsed_paragraph.order_index,
                sequence_index=sequence_index,
                row_index=parsed_paragraph.row_index,
                col_index=parsed_paragraph.col_index,
                heading_level=parsed_paragraph.heading_level,
                list_level=parsed_paragraph.list_level,
                style_name=parsed_paragraph.style_name,
                text=parsed_paragraph.text,
                runs=[run.__dict__ for run in parsed_paragraph.runs],
            )
        )

    document.section_count = parsed.section_count
    document.table_count = parsed.table_count
    document.paragraph_count = parsed.paragraph_count
    document.word_count = parsed.word_count
    document.status = "processed"

    db.commit()
    db.refresh(document)
    return document


def process_upload(db: Session, filename: str, content: bytes) -> Document:
    validate_upload(filename, content)

    parsed = parse_docx(content)

    document = Document(
        original_filename=filename,
        storage_path="",
        content_type=_DOCX_CONTENT_TYPE,
        size_bytes=len(content),
        status="processing",
    )
    db.add(document)
    db.flush()

    storage_path = file_storage.save_document_file(document.id, content)
    document.storage_path = storage_path

    return _persist_parsed_document(db, document, parsed)


def list_documents(db: Session) -> list[dict]:
    """Documents ordered newest-first, each pre-joined with its latest
    review's status/agreement_type and whether a reviewed DOCX exists —
    everything the Documents table and Dashboard need in one query pass.
    """
    documents = db.query(Document).order_by(Document.created_at.desc()).all()
    if not documents:
        return []

    document_ids = [document.id for document in documents]

    latest_review_by_document: dict[str, Review] = {}
    reviews = (
        db.query(Review)
        .filter(Review.document_id.in_(document_ids))
        .order_by(Review.created_at.desc())
        .all()
    )
    for review in reviews:
        latest_review_by_document.setdefault(review.document_id, review)

    reviewed_document_ids = {
        row[0]
        for row in db.query(ReviewedDocument.document_id)
        .filter(ReviewedDocument.document_id.in_(document_ids))
        .distinct()
    }

    items: list[dict] = []
    for document in documents:
        latest_review = latest_review_by_document.get(document.id)
        items.append(
            {
                "id": document.id,
                "original_filename": document.original_filename,
                "content_type": document.content_type,
                "size_bytes": document.size_bytes,
                "status": document.status,
                "section_count": document.section_count,
                "table_count": document.table_count,
                "paragraph_count": document.paragraph_count,
                "word_count": document.word_count,
                "created_at": document.created_at,
                "agreement_type": latest_review.agreement_type if latest_review else None,
                "latest_review_id": latest_review.id if latest_review else None,
                "review_status": latest_review.status if latest_review else None,
                "has_reviewed_document": document.id in reviewed_document_ids,
            }
        )
    return items


def get_document(db: Session, document_id: str) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise NotFoundError(f"Document '{document_id}' was not found.")
    return document


def get_document_structure(db: Session, document_id: str) -> Document:
    document = (
        db.query(Document)
        .options(
            selectinload(Document.sections),
            selectinload(Document.tables),
            selectinload(Document.paragraphs),
        )
        .filter(Document.id == document_id)
        .first()
    )
    if document is None:
        raise NotFoundError(f"Document '{document_id}' was not found.")
    return document
