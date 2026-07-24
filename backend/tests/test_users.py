from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.crud import crud_user


def test_get_user_success(client: TestClient, registered_user, auth_headers):
    # Get the current user's ID via /me
    me = client.get("/api/v1/auth/me", headers=auth_headers).json()
    response = client.get(f"/api/v1/users/{me['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == registered_user["payload"]["email"]


def test_get_user_not_found(client: TestClient, auth_headers):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/users/{fake_id}", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_get_user_unauthenticated(client: TestClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/users/{fake_id}")
    assert response.status_code == 401


def test_update_own_profile_success(client: TestClient, auth_headers):
    me = client.get("/api/v1/auth/me", headers=auth_headers).json()
    response = client.put(
        f"/api/v1/users/{me['id']}",
        json={"full_name": "Updated Name", "degree": "MSCS"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["degree"] == "MSCS"


def test_update_partial_fields_only(client: TestClient, auth_headers):
    me = client.get("/api/v1/auth/me", headers=auth_headers).json()
    # Only update year_of_study — full_name should remain unchanged
    response = client.put(
        f"/api/v1/users/{me['id']}",
        json={"year_of_study": 4},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["year_of_study"] == 4
    assert response.json()["full_name"] == me["full_name"]


def test_update_other_user_forbidden(
    client: TestClient, auth_headers, admin_user
):
    # Try to update admin's profile as a student
    response = client.put(
        f"/api/v1/users/{admin_user.id}",
        json={"full_name": "Hacked"},
        headers=auth_headers,
    )
    assert response.status_code == 403
    assert "own profile" in response.json()["detail"]


def test_get_own_progress_empty(client: TestClient, auth_headers):
    me = client.get("/api/v1/auth/me", headers=auth_headers).json()
    response = client.get(
        f"/api/v1/users/{me['id']}/progress",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_get_own_progress_with_data(
    client: TestClient, auth_headers, test_progress
):
    me = client.get("/api/v1/auth/me", headers=auth_headers).json()
    response = client.get(
        f"/api/v1/users/{me['id']}/progress",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "exploring"


def test_get_other_user_progress_forbidden(
    client: TestClient, auth_headers, admin_user
):
    response = client.get(
        f"/api/v1/users/{admin_user.id}/progress",
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_admin_can_view_any_progress(
    client: TestClient, admin_headers, registered_user, db
):
    user = crud_user.get_by_email(
        db, email=registered_user["payload"]["email"]
    )
    response = client.get(
        f"/api/v1/users/{user.id}/progress",
        headers=admin_headers,
    )
    assert response.status_code == 200