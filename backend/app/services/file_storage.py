"""Local filesystem storage for uploaded documents.

Kept separate from parsing and from the database layer — swapping this
for object storage later should not require changing the parser or models.
"""

from pathlib import Path

from app.core.config import get_settings


def save_document_file(document_id: str, content: bytes) -> str:
    settings = get_settings()
    storage_dir = Path(settings.DOCUMENT_STORAGE_DIR)
    storage_dir.mkdir(parents=True, exist_ok=True)

    file_path = storage_dir / f"{document_id}.docx"
    file_path.write_bytes(content)
    return str(file_path)


def save_reviewed_document_file(document_id: str, version: int, content: bytes) -> str:
    """Reviewed versions live alongside originals but are never written to
    the same path — the original file at save_document_file's path is
    never touched again after upload.
    """
    settings = get_settings()
    storage_dir = Path(settings.DOCUMENT_STORAGE_DIR) / "reviewed"
    storage_dir.mkdir(parents=True, exist_ok=True)

    file_path = storage_dir / f"{document_id}_v{version}.docx"
    file_path.write_bytes(content)
    return str(file_path)


def read_file(storage_path: str) -> bytes:
    return Path(storage_path).read_bytes()
