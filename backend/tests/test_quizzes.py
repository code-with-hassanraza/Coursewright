from fastapi.testclient import TestClient


def test_get_quiz_success(
    client: TestClient, test_quiz, auth_headers
):
    response = client.get(
        f"/api/v1/quizzes/specialization/{test_quiz.specialization_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Quiz"
    assert len(data["questions"]) == 3
    assert data["pass_score"] == 70


def test_get_quiz_not_found(client: TestClient, auth_headers):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(
        f"/api/v1/quizzes/specialization/{fake_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_get_quiz_unauthenticated(client: TestClient, test_quiz):
    response = client.get(
        f"/api/v1/quizzes/specialization/{test_quiz.specialization_id}"
    )
    assert response.status_code == 401


def test_submit_quiz_all_correct(
    client: TestClient, test_quiz, auth_headers
):
    response = client.post(
        f"/api/v1/quizzes/{test_quiz.id}/submit",
        json={
            "answers": {
                "q1": "A language",
                "q2": "A framework",
                "q3": "An ORM",
            }
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 100
    assert data["passed"] is True
    assert data["correct"] == 3
    assert data["total"] == 3


def test_submit_quiz_partial_correct(
    client: TestClient, test_quiz, auth_headers
):
    # 2 out of 3 correct = 66% — fails (pass_score is 70)
    response = client.post(
        f"/api/v1/quizzes/{test_quiz.id}/submit",
        json={
            "answers": {
                "q1": "A language",
                "q2": "A framework",
                "q3": "A language",  # wrong
            }
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 66
    assert data["passed"] is False
    assert data["correct"] == 2


def test_submit_quiz_all_wrong(
    client: TestClient, test_quiz, auth_headers
):
    response = client.post(
        f"/api/v1/quizzes/{test_quiz.id}/submit",
        json={
            "answers": {
                "q1": "A snake",
                "q2": "A database",
                "q3": "A language",
            }
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 0
    assert data["passed"] is False
    assert data["correct"] == 0


def test_submit_quiz_updates_progress(
    client: TestClient, test_quiz, auth_headers, test_progress
):
    # Submit with passing score
    response = client.post(
        f"/api/v1/quizzes/{test_quiz.id}/submit",
        json={
            "answers": {
                "q1": "A language",
                "q2": "A framework",
                "q3": "An ORM",
            }
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["passed"] is True

    # Verify progress was updated
    me = client.get("/api/v1/auth/me", headers=auth_headers).json()
    progress_resp = client.get(
        f"/api/v1/users/{me['id']}/progress", headers=auth_headers
    )
    assert progress_resp.status_code == 200
    items = progress_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["quiz_score"] == 100


def test_submit_quiz_not_found(client: TestClient, auth_headers):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.post(
        f"/api/v1/quizzes/{fake_id}/submit",
        json={"answers": {}},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_submit_quiz_unauthenticated(client: TestClient, test_quiz):
    response = client.post(
        f"/api/v1/quizzes/{test_quiz.id}/submit",
        json={"answers": {"q1": "A language"}},
    )
    assert response.status_code == 401