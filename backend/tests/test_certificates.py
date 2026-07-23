from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user_progress import UserProgress
from app.crud import crud_user


def test_get_my_certificates_empty(client: TestClient, auth_headers):
    response = client.get("/api/v1/certificates/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_generate_certificate_no_progress(
    client: TestClient, test_specialization, auth_headers
):
    response = client.post(
        "/api/v1/certificates/generate",
        json={"specialization_id": str(test_specialization.id)},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "explore" in response.json()["detail"].lower()


def test_generate_certificate_quiz_not_passed(
    client: TestClient, test_specialization, auth_headers, test_progress
):
    # Progress exists but quiz_score is None
    response = client.post(
        "/api/v1/certificates/generate",
        json={"specialization_id": str(test_specialization.id)},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "quiz" in response.json()["detail"].lower()


def test_generate_certificate_quiz_score_too_low(
    client: TestClient,
    test_specialization,
    auth_headers,
    test_progress,
    db,
):
    # Set quiz score below pass threshold
    test_progress.quiz_score = 50
    db.commit()

    response = client.post(
        "/api/v1/certificates/generate",
        json={"specialization_id": str(test_specialization.id)},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "70%" in response.json()["detail"]


def test_generate_certificate_success(
    client: TestClient,
    test_specialization,
    auth_headers,
    test_progress,
    db,
):
    # Set passing quiz score
    test_progress.quiz_score = 85
    db.commit()

    response = client.post(
        "/api/v1/certificates/generate",
        json={"specialization_id": str(test_specialization.id)},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert "certificate_code" in data
    assert len(data["certificate_code"]) <= 64
    assert data["user_id"] is not None
    assert data["specialization_id"] == str(test_specialization.id)


def test_generate_certificate_already_issued(
    client: TestClient,
    test_specialization,
    auth_headers,
    test_progress,
    db,
):
    test_progress.quiz_score = 85
    db.commit()

    # First generation
    r1 = client.post(
        "/api/v1/certificates/generate",
        json={"specialization_id": str(test_specialization.id)},
        headers=auth_headers,
    )
    assert r1.status_code == 201

    # Second attempt — should fail
    r2 = client.post(
        "/api/v1/certificates/generate",
        json={"specialization_id": str(test_specialization.id)},
        headers=auth_headers,
    )
    assert r2.status_code == 400
    assert "already issued" in r2.json()["detail"].lower()


def test_get_my_certificates_after_issuance(
    client: TestClient,
    test_specialization,
    auth_headers,
    test_progress,
    db,
):
    test_progress.quiz_score = 90
    db.commit()

    client.post(
        "/api/v1/certificates/generate",
        json={"specialization_id": str(test_specialization.id)},
        headers=auth_headers,
    )

    response = client.get("/api/v1/certificates/me", headers=auth_headers)
    assert response.status_code == 200
    certs = response.json()
    assert len(certs) == 1
    assert certs[0]["specialization_id"] == str(test_specialization.id)


def test_verify_certificate_valid(
    client: TestClient,
    test_specialization,
    auth_headers,
    test_progress,
    db,
):
    test_progress.quiz_score = 80
    db.commit()

    cert_response = client.post(
        "/api/v1/certificates/generate",
        json={"specialization_id": str(test_specialization.id)},
        headers=auth_headers,
    )
    code = cert_response.json()["certificate_code"]

    # Verify — no auth needed
    response = client.get(f"/api/v1/certificates/verify/{code}")
    assert response.status_code == 200
    data = response.json()
    assert data["certificate_code"] == code
    assert "user_id" in data
    assert "issued_at" in data


def test_verify_certificate_invalid_code(client: TestClient):
    response = client.get("/api/v1/certificates/verify/fakecode123")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()