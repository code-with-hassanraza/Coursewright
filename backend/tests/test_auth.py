import pytest
from fastapi.testclient import TestClient


def test_register_success(client: TestClient):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@test.com",
            "full_name": "New User",
            "password": "securepass123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client: TestClient, registered_user):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": registered_user["payload"]["email"],
            "full_name": "Duplicate User",
            "password": "anotherpass123",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_register_short_password(client: TestClient):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "short@test.com",
            "full_name": "Short Pass",
            "password": "123",
        },
    )
    assert response.status_code == 422  # Pydantic validation error


def test_login_success(client: TestClient, registered_user):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_user["payload"]["email"],
            "password": registered_user["payload"]["password"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient, registered_user):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": registered_user["payload"]["email"],
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_nonexistent_user(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "ghost@test.com",
            "password": "doesntmatter",
        },
    )
    assert response.status_code == 401


def test_get_me_success(client: TestClient, registered_user, auth_headers):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == registered_user["payload"]["email"]
    assert data["full_name"] == registered_user["payload"]["full_name"]
    assert "password_hash" not in data


def test_get_me_no_token(client: TestClient):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_me_invalid_token(client: TestClient):
    headers = {"Authorization": "Bearer this.is.fake"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401