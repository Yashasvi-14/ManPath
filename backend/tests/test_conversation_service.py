from unittest.mock import MagicMock
import sys
from pathlib import Path
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.conversation_service import (
    create_conversation,
    get_user_conversations,
    get_conversation,
    delete_conversation,
    save_message,
    get_conversation_messages,
)

def test_create_conversation_commits_and_returns_record():
    db = MagicMock()
    user_id = uuid4()

    result = create_conversation(db=db, user_id=user_id)

    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(db.add.call_args.args[0])

    assert result is db.add.call_args.args[0]
    assert result.user_id == user_id
    assert result.title == "New conversation"


def test_get_user_conversations_filters_by_user_and_orders_newest_first():
    from sqlalchemy.dialects import postgresql

    db = MagicMock()
    db.scalars.return_value.all.return_value = []

    user_id = uuid4()

    get_user_conversations(db=db, user_id=user_id)

    statement = db.scalars.call_args.args[0]
    compiled = statement.compile(dialect=postgresql.dialect())

    sql = str(compiled)

    assert "conversations.user_id =" in sql
    assert (
        "ORDER BY conversations.updated_at DESC, conversations.id DESC"
        in sql
    )
    assert user_id in compiled.params.values()

def test_get_conversation_filters_by_conversation_and_user():
    from sqlalchemy.dialects import postgresql

    db = MagicMock()
    conversation_id = uuid4()
    user_id = uuid4()

    get_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=user_id,
    )

    statement = db.scalar.call_args.args[0]
    compiled = statement.compile(dialect=postgresql.dialect())

    sql = str(compiled)

    assert "conversations.id =" in sql
    assert "conversations.user_id =" in sql
    assert conversation_id in compiled.params.values()
    assert user_id in compiled.params.values()

def test_delete_conversation_commits_when_owned_by_user():
    db = MagicMock()
    conversation = MagicMock()

    db.scalar.return_value = conversation

    result = delete_conversation(
        db=db,
        conversation_id=uuid4(),
        user_id=uuid4(),
    )

    assert result is True
    db.delete.assert_called_once_with(conversation)
    db.commit.assert_called_once()


def test_delete_conversation_does_nothing_when_not_found():
    db = MagicMock()
    db.scalar.return_value = None

    result = delete_conversation(
        db=db,
        conversation_id=uuid4(),
        user_id=uuid4(),
    )

    assert result is False
    db.delete.assert_not_called()
    db.commit.assert_not_called()

def test_save_message_commits_and_returns_record():
    db = MagicMock()
    conversation = MagicMock()
    db.scalar.return_value = conversation

    conversation_id = uuid4()
    user_id = uuid4()

    result = save_message(
        db=db,
        conversation_id=conversation_id,
        user_id=user_id,
        role="user",
        content="What does my latest assessment mean?",
    )

    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(db.add.call_args.args[0])

    assert result is db.add.call_args.args[0]
    assert result.conversation_id == conversation_id
    assert result.role == "user"
    assert result.content == "What does my latest assessment mean?"
    assert conversation.updated_at is not None

def test_get_conversation_messages_returns_chronological_messages():
    from sqlalchemy.dialects import postgresql

    db = MagicMock()
    db.scalar.return_value = MagicMock()
    db.scalars.return_value.all.return_value = []

    conversation_id = uuid4()
    user_id = uuid4()

    result = get_conversation_messages(
        db=db,
        conversation_id=conversation_id,
        user_id=user_id,
    )

    assert result == []

    statement = db.scalars.call_args.args[0]
    compiled = statement.compile(dialect=postgresql.dialect())

    sql = str(compiled)

    assert "chat_messages.conversation_id =" in sql
    assert (
        "ORDER BY chat_messages.created_at ASC, chat_messages.id ASC"
        in sql
    )
    assert conversation_id in compiled.params.values()


def test_get_conversation_messages_rejects_unauthorized_user():
    db = MagicMock()
    db.scalar.return_value = None

    result = get_conversation_messages(
        db=db,
        conversation_id=uuid4(),
        user_id=uuid4(),
    )

    assert result is None
    db.scalars.assert_not_called()