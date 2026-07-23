import io
from dataclasses import dataclass, field

import docx
import pytest
from docx.oxml.ns import qn
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.document import Document
from app.services import file_storage, review_engine
from app.services.claude_service import ClaudeService

_engine = create_engine(
    "sqlite:///./test_document_modifier.db", connect_args={"check_same_thread": False}
)
_TestSessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def _override_get_db():
    db = _TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True, scope="module")
def _setup_database():
    Base.metadata.create_all(bind=_engine)
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=_engine)


client = TestClient(app)


@dataclass
class _FakeTextBlock:
    text: str
    type: str = "text"


@dataclass
class _FakeUsage:
    input_tokens: int = 10
    output_tokens: int = 20


@dataclass
class _FakeResponse:
    content: list = field(default_factory=list)
    stop_reason: str = "end_turn"
    model: str = "claude-opus-4-8"
    usage: _FakeUsage = field(default_factory=_FakeUsage)


class _FakeMessages:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response

    def create(self, **kwargs):
        return self._response


class _FakeAnthropicClient:
    def __init__(self, response: _FakeResponse) -> None:
        self.messages = _FakeMessages(response)


def _build_sample_docx() -> bytes:
    document = docx.Document()
    document.add_heading("Non-Disclosure Agreement", level=1)
    document.add_paragraph(
        'This Agreement is entered into between ABC Technologies Pvt Ltd ("Supplier") '
        'and XYZ Corporation ("Client").'
    )
    document.add_paragraph(
        "ABC Technologies Pvt Ltd may terminate this Agreement at any time without "
        "notice for any reason, at its sole discretion."
    )
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _upload_and_review(monkeypatch) -> tuple[str, str, str]:
    """Returns (document_id, review_id, target_paragraph_id)."""
    original_bytes = _build_sample_docx()
    upload_response = client.post(
        "/api/v1/documents",
        files={
            "file": (
                "nda.docx",
                original_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    document_id = upload_response.json()["id"]

    structure = client.get(f"/api/v1/documents/{document_id}/structure").json()
    target_paragraph = next(
        p
        for p in structure["paragraphs"]
        if p["location"] == "body" and p["paragraph_type"] != "heading" and "terminate" in p["text"]
    )

    fake_response = _FakeResponse(
        content=[
            _FakeTextBlock(
                text=(
                    '{"findings": [{"finding_id": "f1", '
                    f'"paragraph_id": "{target_paragraph["id"]}", '
                    '"issue_type": "termination_imbalance", "severity": "high", '
                    '"explanation": "One-sided termination right with no notice.", '
                    '"suggested_text": "Either party may terminate with 30 days notice.", '
                    '"confidence": 0.85}, '
                    '{"finding_id": "f2", '
                    f'"paragraph_id": "{target_paragraph["id"]}", '
                    '"issue_type": "vague_notice", "severity": "medium", '
                    '"explanation": "Notice mechanism is undefined.", '
                    '"suggested_text": null, "confidence": 0.6}]}'
                )
            )
        ],
    )
    fake_service = ClaudeService(client=_FakeAnthropicClient(fake_response))
    monkeypatch.setattr(review_engine, "default_claude_service", fake_service)

    review_response = client.post(f"/api/v1/documents/{document_id}/review")
    assert review_response.status_code == 201
    review_id = review_response.json()["id"]

    return document_id, review_id, target_paragraph["id"]


def test_generate_reviewed_document_applies_comments_highlight_and_tracked_change(monkeypatch):
    document_id, review_id, target_paragraph_id = _upload_and_review(monkeypatch)

    generate_response = client.post(f"/api/v1/reviews/{review_id}/reviewed-document")
    assert generate_response.status_code == 201
    body = generate_response.json()

    assert body["document_id"] == document_id
    assert body["review_id"] == review_id
    assert body["version"] == 1
    assert body["comment_count"] == 2
    assert body["highlight_count"] == 1
    assert body["tracked_change_count"] == 1

    download_response = client.get(f"/api/v1/reviewed-documents/{body['id']}/download")
    assert download_response.status_code == 200
    assert download_response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    reviewed_docx = docx.Document(io.BytesIO(download_response.content))
    assert len(reviewed_docx.comments) == 2
    comment_texts = ["\n".join(p.text for p in c.paragraphs) for c in reviewed_docx.comments]
    assert any("Severity: HIGH" in t and "termination_imbalance" in t for t in comment_texts)
    assert any("Severity: MEDIUM" in t and "vague_notice" in t for t in comment_texts)

    body_xml = reviewed_docx.element.body.xml
    assert "<w:ins " in body_xml
    assert "<w:del " in body_xml
    assert "w:delText" in body_xml
    assert 'w:fill="FFA500"' in body_xml  # high severity -> orange

    ins_texts = [
        el.text
        for el in reviewed_docx.element.body.iter(qn("w:ins"))
        for el in el.iter(qn("w:t"))
    ]
    assert any("Either party may terminate with 30 days notice." in (t or "") for t in ins_texts)


def test_original_document_is_never_modified(monkeypatch):
    document_id, review_id, _ = _upload_and_review(monkeypatch)

    db = _TestSessionLocal()
    document = db.get(Document, document_id)
    original_bytes_before = file_storage.read_file(document.storage_path)
    db.close()

    client.post(f"/api/v1/reviews/{review_id}/reviewed-document")

    db = _TestSessionLocal()
    document = db.get(Document, document_id)
    original_bytes_after = file_storage.read_file(document.storage_path)
    db.close()

    assert original_bytes_before == original_bytes_after

    original_docx = docx.Document(io.BytesIO(original_bytes_after))
    body_xml = original_docx.element.body.xml
    assert "<w:ins " not in body_xml
    assert "<w:del " not in body_xml
    assert "commentReference" not in body_xml


def test_generating_twice_creates_new_version_without_overwriting(monkeypatch):
    _document_id, review_id, _ = _upload_and_review(monkeypatch)

    first = client.post(f"/api/v1/reviews/{review_id}/reviewed-document").json()
    second = client.post(f"/api/v1/reviews/{review_id}/reviewed-document").json()

    assert first["id"] != second["id"]
    assert first["version"] == 1
    assert second["version"] == 2

    first_download = client.get(f"/api/v1/reviewed-documents/{first['id']}/download")
    second_download = client.get(f"/api/v1/reviewed-documents/{second['id']}/download")
    assert first_download.status_code == 200
    assert second_download.status_code == 200
    assert first_download.content != b""
    assert second_download.content != b""

    # Both versions must independently open and contain their own tracked change.
    docx.Document(io.BytesIO(first_download.content))
    docx.Document(io.BytesIO(second_download.content))


def test_get_reviewed_document_metadata(monkeypatch):
    _document_id, review_id, _ = _upload_and_review(monkeypatch)
    generated = client.post(f"/api/v1/reviews/{review_id}/reviewed-document").json()

    response = client.get(f"/api/v1/reviewed-documents/{generated['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == generated["id"]


def test_get_unknown_reviewed_document_returns_404():
    response = client.get("/api/v1/reviewed-documents/does-not-exist")
    assert response.status_code == 404

    response = client.get("/api/v1/reviewed-documents/does-not-exist/download")
    assert response.status_code == 404
