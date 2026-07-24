from fastapi.testclient import TestClient


def test_list_specializations_empty(client: TestClient):
    response = client.get("/api/v1/specializations")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] == 0


def test_list_specializations_with_data(
    client: TestClient, test_specialization
):
    response = client.get("/api/v1/specializations")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Test Specialization"


def test_search_specializations(client: TestClient, test_specialization):
    response = client.get("/api/v1/specializations?search=Test")
    assert response.status_code == 200
    assert response.json()["total"] == 1

    response = client.get("/api/v1/specializations?search=nonexistent")
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_filter_specializations_by_field(
    client: TestClient, test_specialization, test_field
):
    response = client.get(
        f"/api/v1/specializations?field_id={test_field.id}"
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_get_specialization_success(
    client: TestClient, test_specialization
):
    response = client.get(
        f"/api/v1/specializations/{test_specialization.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Specialization"
    assert data["job_roles"] == ["Developer", "Engineer"]
    assert data["salary_range"] == "PKR 80,000 - 200,000"


def test_get_specialization_not_found(client: TestClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/specializations/{fake_id}")
    assert response.status_code == 404


def test_create_specialization_admin(
    client: TestClient, test_field, admin_headers
):
    response = client.post(
        "/api/v1/specializations",
        json={
            "name": "New Specialization",
            "field_id": str(test_field.id),
            "description": "A new one",
            "job_roles": ["Engineer"],
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    assert response.json()["status"] == "draft"


def test_create_specialization_student_forbidden(
    client: TestClient, test_field, auth_headers
):
    response = client.post(
        "/api/v1/specializations",
        json={"name": "Forbidden", "field_id": str(test_field.id)},
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_update_specialization_admin(
    client: TestClient, test_specialization, admin_headers
):
    response = client.put(
        f"/api/v1/specializations/{test_specialization.id}",
        json={"name": "Updated Name", "status": "in_review"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


def test_explore_specialization_success(
    client: TestClient, test_specialization, test_roadmap, auth_headers
):
    response = client.post(
        f"/api/v1/specializations/{test_specialization.id}/explore",
        json={"roadmap_id": str(test_roadmap.id)},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "exploring"
    assert data["completed_nodes"] == []


def test_explore_already_exploring(
    client: TestClient, test_specialization, auth_headers, test_progress
):
    response = client.post(
        f"/api/v1/specializations/{test_specialization.id}/explore",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "Already exploring" in response.json()["detail"]


def test_explore_nonexistent_specialization(
    client: TestClient, auth_headers
):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.post(
        f"/api/v1/specializations/{fake_id}/explore",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 404