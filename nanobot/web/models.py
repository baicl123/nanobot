"""SQLAlchemy models for web channel data."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel


Base = declarative_base()


class UserModel(Base):
    """SQLAlchemy model for user information."""
    __tablename__ = "users"

    emp_id = Column(String, primary_key=True, index=True)
    deptname = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_active_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    display_name = Column(String, nullable=True)

    # Relationship to sessions
    sessions = relationship("SessionMetaModel", back_populates="user")


class SessionMetaModel(Base):
    """SQLAlchemy model for session metadata."""
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True, index=True)
    emp_id = Column(String, ForeignKey("users.emp_id"), nullable=False, index=True)
    name = Column(String, nullable=False, default="New Chat")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_message = Column(Text, nullable=False, default="")

    # Relationship to user
    user = relationship("UserModel", back_populates="sessions")


class User(BaseModel):
    """Pydantic model for user information."""
    emp_id: str
    deptname: Optional[str] = None
    created_at: datetime
    last_active_at: datetime
    display_name: Optional[str] = None

    class Config:
        from_attributes = True


class SessionMeta(BaseModel):
    """Pydantic model for session metadata."""
    session_id: str
    emp_id: str
    name: str
    created_at: datetime
    updated_at: datetime
    last_message: str

    class Config:
        from_attributes = True
