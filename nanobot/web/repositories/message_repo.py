"""Message repository for database operations."""

import uuid
import json
from loguru import logger
from nanobot.web.database import get_database


class MessageRepository:
    """Repository for message data access."""

    async def add(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict | None = None
    ) -> str:
        """Add a message to a conversation."""
        msg_id = str(uuid.uuid4())
        db = get_database()
        if db is None:
            raise RuntimeError("Database not initialized")

        # Serialize metadata to JSON
        metadata_json = json.dumps(metadata) if metadata else None

        async with db.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    INSERT INTO messages (id, conversation_id, role, content, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                """, (msg_id, conversation_id, role, content, metadata_json))
                await conn.commit()

        logger.debug(f"Added message {msg_id} to conversation {conversation_id}")
        return msg_id

    async def get_by_conversation(self, conversation_id: str, limit: int = 100) -> list[dict]:
        """Get messages for a conversation."""
        db = get_database()
        if db is None:
            return []

        async with db.get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT id, role, content, metadata, created_at
                    FROM messages
                    WHERE conversation_id = %s
                    ORDER BY created_at ASC
                    LIMIT %s
                """, (conversation_id, limit))
                results = await cursor.fetchall()

        # Convert datetime and parse JSON metadata
        for row in results:
            if row.get("created_at"):
                row["created_at"] = row["created_at"].isoformat()
            if row.get("metadata"):
                try:
                    row["metadata"] = json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"]
                except (json.JSONDecodeError, TypeError):
                    row["metadata"] = {}

        return results

    async def search(
        self,
        user_id: str,
        keyword: str,
        limit: int = 20
    ) -> list[dict]:
        """Search messages across conversations using fulltext search."""
        db = get_database()
        if db is None:
            return []

        async with db.get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT m.id, m.content, m.role, m.created_at,
                           c.title, c.id as conversation_id
                    FROM messages m
                    JOIN conversations c ON m.conversation_id = c.id
                    WHERE c.user_id = %s
                    AND MATCH(m.content) AGAINST(%s IN NATURAL LANGUAGE MODE)
                    ORDER BY m.created_at DESC
                    LIMIT %s
                """, (user_id, keyword, limit))
                results = await cursor.fetchall()

        # Convert datetime
        for row in results:
            if row.get("created_at"):
                row["created_at"] = row["created_at"].isoformat()

        return results

    async def delete_by_conversation(self, conversation_id: str) -> int:
        """Delete all messages in a conversation."""
        db = get_database()
        if db is None:
            return 0

        async with db.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    DELETE FROM messages WHERE conversation_id = %s
                """, (conversation_id,))
                await conn.commit()
                deleted = cursor.rowcount

        logger.debug(f"Deleted {deleted} messages from conversation {conversation_id}")
        return deleted

    async def count(self, conversation_id: str) -> int:
        """Count messages in a conversation."""
        db = get_database()
        if db is None:
            return 0

        async with db.get_connection() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT COUNT(*) FROM messages WHERE conversation_id = %s
                """, (conversation_id,))
                result = await cursor.fetchone()

        return result[0] if result else 0

    async def get_first_message(self, conversation_id: str) -> dict | None:
        """Get the first message in a conversation."""
        db = get_database()
        if db is None:
            return None

        async with db.get_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("""
                    SELECT id, role, content, metadata, created_at
                    FROM messages
                    WHERE conversation_id = %s
                    ORDER BY created_at ASC
                    LIMIT 1
                """, (conversation_id,))
                result = await cursor.fetchone()

        if result and result.get("created_at"):
            result["created_at"] = result["created_at"].isoformat()

        return result
