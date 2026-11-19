
from unittest.mock import MagicMock
from uuid import uuid4
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from app.main import app
from app.core.dependencies import get_current_user
from app.core.database import get_db
from app.services import conversation_service

from app.api import chat as chat_api
from app.schemas.chat import ChatMessageRequest

@pytest.fixture
def client():
    db = MagicMock()
    user = MagicMock(id=uuid4())

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_create_conversation(client, monkeypatch):
    user_id = app.dependency_overrides[get_current_user]().id

    conversation = MagicMock(
        id=uuid4(),
        title="New conversation",
        created_at="2026-11-20T10:00:00Z",
        updated_at="2026-11-20T10:00:00Z",
    )

    mock_create = MagicMock(return_value=conversation)

    monkeypatch.setattr(
        conversation_service,
        "create_conversation",
        mock_create,
    )

    response = client.post("/chat/conversations")

    assert response.status_code == 201
    assert response.json()["title"] == "New conversation"

    mock_create.assert_called_once()
    assert mock_create.call_args.kwargs["user_id"] == user_id


def test_list_conversations(client, monkeypatch):
    user_id = app.dependency_overrides[get_current_user]().id

    conversations = [
        MagicMock(
            id=uuid4(),
            title="New conversation",
            created_at="2026-11-20T10:00:00Z",
            updated_at="2026-11-20T10:00:00Z",
        )
    ]

    mock_list = MagicMock(return_value=conversations)

    monkeypatch.setattr(
        conversation_service,
        "get_user_conversations",
        mock_list,
    )

    response = client.get("/chat/conversations")

    assert response.status_code == 200
    assert len(response.json()) == 1

    mock_list.assert_called_once()
    assert mock_list.call_args.kwargs["user_id"] == user_id


def test_get_conversation_messages(client, monkeypatch):
    user_id = app.dependency_overrides[get_current_user]().id
    conversation_id = uuid4()

    messages = [
        MagicMock(
            id=uuid4(),
            conversation_id=conversation_id,
            role="user",
            content="Explain my assessment.",
            created_at="2026-11-20T10:00:00Z",
        )
    ]

    mock_messages = MagicMock(return_value=messages)

    monkeypatch.setattr(
        conversation_service,
        "get_conversation_messages",
        mock_messages,
    )

    response = client.get(
        f"/chat/conversations/{conversation_id}/messages"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["role"] == "user"

    mock_messages.assert_called_once_with(
        db=mock_messages.call_args.kwargs["db"],
        conversation_id=conversation_id,
        user_id=user_id,
    )


def test_get_messages_returns_404_for_unauthorized_conversation(
    client,
    monkeypatch,
):
    conversation_id = uuid4()

    mock_messages = MagicMock(return_value=None)

    monkeypatch.setattr(
        conversation_service,
        "get_conversation_messages",
        mock_messages,
    )

    response = client.get(
        f"/chat/conversations/{conversation_id}/messages"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found."


def test_delete_conversation(client, monkeypatch):
    user_id = app.dependency_overrides[get_current_user]().id
    conversation_id = uuid4()

    mock_delete = MagicMock(return_value=True)

    monkeypatch.setattr(
        conversation_service,
        "delete_conversation",
        mock_delete,
    )

    response = client.delete(
        f"/chat/conversations/{conversation_id}"
    )

    assert response.status_code == 204

    mock_delete.assert_called_once()
    assert mock_delete.call_args.kwargs["conversation_id"] == conversation_id
    assert mock_delete.call_args.kwargs["user_id"] == user_id


def test_delete_returns_404_for_unauthorized_conversation(
    client,
    monkeypatch,
):
    conversation_id = uuid4()

    mock_delete = MagicMock(return_value=False)

    monkeypatch.setattr(
        conversation_service,
        "delete_conversation",
        mock_delete,
    )

    response = client.delete(
        f"/chat/conversations/{conversation_id}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found."


def test_send_message_success(client, monkeypatch):
    conversation_id = uuid4()
    user_id = app.dependency_overrides[get_current_user]().id

    conversation = MagicMock(id=conversation_id)

    user_message = MagicMock(
        id=uuid4(),
        conversation_id=conversation_id,
        role="user",
        content="Explain my latest assessment.",
        created_at="2026-11-20T10:00:00Z",
    )

    assistant_message = MagicMock(
        id=uuid4(),
        conversation_id=conversation_id,
        role="assistant",
        content="Your assessment indicates...",
        created_at="2026-11-20T10:00:01Z",
    )

    monkeypatch.setattr(
        conversation_service,
        "get_conversation",
        MagicMock(return_value=conversation),
    )
    monkeypatch.setattr(
        conversation_service,
        "get_conversation_messages",
        MagicMock(return_value=[]),
    )
    monkeypatch.setattr(
        conversation_service,
        "save_message",
        MagicMock(side_effect=[user_message, assistant_message]),
    )
    monkeypatch.setattr(
        chat_api,
        "build_chat_context",
        MagicMock(return_value={"has_assessments": True}),
    )

    mock_generate = MagicMock(return_value="Your assessment indicates...")
    mock_gemini = MagicMock()
    mock_gemini.generate_response = mock_generate

    monkeypatch.setattr(
        chat_api,
        "GeminiService",
        MagicMock(return_value=mock_gemini),
    )

    response = client.post(
        f"/chat/conversations/{conversation_id}/messages",
        json={"content": "Explain my latest assessment."},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "assistant"
    assert response.json()["content"] == "Your assessment indicates..."

    mock_generate.assert_called_once()
    assert mock_generate.call_args.kwargs["system_instruction"] == (
        chat_api.MANPATH_SYSTEM_INSTRUCTION
    )

    assert conversation_service.save_message.call_count == 2


def test_send_message_returns_503_when_gemini_fails(
    client,
    monkeypatch,
):
    conversation_id = uuid4()

    monkeypatch.setattr(
        conversation_service,
        "get_conversation",
        MagicMock(return_value=MagicMock()),
    )
    monkeypatch.setattr(
        conversation_service,
        "get_conversation_messages",
        MagicMock(return_value=[]),
    )
    monkeypatch.setattr(
        conversation_service,
        "save_message",
        MagicMock(return_value=MagicMock()),
    )
    monkeypatch.setattr(
        chat_api,
        "build_chat_context",
        MagicMock(return_value={"has_assessments": True}),
    )

    mock_gemini = MagicMock()
    mock_gemini.generate_response.side_effect = RuntimeError(
        "Gemini unavailable"
    )

    monkeypatch.setattr(
        chat_api,
        "GeminiService",
        MagicMock(return_value=mock_gemini),
    )

    response = client.post(
        f"/chat/conversations/{conversation_id}/messages",
        json={"content": "Explain my assessment."},
    )

    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]

def test_send_message_returns_404_for_unauthorized_conversation(
    client,
    monkeypatch,
):
    conversation_id = uuid4()

    monkeypatch.setattr(
        conversation_service,
        "get_conversation",
        MagicMock(return_value=None),
    )

    mock_gemini = MagicMock()

    monkeypatch.setattr(
        chat_api,
        "GeminiService",
        MagicMock(return_value=mock_gemini),
    )

    response = client.post(
        f"/chat/conversations/{conversation_id}/messages",
        json={"content": "Explain my assessment."},
    )

    assert response.status_code == 404
    mock_gemini.generate_response.assert_not_called()

