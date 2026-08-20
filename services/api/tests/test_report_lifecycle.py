"""Report Lifecycle + Dispute/Appeal + Credit/Discredit formula regression tests.

Exercises the Critical Rules from the KuRuTan V2 domain spec:
- Traceability Rule (ledger entries, never deleted, always voided in place)
- Presumption of Innocence Rule (UNVERIFIED never affects score)
- Dispute First Architecture (appeal overturns a verified report)
- RBAC (Public/User/Admin/Officer)
"""
import uuid


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


def _login_seeded(client, email: str) -> str:
    resp = client.post(
        "/api/v1/auth/login", data={"username": email, "password": "ChangeMe123!"}
    )
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _get_a_seller_id(client) -> str:
    resp = client.get("/api/v1/sellers")
    sellers = resp.json()
    assert len(sellers) > 0
    return sellers[0]["id"]


def _get_discredit_factor_id(client, officer_token: str) -> str:
    # No public "list factors" endpoint exists yet (Phase 4 concern); reuse
    # the seeded NON_DELIVERY factor by asking the DB through a verified
    # report review error message is overkill — instead read it straight
    # from the audit log is also overkill. Simplest: query via SQLAlchemy.
    from sqlalchemy import select

    from app.database.session import SessionLocal
    from app.models.credit import DiscreditFactor

    db = SessionLocal()
    try:
        factor = db.execute(
            select(DiscreditFactor).where(DiscreditFactor.code == "NON_DELIVERY")
        ).scalar_one()
        return str(factor.id)
    finally:
        db.close()


def test_public_cannot_create_report(client):
    seller_id = _get_a_seller_id(client)
    resp = client.post(
        "/api/v1/reports",
        json={"seller_id": seller_id, "category": "non_delivery", "description": "x"},
    )
    assert resp.status_code == 401


def test_duplicate_report_is_flagged_but_not_blocked(client):
    token = _register_and_login(client, "dup")
    seller_id = _get_a_seller_id(client)
    # Unique per test invocation — the suite runs against a real shared dev
    # DB with no per-test rollback, so a fixed literal would collide with
    # leftover rows from a previous run.
    reference_key = f"DUPTEST-{uuid.uuid4().hex[:10]}"

    r1 = client.post(
        "/api/v1/reports",
        headers=_auth(token),
        json={
            "seller_id": seller_id,
            "category": "non_delivery",
            "description": "first",
            "reference_key": reference_key,
        },
    )
    assert r1.status_code == 201
    assert r1.json()["status"] == "unverified"

    r2 = client.post(
        "/api/v1/reports",
        headers=_auth(token),
        json={
            "seller_id": seller_id,
            "category": "non_delivery",
            "description": "second, same reference",
            "reference_key": reference_key,
        },
    )
    assert r2.status_code == 201
    assert r2.json()["duplicate_of_report_id"] == r1.json()["id"]


