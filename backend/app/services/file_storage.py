"""Storage for uploaded and reviewed documents.

Two backends, selected by settings.STORAGE_BACKEND:
- "local": filesystem under DOCUMENT_STORAGE_DIR — simple for dev, but
  doesn't survive a container restart on most hosts.
- "s3": any S3-compatible object store (Cloudflare R2, AWS S3, ...) — used
  in hosted environments for exactly that reason.

Callers never see which backend is active. save_*_file returns an opaque
key string (stored as Document.storage_path / ReviewedDocument.storage_path)
that read_file later takes back — swapping backends never touches callers,
models, or migrations.
"""

from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import NotFoundError


def _document_key(document_id: str) -> str:
    return f"{document_id}.docx"


def _reviewed_document_key(document_id: str, version: int) -> str:
    return f"reviewed/{document_id}_v{version}.docx"


def _s3_client():
    import boto3

    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION,
    )


def _write(key: str, content: bytes) -> None:
    settings = get_settings()
    if settings.STORAGE_BACKEND == "s3":
        _s3_client().put_object(Bucket=settings.S3_BUCKET_NAME, Key=key, Body=content)
        return

    path = Path(settings.DOCUMENT_STORAGE_DIR) / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def save_document_file(document_id: str, content: bytes) -> str:
    key = _document_key(document_id)
    _write(key, content)
    return key


def save_reviewed_document_file(document_id: str, version: int, content: bytes) -> str:
    key = _reviewed_document_key(document_id, version)
    _write(key, content)
    return key


def read_file(storage_path: str) -> bytes:
    settings = get_settings()

    if settings.STORAGE_BACKEND == "s3":
        from botocore.exceptions import ClientError

        try:
            obj = _s3_client().get_object(Bucket=settings.S3_BUCKET_NAME, Key=storage_path)
            return obj["Body"].read()
        except ClientError as exc:
            raise NotFoundError(
                "The stored file is missing. It may have been lost if storage was reset "
                "without the database — please regenerate it."
            ) from exc

    try:
        return (Path(settings.DOCUMENT_STORAGE_DIR) / storage_path).read_bytes()
    except FileNotFoundError as exc:
        raise NotFoundError(
            "The stored file is missing. It may have been lost if the server's storage "
            "was reset without the database — please regenerate it."
        ) from exc
