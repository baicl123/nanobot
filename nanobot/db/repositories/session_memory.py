"""Session-level memory repository (single-session short-term memory)."""

from pathlib import Path
from typing import Any
from datetime import datetime

from loguru import logger

from nanobot.db.repositories.base import BaseMemoryRepository


class SessionMemoryRepository(BaseMemoryRepository):
    """
    Repository for session memories.

    Each session has exactly ONE memory record (consolidated summary).
    Content is a condensed summary of old messages.
    """

    def __init__(self, workspace: Path, db):
        super().__init__(workspace, db)

    def _get_session_memory_dir(self, session_id: str) -> Path:
        """Get session memory directory for filesystem backup."""
        return self.workspace / "memory" / "sessions" / session_id

    async def get_session_memory(self, session_id: str) -> str:
        """
        Get session's consolidated summary.

        Args:
            session_id: Session identifier (e.g., "web:60079031:conv-001")

        Returns:
            Summary content, or empty string if not exists
        """
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT content FROM session_memories WHERE session_id = ?",
                (session_id,)
            )
            row = await cursor.fetchone()
            return row[0] if row else ""

    async def update_session_memory(
        self,
        session_id: str,
        content: str,
        message_count: int = 0
    ) -> bool:
        """
        Update session's consolidated summary (complete replacement).

        Args:
            session_id: Session identifier
            content: Consolidated summary text
            message_count: How many old messages this summary covers

        Returns:
            True if updated/inserted successfully
        """
        now = datetime.now().isoformat()

        async with self._transaction() as conn:
            # Try update first
            cursor = await conn.execute(
                """
                UPDATE session_memories
                SET content = ?, message_count = ?, last_message_at = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (content, message_count, now, now, session_id)
            )
            updated = cursor.rowcount > 0

            # If not exists, insert
            if not updated:
                await conn.execute(
                    """
                    INSERT INTO session_memories (session_id, content, message_count, last_message_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (session_id, content, message_count, now, now)
                )

            # Filesystem backup
            memory_dir = self._get_session_memory_dir(session_id)
            summary_file = memory_dir / "SUMMARY.md"
            await self._write_file_backup(summary_file, content)

        logger.info(f"Updated session memory: {session_id}, covering {message_count} messages")
        return True

    async def get_active_sessions(self, user_id: str) -> list[dict]:
        """
        Get user's active sessions (with memory).

        Args:
            user_id: User identifier

        Returns:
            List of sessions with their summary info
        """
        async with self.db.get_connection() as conn:
            # Use dict_cursor for dict-like row access
            async with conn.get_cursor(dict_cursor=True) as cursor:
                await cursor.execute(
                    """
                    SELECT session_id, message_count, last_message_at, updated_at
                    FROM session_memories
                    WHERE session_id LIKE ?
                    ORDER BY last_message_at DESC
                    """,
                    (f"web:{user_id}:%",)
                )
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
