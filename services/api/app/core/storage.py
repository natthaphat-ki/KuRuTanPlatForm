"""Evidence file storage — Phase 3 local disk backend.

Files are streamed to disk under `settings.STORAGE_DIR/evidence/<report_id>/`
with a UUID-based filename (never trusting the uploader's original filename),
while a SHA-256 hash is computed on the fly so the same physical file
(e.g. the same payment slip photo reused across reports) can be detected —
this is the "สลิปเดียวกัน" duplicate check called out in the domain spec.

Swapping this module for an S3/MinIO-backed one later (Phase 3+) should not
require changes anywhere else: routers/services only depend on the
`save_evidence_file` / `resolve_evidence_path` functions below.
"""
import hashlib
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.models.evidence import EvidenceFileType

# Whitelist only — anything not listed here is rejected outright (never
# guessed/defaulted to OTHER) to avoid accepting executables or scripts
# disguised as evidence.
EXTENSION_TO_FILE_TYPE: dict[str, EvidenceFileType] = {
    ".jpg": EvidenceFileType.IMAGE,
    ".jpeg": EvidenceFileType.IMAGE,
    ".png": EvidenceFileType.IMAGE,
    ".webp": EvidenceFileType.IMAGE,
    ".gif": EvidenceFileType.IMAGE,
    ".pdf": EvidenceFileType.DOCUMENT,
    ".doc": EvidenceFileType.DOCUMENT,
    ".docx": EvidenceFileType.DOCUMENT,
    ".txt": EvidenceFileType.DOCUMENT,
    ".mp4": EvidenceFileType.VIDEO,
    ".mov": EvidenceFileType.VIDEO,
    ".avi": EvidenceFileType.VIDEO,
    ".mp3": EvidenceFileType.AUDIO,
    ".wav": EvidenceFileType.AUDIO,
    ".m4a": EvidenceFileType.AUDIO,
}

_CHUNK_SIZE = 1024 * 1024  # 1 MB


def _storage_root() -> Path:
    root = Path(settings.STORAGE_DIR) / "evidence"
    root.mkdir(parents=True, exist_ok=True)
    return root


def infer_file_type(filename: str) -> EvidenceFileType:
    ext = Path(filename).suffix.lower()
    file_type = EXTENSION_TO_FILE_TYPE.get(ext)
    if file_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext or '(none)'}' is not an allowed evidence type.",
        )
    return file_type


def save_evidence_file(report_id: uuid.UUID, upload: UploadFile) -> dict:
    """Stream `upload` to disk, enforcing the size limit and computing a
    SHA-256 hash as it goes. Returns a dict with `relative_path`,
    `file_type`, `file_size_bytes`, `file_hash`.
    """
    file_type = infer_file_type(upload.filename or "")

    ext = Path(upload.filename).suffix.lower()
    stored_name = f"{uuid.uuid4().hex}{ext}"
    report_dir = _storage_root() / str(report_id)
    report_dir.mkdir(parents=True, exist_ok=True)
    dest_path = report_dir / stored_name

    hasher = hashlib.sha256()
    size = 0
    try:
        with open(dest_path, "wb") as out:
            while True:
                chunk = upload.file.read(_CHUNK_SIZE)
                if not chunk:
                    break
                size += len(chunk)
                if size > settings.MAX_EVIDENCE_FILE_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Evidence file exceeds the maximum allowed size.",
                    )
                hasher.update(chunk)
                out.write(chunk)
    except HTTPException:
        dest_path.unlink(missing_ok=True)
        raise
    except Exception as exc:  # pragma: no cover - unexpected I/O failure
        dest_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store evidence file.",
        ) from exc

    if size == 0:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty."
        )

    relative_path = f"evidence/{report_id}/{stored_name}"
    return {
        "relative_path": relative_path,
        "file_type": file_type,
        "file_size_bytes": size,
        "file_hash": hasher.hexdigest(),
    }


def resolve_evidence_path(relative_path: str) -> Path:
    """Resolve a stored relative_path back to an absolute path, guarding
    against path traversal outside the storage root.
    """
    root = Path(settings.STORAGE_DIR).resolve()
    candidate = (root / relative_path).resolve()
    if root not in candidate.parents and candidate != root:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if not candidate.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return candidate
