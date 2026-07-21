from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_filename: str
    content_type: str
    size_bytes: int
    status: str
    section_count: int
    table_count: int
    paragraph_count: int
    word_count: int
    created_at: datetime


class RunSchema(BaseModel):
    text: str
    bold: bool
    italic: bool
    underline: bool
    font_name: str | None = None
    font_size_pt: float | None = None


class SectionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_index: int
    start_type: str | None = None


class TableSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    section_id: str | None = None
    order_index: int
    row_count: int
    col_count: int


class ParagraphSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    section_id: str | None = None
    table_id: str | None = None
    location: str
    paragraph_type: str
    order_index: int
    row_index: int | None = None
    col_index: int | None = None
    heading_level: int | None = None
    list_level: int | None = None
    style_name: str | None = None
    text: str
    runs: list[RunSchema] = []


class DocumentStructure(BaseModel):
    document: DocumentSummary
    sections: list[SectionSchema]
    tables: list[TableSchema]
    paragraphs: list[ParagraphSchema]
