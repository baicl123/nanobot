"""API routes for conversation management."""

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from nanobot.web.repositories.conversation_repo import ConversationRepository
from nanobot.web.schemas import (
    CreateConversationRequest,
    CreateConversationResponse,
    UpdateTitleRequest,
    ErrorResponse
)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("/", response_model=CreateConversationResponse)
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation."""
    try:
        repo = ConversationRepository()
        result = await repo.create(
            user_id=request.user_id,
            title=request.title or "新对话",
            channel=request.channel or "web"
        )
        return CreateConversationResponse(**result)
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_conversations(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(50, description="Maximum number of conversations", ge=1, le=100)
):
    """Get user's conversations."""
    try:
        repo = ConversationRepository()
        results = await repo.get_by_user(user_id, limit)
        return {"conversations": results}
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a single conversation by ID."""
    try:
        repo = ConversationRepository()
        result = await repo.get(conversation_id)
        if not result:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: str,
    request: UpdateTitleRequest
):
    """Update conversation title."""
    try:
        repo = ConversationRepository()
        exists = await repo.exists(conversation_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Conversation not found")

        await repo.update_title(conversation_id, request.title)
        return {"success": True, "conversation_id": conversation_id, "title": request.title}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating title: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    try:
        repo = ConversationRepository()
        exists = await repo.exists(conversation_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Conversation not found")

        await repo.delete(conversation_id)
        return {"success": True, "conversation_id": conversation_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