def test_minimum_image_evidence_required_before_review(client):
    token = _register_and_login(client, "evi")
    seller_id = _get_a_seller_id(client)

    report = client.post(
        "/api/v1/reports",
        headers=_auth(token),
        json={"seller_id": seller_id, "category": "non_delivery", "description": "no evidence yet"},
    ).json()

    # No evidence at all -> rejected.
    resp = client.post(f"/api/v1/reports/{report['id']}/submit-for-review", headers=_auth(token))
    assert resp.status_code == 400

    # Only a non-image evidence -> still rejected.
    client.post(
        "/api/v1/evidence",
        headers=_auth(token),
        json={
            "report_id": report["id"],
            "file_url": "https://example.com/chat.txt",
            "file_type": "document",
            "file_size_bytes": 100,
        },
    )
    resp = client.post(f"/api/v1/reports/{report['id']}/submit-for-review", headers=_auth(token))
    assert resp.status_code == 400

    # Adding an image evidence unblocks the transition.
    client.post(
        "/api/v1/evidence",
        headers=_auth(token),
        json={
            "report_id": report["id"],
            "file_url": "https://example.com/slip.jpg",
            "file_type": "image",
            "file_size_bytes": 200,
        },
    )
    resp = client.post(f"/api/v1/reports/{report['id']}/submit-for-review", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending_review"


def _create_verified_report(client, user_token, officer_token, seller_id, factor_id, tag):
    report = client.post(
        "/api/v1/reports",
        headers=_auth(user_token),
        json={"seller_id": seller_id, "category": "non_delivery", "description": tag},
    ).json()
    client.post(
        "/api/v1/evidence",
        headers=_auth(user_token),
        json={
            "report_id": report["id"],
            "file_url": f"https://example.com/{tag}.jpg",
            "file_type": "image",
            "file_size_bytes": 200,
        },
    )
    client.post(f"/api/v1/reports/{report['id']}/submit-for-review", headers=_auth(user_token))
    verified = client.post(
        f"/api/v1/reports/{report['id']}/review",
        headers=_auth(officer_token),
        json={"decision": "verified", "discredit_factor_id": factor_id},
    ).json()
    assert verified["status"] == "verified"
    return report["id"]


def test_verify_creates_discredit_ledger_and_updates_score(client):
    user_token = _register_and_login(client, "verify")
    officer_token = _login_seeded(client, "officer@kurutan.dev")
    seller_id = _get_a_seller_id(client)
    factor_id = _get_discredit_factor_id(client, officer_token)

    score_before = client.get(f"/api/v1/discredits/{seller_id}/score").json()
    before = score_before["score"] if score_before else 0.0

    report_id = _create_verified_report(
        client, user_token, officer_token, seller_id, factor_id, "score-verify"
    )

    ledger = client.get(f"/api/v1/discredits/{seller_id}/ledger").json()
    entry = next(e for e in ledger if e["report_id"] == report_id)
    assert entry["points"] == entry["factor_weight"] * entry["verification_impact_multiplier"]
    assert entry["is_voided"] is False

    score_after = client.get(f"/api/v1/discredits/{seller_id}/score").json()
    assert score_after["score"] == before + entry["points"]


def test_dispute_overturn_voids_ledger_and_recalculates_score(client):
    user_token = _register_and_login(client, "overturn")
    officer_token = _login_seeded(client, "officer@kurutan.dev")
    seller_id = _get_a_seller_id(client)
    factor_id = _get_discredit_factor_id(client, officer_token)

    report_id = _create_verified_report(
        client, user_token, officer_token, seller_id, factor_id, "overturn"
    )
    score_after_verify = client.get(f"/api/v1/discredits/{seller_id}/score").json()["score"]

    dispute = client.post(
        "/api/v1/disputes",
        headers=_auth(user_token),
        json={"report_id": report_id, "seller_id": seller_id, "reason": "delivered on time"},
    ).json()
    assert dispute["status"] == "pending"

    report_after_dispute = client.get(f"/api/v1/reports/{report_id}").json()
    assert report_after_dispute["status"] == "appealed"

    resolved = client.post(
        f"/api/v1/disputes/{dispute['id']}/resolve",
        headers=_auth(officer_token),
        json={"decision": "approved", "resolution_notes": "carrier confirmed delivery"},
    ).json()
    assert resolved["status"] == "approved"

    report_after_resolve = client.get(f"/api/v1/reports/{report_id}").json()
    assert report_after_resolve["status"] == "voided"

    ledger = client.get(f"/api/v1/discredits/{seller_id}/ledger").json()
    entry = next(e for e in ledger if e["report_id"] == report_id)
    assert entry["is_voided"] is True

    score_after_void = client.get(f"/api/v1/discredits/{seller_id}/score").json()["score"]
    assert score_after_void == score_after_verify - entry["points"]


def test_dispute_rejected_maintains_score(client):
    user_token = _register_and_login(client, "maintain")
    officer_token = _login_seeded(client, "officer@kurutan.dev")
    seller_id = _get_a_seller_id(client)
    factor_id = _get_discredit_factor_id(client, officer_token)

    report_id = _create_verified_report(
        client, user_token, officer_token, seller_id, factor_id, "maintain"
    )
    score_after_verify = client.get(f"/api/v1/discredits/{seller_id}/score").json()["score"]

    dispute = client.post(
        "/api/v1/disputes",
        headers=_auth(user_token),
        json={"report_id": report_id, "seller_id": seller_id, "reason": "not delivered really"},
    ).json()

    resolved = client.post(
        f"/api/v1/disputes/{dispute['id']}/resolve",
        headers=_auth(officer_token),
        json={"decision": "rejected", "resolution_notes": "insufficient counter evidence"},
    ).json()
    assert resolved["status"] == "rejected"

    report_after_resolve = client.get(f"/api/v1/reports/{report_id}").json()
    assert report_after_resolve["status"] == "verified"

    score_after = client.get(f"/api/v1/discredits/{seller_id}/score").json()["score"]
    assert score_after == score_after_verify


def test_public_seller_view_masks_display_name(client):
    seller_id = _get_a_seller_id(client)
    resp = client.get(f"/api/v1/sellers/{seller_id}")
    body = resp.json()
    assert "masked_name" in body
    assert "display_name" not in body

    user_token = _register_and_login(client, "sellerview")
    resp2 = client.get(f"/api/v1/sellers/{seller_id}", headers=_auth(user_token))
    body2 = resp2.json()
    assert "display_name" in body2
