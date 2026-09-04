from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, update, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid

from app.models.chat import Conversation, Message, CommunityPost
from app.models.property import Property
from app.schemas.chat import CommunityPostCreate


async def get_or_create_conversation(
    db: AsyncSession,
    user_id: str,
    other_user_id: str,
    property_id: Optional[str] = None,
) -> Conversation:
    result = await db.execute(
        select(Conversation).where(
            or_(
                and_(Conversation.user_a_id == user_id, Conversation.user_b_id == other_user_id),
                and_(Conversation.user_a_id == other_user_id, Conversation.user_b_id == user_id),
            )
        )
    )
    conversation = result.scalar_one_or_none()
    if conversation:
        return conversation

    conversation = Conversation(
        id=str(uuid.uuid4()),
        user_a_id=user_id,
        user_b_id=other_user_id,
        property_id=property_id,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def get_conversation_by_id(db: AsyncSession, conversation_id: str) -> Optional[Conversation]:
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    return result.scalar_one_or_none()


async def send_message(db: AsyncSession, conversation_id: str, sender_id: str, text: str) -> Message:
    message = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        sender_id=sender_id,
        text=text,
    )
    db.add(message)
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(updated_at=func.now())
    )
    await db.commit()
    await db.refresh(message)
    return message


async def get_conversation_messages(
    db: AsyncSession, conversation_id: str, current_user_id: str
) -> List[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = list(result.scalars().all())

    # Mark the other person's messages as read now that this user has
    # fetched the thread.
    await db.execute(
        update(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.sender_id != current_user_id,
            Message.is_read == False,  # noqa: E712
        )
        .values(is_read=True)
    )
    await db.commit()
    return messages


async def get_user_conversations(db: AsyncSession, user_id: str) -> List[dict]:
    result = await db.execute(
        select(Conversation)
        .where(or_(Conversation.user_a_id == user_id, Conversation.user_b_id == user_id))
        .options(
            selectinload(Conversation.user_a),
            selectinload(Conversation.user_b),
            selectinload(Conversation.property),
            selectinload(Conversation.messages),
        )
        .order_by(Conversation.updated_at.desc())
    )
    conversations = list(result.scalars().all())

    summaries = []
    for conversation in conversations:
        other_user = conversation.user_b if conversation.user_a_id == user_id else conversation.user_a
        messages = conversation.messages
        last_message = messages[-1] if messages else None
        unread_count = sum(1 for m in messages if m.sender_id != user_id and not m.is_read)
        summaries.append({
            "id": conversation.id,
            "other_user": other_user,
            "property_id": conversation.property_id,
            "property_title": conversation.property.title if conversation.property else None,
            "last_message": last_message.text if last_message else None,
            "last_message_at": last_message.created_at if last_message else None,
            "unread_count": unread_count,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
        })
    return summaries


# Community posts
async def list_community_posts(db: AsyncSession) -> List[CommunityPost]:
    result = await db.execute(select(CommunityPost).order_by(CommunityPost.created_at.desc()))
    return list(result.scalars().all())


async def create_community_post(
    db: AsyncSession, post_data: CommunityPostCreate, posted_by_id: str
) -> CommunityPost:
    post = CommunityPost(
        id=str(uuid.uuid4()),
        title=post_data.title,
        body=post_data.body,
        image_url=post_data.image_url,
        posted_by_id=posted_by_id,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post
