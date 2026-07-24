from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reviewed_document import ReviewedDocumentSchema
from app.services import document_modifier_service

router = APIRouter()

_DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@router.post(
    "/reviews/{review_id}/reviewed-document",
    response_model=ReviewedDocumentSchema,
    status_code=status.HTTP_201_CREATED,
)
def generate_reviewed_document(review_id: str, db: Session = Depends(get_db)) -> ReviewedDocumentSchema:
    reviewed_document = document_modifier_service.generate_reviewed_document(db, review_id)
    return ReviewedDocumentSchema.model_validate(reviewed_document)


@router.get(
    "/documents/{document_id}/reviewed-documents", response_model=list[ReviewedDocumentSchema]
)
def list_reviewed_documents(document_id: str, db: Session = Depends(get_db)) -> list[ReviewedDocumentSchema]:
    reviewed_documents = document_modifier_service.list_reviewed_documents_for_document(db, document_id)
    return [ReviewedDocumentSchema.model_validate(item) for item in reviewed_documents]


@router.get("/reviewed-documents/{reviewed_document_id}", response_model=ReviewedDocumentSchema)
def get_reviewed_document(
    reviewed_document_id: str, db: Session = Depends(get_db)
) -> ReviewedDocumentSchema:
    reviewed_document = document_modifier_service.get_reviewed_document(db, reviewed_document_id)
    return ReviewedDocumentSchema.model_validate(reviewed_document)


@router.get("/reviewed-documents/{reviewed_document_id}/download")
def download_reviewed_document(reviewed_document_id: str, db: Session = Depends(get_db)) -> Response:
    reviewed_document, content = document_modifier_service.get_reviewed_document_file(
        db, reviewed_document_id
    )
    filename = f"reviewed_v{reviewed_document.version}_{reviewed_document.document_id}.docx"
    return Response(
        content=content,
        media_type=_DOCX_CONTENT_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
