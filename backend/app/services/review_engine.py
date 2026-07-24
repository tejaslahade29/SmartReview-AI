"""Orchestrates the AI review pipeline.

Detect agreement -> normalize parties -> build prompt -> call Claude ->
validate response -> persist findings -> return structured review.

This module owns the workflow only. It never talks to Anthropic directly
(that's ClaudeService) and never touches DOCX files.
"""

from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundError, ValidationFailedError
from app.models.document import DocumentParagraph
from app.models.review import Review, ReviewFinding
from app.services import agreement_detector, document_service, party_normalization_service, prompt_builder
from app.services.claude_service import ClaudeService, claude_service as default_claude_service
from app.services.review_validator import validate_findings

_REVIEWABLE_LOCATIONS = {"body", "table_cell"}


def _select_reviewable_clauses(
    paragraphs: list[DocumentParagraph],
    normalized_text_by_paragraph_id: dict[str, str],
) -> list[tuple[str, str]]:
    clauses: list[tuple[str, str]] = []
    for paragraph in paragraphs:
        if paragraph.location not in _REVIEWABLE_LOCATIONS:
            continue
        if paragraph.paragraph_type == "heading":
            continue
        text = normalized_text_by_paragraph_id.get(paragraph.id)
        if text and text.strip():
            clauses.append((paragraph.id, text))
    return clauses


def run_review(
    db: Session, document_id: str, claude_service: ClaudeService | None = None
) -> Review:
    document = document_service.get_document_structure(db, document_id)

    normalization_result = party_normalization_service.normalize_parties(document.paragraphs)
    agreement_type = agreement_detector.detect_agreement_type(document.paragraphs)

    clauses = _select_reviewable_clauses(
        document.paragraphs, normalization_result.normalized_text_by_paragraph_id
    )
    if not clauses:
        raise ValidationFailedError("Document has no reviewable clauses.")

    prompt = prompt_builder.build_review_prompt(agreement_type, clauses)

    service = claude_service or default_claude_service
    claude_result = service.review_clauses(
        system=prompt.system,
        user_message=prompt.user_message,
        json_schema=prompt.json_schema,
    )

    valid_paragraph_ids = {paragraph_id for paragraph_id, _ in clauses}
    validated = validate_findings(claude_result.findings, valid_paragraph_ids)

    review = Review(
        document_id=document.id,
        agreement_type=agreement_type,
        status="completed",
        model_used=claude_result.model,
        party_mapping=[
            {"original_name": entry.original_name, "normalized_role": entry.normalized_role}
            for entry in normalization_result.mapping
        ],
    )
    db.add(review)
    db.flush()

    for finding in validated:
        db.add(
            ReviewFinding(
                review_id=review.id,
                paragraph_id=finding.paragraph_id,
                finding_id=finding.finding_id,
                issue_type=finding.issue_type,
                severity=finding.severity,
                explanation=finding.explanation,
                suggested_text=finding.suggested_text,
                confidence=finding.confidence,
            )
        )

    db.commit()
    db.refresh(review)
    return review


def get_review(db: Session, review_id: str) -> Review:
    review = (
        db.query(Review)
        .options(selectinload(Review.findings))
        .filter(Review.id == review_id)
        .first()
    )
    if review is None:
        raise NotFoundError(f"Review '{review_id}' was not found.")
    return review


def list_reviews_for_document(db: Session, document_id: str) -> list[Review]:
    document_service.get_document(db, document_id)  # raises NotFoundError if missing
    return (
        db.query(Review)
        .options(selectinload(Review.findings))
        .filter(Review.document_id == document_id)
        .order_by(Review.created_at.desc())
        .all()
    )
