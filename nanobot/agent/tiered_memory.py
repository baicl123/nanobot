"""Two-tier memory system: UserMemory + SessionMemory."""

from pathlib import Path
from typing import Any
from loguru import logger

from nanobot.db.repositories.user_memory import UserMemoryRepository
from nanobot.db.repositories.session_memory import SessionMemoryRepository
from nanobot.db.sqlite import SQLiteDatabase


class TieredMemoryManager:
    """
    Manager for two-tier memory system.

    - UserMemory: Cross-session long-term memory (1 record per user)
    - SessionMemory: Single-session consolidated summary (1 record per session)
    """

    def __init__(self, workspace: Path, db_path: str | Path = None):
        self.workspace = workspace

        # Initialize SQLite database
        if db_path is None:
            db_path = workspace / "nanobot.db"
        self.db = SQLiteDatabase(db_path)

        # Repositories
        self.user_memory: UserMemoryRepository | None = None
        self.session_memory: SessionMemoryRepository | None = None

    async def initialize(self) -> None:
        """Initialize database and repositories."""
        await self.db.connect()

        # Run migrations
        from nanobot.db.migrations import run_migrations
        async with self.db.get_connection() as conn:
            await run_migrations(conn)

        # Initialize repositories
        self.user_memory = UserMemoryRepository(self.workspace, self.db)
        self.session_memory = SessionMemoryRepository(self.workspace, self.db)

        logger.info("TieredMemoryManager initialized")

    async def close(self) -> None:
        """Close database connection."""
        await self.db.disconnect()

    async def get_user_context(self, user_id: str) -> str:
        """
        Get user-level memory context for LLM.

        Returns:
            Formatted user memory (cross-session facts, preferences, etc.)
        """
        if self.user_memory is None:
            return ""
        return await self.user_memory.get_memory_context(user_id)

    async def get_session_summary(self, session_id: str) -> str:
        """
        Get session's consolidated summary.

        Returns:
            Summary text of old messages in this session
        """
        if self.session_memory is None:
            return ""
        return await self.session_memory.get_session_memory(session_id)

    async def update_session_summary(
        self,
        session_id: str,
        summary: str,
        message_count: int = 0
    ) -> bool:
        """
        Update session's consolidated summary.

        Args:
            session_id: Session identifier
            summary: New consolidated summary (replaces old one)
            message_count: How many old messages this summary covers

        Returns:
            True if successful
        """
        if self.session_memory is None:
            raise RuntimeError("TieredMemoryManager not initialized")

        return await self.session_memory.update_session_memory(
            session_id=session_id,
            content=summary,
            message_count=message_count
        )

    async def consolidate_to_user_memory(
        self,
        user_id: str,
        session_summary: str
    ) -> bool:
        """
        Consolidate session summary into user memory.

        Called when a session ends or has important information.

        Args:
            user_id: User identifier
            session_summary: Summary of the session to extract facts from

        Returns:
            True if successful
        """
        if self.user_memory is None:
            raise RuntimeError("TieredMemoryManager not initialized")

        # Get existing user memory
        existing = await self.user_memory.get_user_memory(user_id)

        # Append session summary to user memory
        # In production, you'd use LLM to extract key facts
        new_content = existing + f"\n\n## Session Summary\n{session_summary}\n"

        await self.user_memory.update_user_memory(user_id, new_content)

        logger.info(f"Consolidated session to user memory: {user_id}")
        return True

    async def get_session_context(
        self,
        session_id: str,
        message_repo,
        recent_message_count: int = 50
    ) -> str:
        """
        Get complete session context: summary + recent messages.

        This is what you inject into LLM prompt.

        Args:
            session_id: Session identifier
            message_repo: MessageRepository instance
            recent_message_count: How many recent messages to include

        Returns:
            Formatted context string
        """
        # Get session summary (old messages)
        summary = await self.get_session_summary(session_id)

        # Get recent messages (new messages)
        recent_messages = await message_repo.get_by_conversation(
            session_id.split(':')[-1],  # Extract conversation_id from session_id
            limit=recent_message_count
        )

        # Build context
        context = ""
        if summary:
            context += f"## Previous Conversation Summary\n{summary}\n\n"

        context += "## Recent Messages\n"
        for msg in recent_messages:
            context += f"{msg['role']}: {msg['content']}\n"

        return context
