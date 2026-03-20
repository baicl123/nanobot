"""Database operations for web channel."""

import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from nanobot.web.models import Base, SessionMetaModel, SessionMeta
from nanobot.config import load_config

# Get database path from config
config = load_config()
db_path = Path(config.workspace_path) / "web.db"

# Create engine - SQLite不需要连接池，使用NullPool避免连接耗尽
from sqlalchemy.pool import NullPool
engine = create_engine(
    f"sqlite:///{db_path}",
    connect_args={"check_same_thread": False},
    poolclass=NullPool
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database and create tables if they don't exist."""
    # Ensure workspace directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Create tables
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_session(session: SessionMeta) -> SessionMeta:
    """Create a new session metadata entry."""
    db = next(get_db())
    db_session = SessionMetaModel(
        session_id=session.session_id,
        user_id=session.user_id,
        name=session.name,
        created_at=session.created_at,
        updated_at=session.updated_at,
        last_message=session.last_message,
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return SessionMeta.from_orm(db_session)


def get_session_meta(session_id: str) -> Optional[SessionMeta]:
    """Get session metadata by session ID."""
    db = next(get_db())
    db_session = db.query(SessionMetaModel).filter(SessionMetaModel.session_id == session_id).first()
    return SessionMeta.from_orm(db_session) if db_session else None


def update_session(session: SessionMeta) -> Optional[SessionMeta]:
    """Update session metadata."""
    db = next(get_db())
    db_session = db.query(SessionMetaModel).filter(SessionMetaModel.session_id == session.session_id).first()
    if not db_session:
        return None

    db_session.name = session.name
    db_session.updated_at = session.updated_at
    db_session.last_message = session.last_message

    db.commit()
    db.refresh(db_session)
    return SessionMeta.from_orm(db_session)


def delete_session(session_id: str) -> bool:
    """Delete a session metadata entry."""
    db = next(get_db())
    db_session = db.query(SessionMetaModel).filter(SessionMetaModel.session_id == session_id).first()
    if not db_session:
        return False

    db.delete(db_session)
    db.commit()
    return True


def list_user_sessions(user_id: str) -> List[SessionMeta]:
    """List all sessions for a user, ordered by updated_at descending."""
    db = next(get_db())
    db_sessions = db.query(SessionMetaModel)\
        .filter(SessionMetaModel.user_id == user_id)\
        .order_by(SessionMetaModel.updated_at.desc())\
        .all()
    return [SessionMeta.from_orm(s) for s in db_sessions]
