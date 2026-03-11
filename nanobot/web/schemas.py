"""API schemas for web channel."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class SessionCreateRequest(BaseModel):
    """Request schema for creating a new session."""
    name: str = "New Chat"


class SessionUpdateRequest(BaseModel):
    """Request schema for updating a session."""
    name: str


class SessionResponse(BaseModel):
    """Response schema for session metadata."""
    session_id: str
    user_id: str
    name: str
    created_at: datetime
    updated_at: datetime
    last_message: str


class SessionListResponse(BaseModel):
    """Response schema for listing user sessions."""
    sessions: List[SessionResponse]


class MessageRequest(BaseModel):
    """Request schema for sending a message."""
    content: str
    session_id: str


class MessageResponse(BaseModel):
    """Response schema for chat messages."""
    type: str = "message"
    session_id: str
    content: str
    role: str
    metadata: Dict[str, Any] = {}
    is_progress: bool = False
    is_tool_hint: bool = False


class ErrorResponse(BaseModel):
    """Response schema for errors."""
    type: str = "error"
    message: str
