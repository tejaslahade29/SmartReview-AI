from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.review import ReviewSchema
from app.services import review_engine

router = APIRouter()


@router.post(
    "/documents/{document_id}/review",
    response_model=ReviewSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_review(document_id: str, db: Session = Depends(get_db)) -> ReviewSchema:
    review = review_engine.run_review(db, document_id)
    return ReviewSchema.model_validate(review)


@router.get("/reviews/{review_id}", response_model=ReviewSchema)
def get_review(review_id: str, db: Session = Depends(get_db)) -> ReviewSchema:
    review = review_engine.get_review(db, review_id)
    return ReviewSchema.model_validate(review)


@router.get("/documents/{document_id}/reviews", response_model=list[ReviewSchema])
def list_reviews_for_document(document_id: str, db: Session = Depends(get_db)) -> list[ReviewSchema]:
    reviews = review_engine.list_reviews_for_document(db, document_id)
    return [ReviewSchema.model_validate(review) for review in reviews]
