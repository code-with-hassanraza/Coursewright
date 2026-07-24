from fastapi.testclient import TestClient


def test_list_pending_reviews_as_admin(
    client: TestClient, admin_headers, test_review
):
    response = client.get("/api/v1/admin/reviews", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "pending"


def test_list_pending_reviews_as_reviewer(
    client: TestClient, reviewer_headers, test_review
):
    response = client.get("/api/v1/admin/reviews", headers=reviewer_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_list_pending_reviews_as_student_forbidden(
    client: TestClient, auth_headers
):
    response = client.get("/api/v1/admin/reviews", headers=auth_headers)
    assert response.status_code == 403


def test_list_pending_reviews_unauthenticated(client: TestClient):
    response = client.get("/api/v1/admin/reviews")
    assert response.status_code == 401


def test_approve_review_success(
    client: TestClient, admin_headers, test_review
):
    response = client.post(
        f"/api/v1/admin/reviews/{test_review.id}/approve",
        json={"notes": "Looks great!"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["notes"] == "Looks great!"
    assert data["reviewed_at"] is not None


def test_approve_already_approved_review(
    client: TestClient, admin_headers, test_review
):
    # Approve once
    client.post(
        f"/api/v1/admin/reviews/{test_review.id}/approve",
        json={},
        headers=admin_headers,
    )
    # Try to approve again
    response = client.post(
        f"/api/v1/admin/reviews/{test_review.id}/approve",
        json={},
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert "already" in response.json()["detail"].lower()


def test_reject_review_success(
    client: TestClient, admin_headers, test_review
):
    response = client.post(
        f"/api/v1/admin/reviews/{test_review.id}/reject",
        json={"notes": "Needs more detail"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"
    assert data["notes"] == "Needs more detail"


def test_reject_already_rejected_review(
    client: TestClient, admin_headers, test_review
):
    client.post(
        f"/api/v1/admin/reviews/{test_review.id}/reject",
        json={},
        headers=admin_headers,
    )
    response = client.post(
        f"/api/v1/admin/reviews/{test_review.id}/reject",
        json={},
        headers=admin_headers,
    )
    assert response.status_code == 400


def test_approve_review_not_found(client: TestClient, admin_headers):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.post(
        f"/api/v1/admin/reviews/{fake_id}/approve",
        json={},
        headers=admin_headers,
    )
    assert response.status_code == 404


def test_list_drafts_as_admin(
    client: TestClient, admin_headers, admin_user, test_field, db
):
    from app.models.specialization import Specialization
    draft = Specialization(
        field_id=test_field.id,
        name="Draft Spec",
        status="draft",
        created_by=admin_user.id,
    )
    db.add(draft)
    db.commit()

    response = client.get(
        "/api/v1/admin/content/drafts", headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    names = [item["name"] for item in data["items"]]
    assert "Draft Spec" in names


def test_list_drafts_as_student_forbidden(
    client: TestClient, auth_headers
):
    response = client.get(
        "/api/v1/admin/content/drafts", headers=auth_headers
    )
    assert response.status_code == 403