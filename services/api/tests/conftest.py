import base64
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def tiny_png_bytes() -> bytes:
    # 1x1 transparent PNG, with a random trailing marker appended so every
    # test invocation gets unique bytes (-> a unique SHA-256 hash). The
    # pytest suite runs against a real shared dev DB with no per-test
    # isolation/rollback, so reusing identical bytes across test runs would
    # spuriously trip the "สลิปเดียวกัน" duplicate-file detection.
    base_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
        "+A8AAQUBAScY42YAAAAASUVORK5CYII="
    )
    return base_png + uuid.uuid4().bytes
