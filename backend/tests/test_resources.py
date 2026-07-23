from fastapi.testclient import TestClient


def test_get_node_resources_empty(client: TestClient, test_roadmap):
    response = client.get("/api/v1/resources/node/nonexistent-node")
    assert response.status_code == 200
    assert response.json() == []


def test_get_node_resources_with_data(
    client: TestClient, test_resource
):
    response = client.get(f"/api/v1/resources/node/{test_resource.node_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Python Tutorial"
    assert data[0]["is_free"] is True
    assert data[0]["verified"] is True


def test_create_resource_as_admin(
    client: TestClient, test_roadmap, admin_headers
):
    response = client.post(
        "/api/v1/resources",
        json={
            "roadmap_id": str(test_roadmap.id),
            "node_id": "node-1",
            "title": "Python Docs",
            "url": "https://docs.python.org",
            "type": "docs",
            "is_free": True,
            "verified": True,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Python Docs"
    assert data["node_id"] == "node-1"
    assert data["type"] == "docs"


def test_create_resource_as_student_forbidden(
    client: TestClient, test_roadmap, auth_headers
):
    response = client.post(
        "/api/v1/resources",
        json={
            "roadmap_id": str(test_roadmap.id),
            "node_id": "node-1",
            "title": "Forbidden",
            "url": "https://example.com",
        },
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_create_resource_unauthenticated(
    client: TestClient, test_roadmap
):
    response = client.post(
        "/api/v1/resources",
        json={
            "roadmap_id": str(test_roadmap.id),
            "node_id": "node-1",
            "title": "Unauth",
            "url": "https://example.com",
        },
    )
    assert response.status_code == 401


def test_delete_resource_as_admin(
    client: TestClient, test_resource, admin_headers
):
    response = client.delete(
        f"/api/v1/resources/{test_resource.id}",
        headers=admin_headers,
    )
    assert response.status_code == 204

    # Verify it's gone
    check = client.get(
        f"/api/v1/resources/node/{test_resource.node_id}"
    )
    assert check.json() == []


def test_delete_resource_not_found(
    client: TestClient, admin_headers
):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.delete(
        f"/api/v1/resources/{fake_id}", headers=admin_headers
    )
    assert response.status_code == 404


def test_delete_resource_as_student_forbidden(
    client: TestClient, test_resource, auth_headers
):
    response = client.delete(
        f"/api/v1/resources/{test_resource.id}",
        headers=auth_headers,
    )
    assert response.status_code == 403