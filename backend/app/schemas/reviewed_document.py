from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReviewedDocumentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    review_id: str
    version: int
    comment_count: int
    highlight_count: int
    tracked_change_count: int
    created_at: datetime
