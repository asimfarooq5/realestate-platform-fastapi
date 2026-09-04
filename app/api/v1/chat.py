from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.base import get_db
from app.api.deps import get_current_user
from app.schemas.chat import (
    StartConversationRequest, ConversationResponse, MessageCreate, MessageResponse,
)
from app.crud.chat import (
    get_or_create_conversation, get_conversation_by_id, send_message,
    get_conversation_messages, get_user_conversations,
)
from app.crud.user import get_user_by_id

router = APIRouter()


@router.get("/", response_model=List[ConversationResponse])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_user_conversations(db, current_user.id)


@router.post("/start", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def start_conversation(
    request: StartConversationRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if request.other_user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot message yourself")

    other_user = await get_user_by_id(db, request.other_user_id)
    if not other_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    conversation = await get_or_create_conversation(
        db, current_user.id, request.other_user_id, request.property_id
    )
    await send_message(db, conversation.id, current_user.id, request.message)

    conversations = await get_user_conversations(db, current_user.id)
    return next(c for c in conversations if c["id"] == conversation.id)


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    conversation = await get_conversation_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if current_user.id not in (conversation.user_a_id, conversation.user_b_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not part of this conversation")

    return await get_conversation_messages(db, conversation_id, current_user.id)


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def post_message(
    conversation_id: str,
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    conversation = await get_conversation_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if current_user.id not in (conversation.user_a_id, conversation.user_b_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not part of this conversation")

    return await send_message(db, conversation_id, current_user.id, message_data.text)
