import uuid


def _unique_email() -> str:
    return f"pytest-{uuid.uuid4().hex[:10]}@kurutan.dev"


def test_register_login_me_flow(client):
    email = _unique_email()
    password = "PytestPass123!"

    register_resp = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Pytest User"},
    )
    assert register_resp.status_code == 201
    assert register_resp.json()["role"] == "user"

    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email


def test_regular_user_cannot_access_admin_endpoint(client):
    email = _unique_email()
    password = "PytestPass123!"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Pytest User 2"},
    )
    login_resp = client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )
    token = login_resp.json()["access_token"]

    resp = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_login_rejects_wrong_password(client):
    email = _unique_email()
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "CorrectPass123!", "full_name": "Pytest User 3"},
    )
    resp = client.post(
        "/api/v1/auth/login", data={"username": email, "password": "WrongPass"}
    )
    assert resp.status_code == 401
