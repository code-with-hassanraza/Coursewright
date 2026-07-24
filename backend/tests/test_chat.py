from unittest.mock import patch
from fastapi.testclient import TestClient

MOCK_AI_RESPONSE = {
    "reply": "Great question! Here's how it works...",
    "source": "gemini/gemini-2.0-flash",
}

# Patch path: where AIService is DEFINED (lazy import inside function)
PATCH_PATH = "app.services.ai_service.AIService"


def test_chat_message_success(client: TestClient, auth_headers):
    with patch(PATCH_PATH) as MockAIService:
        MockAIService.return_value.chat_with_context.return_value = MOCK_AI_RESPONSE
        response = client.post(
            "/api/v1/chat/message",
            json={"message": "How does backend development work?"},
            headers=auth_headers,
        )
    assert response.status_code == 200
    assert response.json()["reply"] == MOCK_AI_RESPONSE["reply"]
    assert response.json()["source"] == MOCK_AI_RESPONSE["source"]


def test_chat_with_roadmap_context(
    client: TestClient, auth_headers, test_roadmap
):
    with patch(PATCH_PATH) as MockAIService:
        MockAIService.return_value.chat_with_context.return_value = {
            "reply": "Based on your roadmap, start with Introduction...",
            "source": "groq/llama-3.1-8b-instant",
        }
        response = client.post(
            "/api/v1/chat/message",
            json={
                "message": "What should I study first?",
                "roadmap_id": str(test_roadmap.id),
            },
            headers=auth_headers,
        )
    assert response.status_code == 200
    assert "reply" in response.json()


def test_chat_with_invalid_roadmap_id(client: TestClient, auth_headers):
    with patch(PATCH_PATH) as MockAIService:
        MockAIService.return_value.chat_with_context.return_value = MOCK_AI_RESPONSE
        response = client.post(
            "/api/v1/chat/message",
            json={"message": "Hello", "roadmap_id": "not-a-uuid"},
            headers=auth_headers,
        )
    assert response.status_code == 200


def test_chat_fallback_response(client: TestClient, auth_headers):
    with patch(PATCH_PATH) as MockAIService:
        MockAIService.return_value.chat_with_context.return_value = {
            "reply": "I'm having trouble connecting. Please try again.",
            "source": "fallback",
        }
        response = client.post(
            "/api/v1/chat/message",
            json={"message": "Test message"},
            headers=auth_headers,
        )
    assert response.status_code == 200
    assert response.json()["source"] == "fallback"


def test_chat_unauthenticated(client: TestClient):
    response = client.post(
        "/api/v1/chat/message",
        json={"message": "Hello"},
    )
    assert response.status_code == 401


def test_chat_empty_message(client: TestClient, auth_headers):
    with patch(PATCH_PATH) as MockAIService:
        MockAIService.return_value.chat_with_context.return_value = MOCK_AI_RESPONSE
        response = client.post(
            "/api/v1/chat/message",
            json={"message": ""},
            headers=auth_headers,
        )
    assert response.status_code == 200
    