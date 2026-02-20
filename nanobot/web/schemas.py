"""Pydantic schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    user_id: str
    title: Optional[str] = "新对话"
    channel: Optional[str] = "web"


class CreateConversationResponse(BaseModel):
    """Response after creating a conversation."""
    id: str
    user_id: str
    title: str
    channel: str
    message_count: int
    created_at: Optional[str] = None


class UpdateTitleRequest(BaseModel):
    """Request to update conversation title."""
    title: str


class MessageRequest(BaseModel):
    """Request to send a message."""
    conversation_id: str
    content: str
    role: Optional[str] = "user"
    metadata: Optional[dict] = None


class MessageResponse(BaseModel):
    """Response for a message."""
    id: str
    conversation_id: str
    role: str
    content: str
    metadata: Optional[dict] = None
    created_at: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database: Optional[bool] = None
    channels: Optional[dict] = None


class StatusResponse(BaseModel):
    """Status response."""
    enabled: bool
    running: bool


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None


# WebSocket message schemas
class WSMessage(BaseModel):
    """WebSocket message base schema."""
    type: str  # message, error, status, title_generated, etc.
    data: dict


class WSMessageData(BaseModel):
    """Data for a chat message."""
    conversation_id: str
    content: str
    role: str  # user or assistant
    timestamp: Optional[str] = None


class WSTitleGeneratedData(BaseModel):
    """Data for title generation event."""
    conversation_id: str
    title: str


class WSErrorData(BaseModel):
    """Data for error event."""
    message: str
    code: Optional[str] = None
