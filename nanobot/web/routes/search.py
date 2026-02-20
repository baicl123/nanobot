"""API routes for search functionality."""

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from nanobot.web.repositories.message_repo import MessageRepository

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/messages")
async def search_messages(
    q: str = Query(..., description="Search keyword"),
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(20, description="Maximum number of results", ge=1, le=100)
):
    """Search messages across all conversations using fulltext search."""
    try:
        if not q or len(q.strip()) == 0:
            raise HTTPException(status_code=400, detail="Search query cannot be empty")

        msg_repo = MessageRepository()
        results = await msg_repo.search(user_id=user_id, keyword=q, limit=limit)
        return {"query": q, "count": len(results), "results": results}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))
