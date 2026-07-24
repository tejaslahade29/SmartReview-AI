from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import DocumentListItem, DocumentStructure, DocumentSummary
from app.services import document_service

router = APIRouter()


@router.post("", response_model=DocumentSummary, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DocumentSummary:
    content = await file.read()
    document = document_service.process_upload(db, file.filename or "upload.docx", content)
    return DocumentSummary.model_validate(document)


@router.get("", response_model=list[DocumentListItem])
def list_documents(db: Session = Depends(get_db)) -> list[DocumentListItem]:
    return [DocumentListItem.model_validate(item) for item in document_service.list_documents(db)]


@router.get("/{document_id}", response_model=DocumentSummary)
def get_document(document_id: str, db: Session = Depends(get_db)) -> DocumentSummary:
    document = document_service.get_document(db, document_id)
    return DocumentSummary.model_validate(document)


@router.get("/{document_id}/structure", response_model=DocumentStructure)
def get_document_structure(document_id: str, db: Session = Depends(get_db)) -> DocumentStructure:
    document = document_service.get_document_structure(db, document_id)
    return DocumentStructure(
        document=DocumentSummary.model_validate(document),
        sections=document.sections,
        tables=document.tables,
        paragraphs=document.paragraphs,
    )
