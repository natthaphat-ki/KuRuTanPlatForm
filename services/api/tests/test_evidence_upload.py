"""Evidence file upload tests — Phase 3 local disk storage backend.

Covers: real multipart upload, whitelist extension validation, oversized
file rejection, download round-trip, and the "สลิปเดียวกัน" (same file)
duplicate detection by SHA-256 hash across different reports.
"""
import uuid

from app.core.config import settings


def _unique_email(prefix: str) -> str:
    return f"pytest-{prefix}-{uuid.uuid4().hex[:8]}@kurutan.dev"


def _register_and_login(client, prefix: str) -> str:
    email = _unique_email(prefix)
    password = "PytestPass123!"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": prefix},
    )
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _get_a_seller_id(client) -> str:
    resp = client.get("/api/v1/sellers")
    return resp.json()[0]["id"]


def _create_report(client, token: str, tag: str) -> str:
    seller_id = _get_a_seller_id(client)
    resp = client.post(
        "/api/v1/reports",
        headers=_auth(token),
        json={"seller_id": seller_id, "category": "non_delivery", "description": tag},
    )
    return resp.json()["id"]


def test_upload_valid_image_and_download_roundtrip(client, tiny_png_bytes):
    token = _register_and_login(client, "upload-ok")
    report_id = _create_report(client, token, "upload-ok")

    resp = client.post(
        "/api/v1/evidence/upload",
        headers=_auth(token),
        data={"report_id": report_id, "comment": "payment slip"},
        files={"file": ("slip.png", tiny_png_bytes, "image/png")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["file_type"] == "image"
    assert body["file_size_bytes"] == len(tiny_png_bytes)
    assert body["file_hash"] is not None and len(body["file_hash"]) == 64
    assert body["duplicate_of_evidence_id"] is None

    download = client.get(f"/api/v1/evidence/{body['id']}/file")
    assert download.status_code == 200
    assert download.content == tiny_png_bytes


def test_upload_rejects_disallowed_extension(client, tiny_png_bytes):
    token = _register_and_login(client, "upload-bad-ext")
    report_id = _create_report(client, token, "upload-bad-ext")

    resp = client.post(
        "/api/v1/evidence/upload",
        headers=_auth(token),
        data={"report_id": report_id},
        files={"file": ("payload.exe", tiny_png_bytes, "application/octet-stream")},
    )
    assert resp.status_code == 400


def test_upload_rejects_oversized_file(client, monkeypatch):
    monkeypatch.setattr(settings, "MAX_EVIDENCE_FILE_SIZE_BYTES", 10)

    token = _register_and_login(client, "upload-too-big")
    report_id = _create_report(client, token, "upload-too-big")

    resp = client.post(
        "/api/v1/evidence/upload",
        headers=_auth(token),
        data={"report_id": report_id},
        files={"file": ("slip.png", b"x" * 100, "image/png")},
    )
    assert resp.status_code == 413


def test_upload_flags_duplicate_file_across_reports(client, tiny_png_bytes):
    token = _register_and_login(client, "upload-dup")
    report1 = _create_report(client, token, "upload-dup-1")
    report2 = _create_report(client, token, "upload-dup-2")

    first = client.post(
        "/api/v1/evidence/upload",
        headers=_auth(token),
        data={"report_id": report1},
        files={"file": ("slip.png", tiny_png_bytes, "image/png")},
    ).json()

    second = client.post(
        "/api/v1/evidence/upload",
        headers=_auth(token),
        data={"report_id": report2},
        files={"file": ("slip_copy.png", tiny_png_bytes, "image/png")},
    ).json()

    assert second["duplicate_of_evidence_id"] == first["id"]


def test_upload_requires_login(client, tiny_png_bytes):
    resp = client.post(
        "/api/v1/evidence/upload",
        data={"report_id": str(uuid.uuid4())},
        files={"file": ("slip.png", tiny_png_bytes, "image/png")},
    )
    assert resp.status_code == 401


def test_upload_rejects_unknown_report(client, tiny_png_bytes):
    token = _register_and_login(client, "upload-no-report")
    resp = client.post(
        "/api/v1/evidence/upload",
        headers=_auth(token),
        data={"report_id": str(uuid.uuid4())},
        files={"file": ("slip.png", tiny_png_bytes, "image/png")},
    )
    assert resp.status_code == 404
