from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.chat_message import ChatMessage
from app.models.conversation import Conversation


def create_conversation(
    db: Session,
    user_id: UUID,
) -> Conversation:
    conversation = Conversation(
        user_id=user_id,
        title="New conversation",
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


def get_user_conversations(
    db: Session,
    user_id: UUID,
) -> list[Conversation]:
    statement = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(
            Conversation.updated_at.desc(),
            Conversation.id.desc(),
        )
    )

    return list(db.scalars(statement).all())


def get_conversation(
    db: Session,
    conversation_id: UUID,
    user_id: UUID,
) -> Conversation | None:
    statement = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id,
    )

    return db.scalar(statement)


def delete_conversation(
    db: Session,
    conversation_id: UUID,
    user_id: UUID,
) -> bool:
    conversation = get_conversation(db, conversation_id, user_id)

    if conversation is None:
        return False

    db.delete(conversation)
    db.commit()

    return True

def save_message(
    db: Session,
    conversation_id: UUID,
    user_id: UUID,
    role: str,
    content: str,
) -> ChatMessage | None:
    conversation = get_conversation(
        db,
        conversation_id,
        user_id,
    )

    if conversation is None:
        return None

    message = ChatMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
    )

    conversation.updated_at = func.now()

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


def get_conversation_messages(
    db: Session,
    conversation_id: UUID,
    user_id: UUID,
) -> list[ChatMessage] | None:
    conversation = get_conversation(
        db,
        conversation_id,
        user_id,
    )

    if conversation is None:
        return None

    statement = (
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(
            ChatMessage.created_at.asc(),
            ChatMessage.id.asc(),
        )
    )

    return list(db.scalars(statement).all())