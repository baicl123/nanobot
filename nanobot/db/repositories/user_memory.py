"""User-level memory repository (cross-session long-term memory)."""

from pathlib import Path
from typing import Any
from datetime import datetime

from loguru import logger

from nanobot.db.repositories.base import BaseMemoryRepository


class UserMemoryRepository(BaseMemoryRepository):
    """
    Repository for user memories.

    Each user has exactly ONE memory record (like MEMORY.md).
    Content is a complete Markdown text block.
    """

    def __init__(self, workspace: Path, db):
        super().__init__(workspace, db)

    def _get_user_memory_dir(self, user_id: str) -> Path:
        """Get user memory directory for filesystem backup."""
        return self.workspace / "memory" / "users" / user_id

    async def get_user_memory(self, user_id: str) -> str:
        """
        Get user's complete memory content.

        Args:
            user_id: User identifier (e.g., "60079031")

        Returns:
            Markdown formatted memory content, or empty string if not exists
        """
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT content FROM user_memories WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            return row[0] if row else ""

    async def update_user_memory(self, user_id: str, content: str) -> bool:
        """
        Update user's memory (complete replacement).

        Args:
            user_id: User identifier
            content: Complete memory content in Markdown format

        Returns:
            True if updated/inserted successfully
        """
        now = datetime.now().isoformat()

        async with self._transaction() as conn:
            # Try update first
            cursor = await conn.execute(
                "UPDATE user_memories SET content = ?, updated_at = ? WHERE user_id = ?",
                (content, now, user_id)
            )
            updated = cursor.rowcount > 0

            # If not exists, insert
            if not updated:
                await conn.execute(
                    "INSERT INTO user_memories (user_id, content, updated_at) VALUES (?, ?, ?)",
                    (user_id, content, now)
                )

            # Filesystem backup
            memory_dir = self._get_user_memory_dir(user_id)
            memory_file = memory_dir / "MEMORY.md"
            await self._write_file_backup(memory_file, content)

        logger.info(f"Updated user memory: {user_id}")
        return True

    async def get_memory_context(self, user_id: str) -> str:
        """
        Get formatted memory context for LLM.

        Returns:
            Formatted string ready to inject into prompt
        """
        content = await self.get_user_memory(user_id)
        if not content:
            return ""

        return f"## User Memory (Cross-Session)\n{content}\n"
