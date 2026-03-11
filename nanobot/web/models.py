"""SQLAlchemy models for web channel data."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel


Base = declarative_base()


class SessionMetaModel(Base):
    """SQLAlchemy model for session metadata."""
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False, default="New Chat")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_message = Column(Text, nullable=False, default="")


class SessionMeta(BaseModel):
    """Pydantic model for session metadata."""
    session_id: str
    user_id: str
    name: str
    created_at: datetime
    updated_at: datetime
    last_message: str

    class Config:
        from_attributes = True
