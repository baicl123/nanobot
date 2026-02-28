"""Conversation repository for database operations."""

import uuid
from datetime import datetime
from loguru import logger
from nanobot.web.database import get_database


class ConversationRepository:
    """Repository for conversation data access."""

    async def create(self, user_id: str, title: str = "新对话", channel: str = "web", conv_id: str | None = None) -> dict:
        """Create a new conversation.

        Args:
            user_id: User identifier
            title: Conversation title
            channel: Channel name (web, telegram, etc.)
            conv_id: Optional conversation ID (if not provided, generates UUID)
        """
        if conv_id is None:
            conv_id = str(uuid.uuid4())

        db = get_database()
        if db is None:
            raise RuntimeError("Database not initialized")

        async with db.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO conversations (id, user_id, title, channel)
                    VALUES (%s, %s, %s, %s)
                """, (conv_id, user_id, title, channel))
                await conn.commit()

        logger.debug(f"Created conversation {conv_id} for user {user_id}")
        return {
            "id": conv_id,
            "user_id": user_id,
            "title": title,
            "channel": channel,
            "message_count": 0
        }

    async def get_by_user(self, user_id: str, limit: int = 50) -> list[dict]:
        """Get user's conversations (ordered by updated_at desc)."""
        db = get_database()
        if db is None:
            return []

        async with db.get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT id, title, created_at, updated_at, message_count, channel
                    FROM conversations
                    WHERE user_id = %s
                    ORDER BY updated_at DESC
                    LIMIT %s
                """, (user_id, limit))
                results = await cursor.fetchall()

        # Convert datetime to string for JSON serialization
        for row in results:
            if row.get("created_at"):
                row["created_at"] = row["created_at"].isoformat()
            if row.get("updated_at"):
                row["updated_at"] = row["updated_at"].isoformat()

        return results

    async def get(self, conversation_id: str) -> dict | None:
        """Get a single conversation by ID."""
        db = get_database()
        if db is None:
            return None

        async with db.get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT * FROM conversations WHERE id = %s
                """, (conversation_id,))
                result = await cursor.fetchone()

        if result and result.get("created_at"):
            result["created_at"] = result["created_at"].isoformat()
        if result and result.get("updated_at"):
            result["updated_at"] = result["updated_at"].isoformat()

        return result

    async def update_title(self, conversation_id: str, title: str) -> bool:
        """Update conversation title."""
        db = get_database()
        if db is None:
            return False

        async with db.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    UPDATE conversations SET title = %s WHERE id = %s
                """, (title, conversation_id))
                await conn.commit()

        logger.debug(f"Updated title for conversation {conversation_id}: {title}")
        return True

    async def increment_count(self, conversation_id: str) -> bool:
        """Increment message count."""
        db = get_database()
        if db is None:
            return False

        async with db.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    UPDATE conversations
                    SET message_count = message_count + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (conversation_id,))
                await conn.commit()

        return True

    async def delete(self, conversation_id: str) -> bool:
        """Delete a conversation (cascades to messages)."""
        db = get_database()
        if db is None:
            return False

        async with db.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    DELETE FROM conversations WHERE id = %s
                """, (conversation_id,))
                await conn.commit()

        logger.debug(f"Deleted conversation {conversation_id}")
        return True

    async def exists(self, conversation_id: str) -> bool:
        """Check if a conversation exists."""
        db = get_database()
        if db is None:
            return False

        async with db.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT 1 FROM conversations WHERE id = %s
                """, (conversation_id,))
                result = await cursor.fetchone()

        return result is not None
