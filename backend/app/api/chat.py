from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import (
    ChatMessageResponse,
    ConversationResponse,
)
from app.services import conversation_service

import json

from app.schemas.chat import ChatMessageRequest
from app.core.chat_prompts import MANPATH_SYSTEM_INSTRUCTION
from app.services.gemini_service import GeminiService
from app.services.chat_context_service import build_chat_context

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)

@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_conversation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return conversation_service.create_conversation(
        db=db,
        user_id=current_user.id,
    )

@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
)
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return conversation_service.get_user_conversations(
        db=db,
        user_id=current_user.id,
    )

@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[ChatMessageResponse],
)
def list_conversation_messages(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    messages = conversation_service.get_conversation_messages(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    if messages is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    return messages

@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = conversation_service.delete_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ChatMessageResponse,
)
def send_chat_message(
    conversation_id: UUID,
    request: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Verify conversation ownership.
    conversation = conversation_service.get_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    # 2. Retrieve previous conversation history.
    history = conversation_service.get_conversation_messages(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    # 3. Build authenticated user's assessment context.
    context = build_chat_context(
        db=db,
        user_id=current_user.id,
    )

    # 4. Persist the user's message.
    user_message = conversation_service.save_message(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        role="user",
        content=request.content,
    )

    if user_message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    # 5. Prepare context and conversation history for Gemini.
    prompt = {
        "assessment_context": context,
        "conversation_history": [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in history
        ],
        "current_message": request.content,
    }

        # 5. Generate the assistant response.
    try:
        gemini = GeminiService()

        assistant_response = gemini.generate_response(
            system_instruction=MANPATH_SYSTEM_INSTRUCTION,
            user_message=json.dumps(prompt, default=str),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The AI assistant is temporarily unavailable. "
                "Your message has been saved; please try again."
            ),
        ) from exc

    # 6. Persist the assistant response.
    saved_response = conversation_service.save_message(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        role="assistant",
        content=assistant_response,
    )

    if saved_response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    return saved_response