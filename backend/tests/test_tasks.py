from fastapi.testclient import TestClient


def test_list_tasks_empty(
    client: TestClient, test_specialization, auth_headers
):
    response = client.get(
        f"/api/v1/tasks/specialization/{test_specialization.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_list_tasks_with_data(
    client: TestClient, test_task, auth_headers
):
    response = client.get(
        f"/api/v1/tasks/specialization/{test_task.specialization_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Build a REST API"
    assert data["items"][0]["difficulty"] == "beginner"


def test_list_tasks_unauthenticated(client: TestClient, test_task):
    response = client.get(
        f"/api/v1/tasks/specialization/{test_task.specialization_id}"
    )
    assert response.status_code == 401


def test_get_task_success(client: TestClient, test_task, auth_headers):
    response = client.get(
        f"/api/v1/tasks/{test_task.id}", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Build a REST API"
    assert "FastAPI" in data["suggested_tools"]
    assert "Step 1" in data["instructions"]


def test_get_task_not_found(client: TestClient, auth_headers):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/tasks/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


def test_complete_task_without_exploring_first(
    client: TestClient, test_task, auth_headers
):
    # No progress record exists — should fail
    response = client.post(
        f"/api/v1/tasks/{test_task.id}/complete",
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "explore" in response.json()["detail"].lower()


def test_complete_task_success(
    client: TestClient, test_task, auth_headers, test_progress
):
    response = client.post(
        f"/api/v1/tasks/{test_task.id}/complete",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "learning"
    assert str(test_task.id) in data["completed_nodes"]


def test_complete_task_twice(
    client: TestClient, test_task, auth_headers, test_progress
):
    # Complete once
    client.post(
        f"/api/v1/tasks/{test_task.id}/complete", headers=auth_headers
    )
    # Complete again — should not duplicate the node_id
    response = client.post(
        f"/api/v1/tasks/{test_task.id}/complete", headers=auth_headers
    )
    assert response.status_code == 200
    completed = response.json()["completed_nodes"]
    assert completed.count(str(test_task.id)) == 1


def test_complete_task_not_found(
    client: TestClient, auth_headers, test_progress
):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.post(
        f"/api/v1/tasks/{fake_id}/complete", headers=auth_headers
    )
    assert response.status_code == 404