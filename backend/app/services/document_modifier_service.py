"""Converts persisted review findings into a new, review-annotated DOCX.

Orchestrates comment_generator, highlight_applier, and tracked_change_applier
against paragraphs located purely by paragraph_id (via paragraph_locator —
never by searching text). Claude is not involved: this module only consumes
findings Module 3 already persisted. The original file is read-only here;
output is always written to a new path via file_storage.
"""

import io
from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationFailedError
from app.models.review import Review, ReviewFinding
from app.models.reviewed_document import ReviewedDocument
from app.services import document_service, file_storage
from app.services.comment_generator import apply_comments
from app.services.highlight_applier import apply_highlight
from app.services.paragraph_locator import locate_paragraphs
from app.services.severity_styles import highest_severity
from app.services.tracked_change_applier import apply_tracked_replacement, next_free_revision_id


def _pick_best_candidate(findings: list[ReviewFinding]) -> ReviewFinding | None:
    candidates = [f for f in findings if f.suggested_text]
    if not candidates:
        return None
    severity_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    return max(candidates, key=lambda f: severity_rank.get(f.severity, -1))


def generate_reviewed_document(db: Session, review_id: str) -> ReviewedDocument:
    review = (
        db.query(Review)
        .filter(Review.id == review_id)
        .first()
    )
    if review is None:
        raise NotFoundError(f"Review '{review_id}' was not found.")

    findings: list[ReviewFinding] = (
        db.query(ReviewFinding).filter(ReviewFinding.review_id == review_id).all()
    )
    if not findings:
        raise ValidationFailedError("Review has no findings to apply.")

    document = document_service.get_document_structure(db, review.document_id)
    original_bytes = file_storage.read_file(document.storage_path)

    docx_document, element_by_paragraph_id = locate_paragraphs(original_bytes, document.paragraphs)

    findings_by_paragraph: dict[str, list[ReviewFinding]] = defaultdict(list)
    for finding in findings:
        findings_by_paragraph[finding.paragraph_id].append(finding)

    comment_count = 0
    highlight_count = 0
    tracked_change_count = 0
    revision_id = next_free_revision_id(docx_document)

    for paragraph_id, paragraph_findings in findings_by_paragraph.items():
        paragraph = element_by_paragraph_id.get(paragraph_id)
        if paragraph is None:
            continue

        # Snapshot the original runs once — comment insertion adds a new
        # commentReference run, and re-deriving from paragraph.runs after
        # that would wrongly sweep it into the highlight/tracked-change.
        original_runs = list(paragraph.runs)

        comment_count += apply_comments(docx_document, original_runs, paragraph_findings)

        severity = highest_severity([f.severity for f in paragraph_findings])
        apply_highlight(original_runs, severity)
        highlight_count += 1

        tracked_finding = _pick_best_candidate(paragraph_findings)
        if tracked_finding is not None:
            revision_id = apply_tracked_replacement(
                paragraph, original_runs, tracked_finding.suggested_text, revision_id
            )
            tracked_change_count += 1

    buffer = io.BytesIO()
    docx_document.save(buffer)
    reviewed_bytes = buffer.getvalue()

    current_max_version = (
        db.query(func.max(ReviewedDocument.version))
        .filter(ReviewedDocument.document_id == document.id)
        .scalar()
    )
    version = (current_max_version or 0) + 1

    storage_path = file_storage.save_reviewed_document_file(document.id, version, reviewed_bytes)

    reviewed_document = ReviewedDocument(
        document_id=document.id,
        review_id=review.id,
        version=version,
        storage_path=storage_path,
        comment_count=comment_count,
        highlight_count=highlight_count,
        tracked_change_count=tracked_change_count,
    )
    db.add(reviewed_document)
    db.commit()
    db.refresh(reviewed_document)
    return reviewed_document


def list_reviewed_documents_for_document(db: Session, document_id: str) -> list[ReviewedDocument]:
    document_service.get_document(db, document_id)  # raises NotFoundError if missing
    return (
        db.query(ReviewedDocument)
        .filter(ReviewedDocument.document_id == document_id)
        .order_by(ReviewedDocument.version.desc())
        .all()
    )


def get_reviewed_document(db: Session, reviewed_document_id: str) -> ReviewedDocument:
    reviewed_document = db.get(ReviewedDocument, reviewed_document_id)
    if reviewed_document is None:
        raise NotFoundError(f"Reviewed document '{reviewed_document_id}' was not found.")
    return reviewed_document


def get_reviewed_document_file(db: Session, reviewed_document_id: str) -> tuple[ReviewedDocument, bytes]:
    reviewed_document = get_reviewed_document(db, reviewed_document_id)
    content = file_storage.read_file(reviewed_document.storage_path)
    return reviewed_document, content
