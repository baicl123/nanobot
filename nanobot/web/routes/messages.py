"""API routes for message management."""

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from nanobot.web.repositories.message_repo import MessageRepository
from nanobot.web.repositories.conversation_repo import ConversationRepository
from nanobot.web.schemas import MessageRequest, MessageResponse

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("/{conversation_id}")
async def get_messages(
    conversation_id: str,
    limit: int = Query(100, description="Maximum number of messages", ge=1, le=500)
):
    """Get messages for a conversation."""
    try:
        # Check if conversation exists
        conv_repo = ConversationRepository()
        exists = await conv_repo.exists(conversation_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get messages
        msg_repo = MessageRepository()
        messages = await msg_repo.get_by_conversation(conversation_id, limit)
        return {"conversation_id": conversation_id, "messages": messages}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_message(request: MessageRequest):
    """Create a new message."""
    try:
        # Check if conversation exists
        conv_repo = ConversationRepository()
        exists = await conv_repo.exists(request.conversation_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Create message
        msg_repo = MessageRepository()
        msg_id = await msg_repo.add(
            conversation_id=request.conversation_id,
            role=request.role,
            content=request.content,
            metadata=request.metadata
        )

        # Increment conversation message count
        await conv_repo.increment_count(request.conversation_id)

        return {
            "success": True,
            "message_id": msg_id,
            "conversation_id": request.conversation_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/count")
async def get_message_count(conversation_id: str):
    """Get message count for a conversation."""
    try:
        msg_repo = MessageRepository()
        count = await msg_repo.count(conversation_id)
        return {"conversation_id": conversation_id, "count": count}
    except Exception as e:
        logger.error(f"Error getting message count: {e}")
        raise HTTPException(status_code=500, detail=str(e))
