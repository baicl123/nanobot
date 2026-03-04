"""Database schema migrations."""

from pathlib import Path
from typing import Any
from aiosqlite import Connection
from loguru import logger


class Migration:
    """Base migration class."""

    version: str = "001"
    name: str = "base_schema"
    sql: str = ""

    async def up(self, conn: Connection) -> None:
        """Apply migration."""
        await conn.executescript(self.sql)
        logger.info(f"Migration {self.version}_{self.name} applied")

    async def down(self, conn: Connection) -> None:
        """Rollback migration."""
        pass


class CreateMemoryTables(Migration):
    """Create user_memories and session_memories tables (simplified design)."""

    version = "001"
    name = "create_memory_tables"
    sql = """
    -- 用户记忆表（跨会话长期记忆）
    -- 每个用户只有 1 条记录，存储完整的 Markdown 文本
    CREATE TABLE IF NOT EXISTS user_memories (
        user_id VARCHAR(255) PRIMARY KEY,
        content TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metadata JSON
    );

    -- 会话记忆表（单会话短期记忆）
    -- 每个会话只有 1 条记录，存储旧消息的浓缩摘要
    CREATE TABLE IF NOT EXISTS session_memories (
        session_id VARCHAR(64) PRIMARY KEY,
        content TEXT NOT NULL,
        message_count INT DEFAULT 0,
        last_message_at TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metadata JSON
    );

    -- 迁移记录表（用于跟踪版本）
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version VARCHAR(20) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    async def down(self, conn: Connection) -> None:
        """Rollback migration."""
        await conn.execute("DROP TABLE IF EXISTS session_memories")
        await conn.execute("DROP TABLE IF EXISTS user_memories")
        await conn.execute("DROP TABLE IF EXISTS schema_migrations")


MIGRATIONS = [
    CreateMemoryTables(),
]


async def run_migrations(conn: Connection, target_version: str | None = None) -> None:
    """Run pending migrations."""
    # Ensure migrations table exists
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(20) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Get applied migrations
    cursor = await conn.execute("SELECT version FROM schema_migrations ORDER BY version")
    applied_rows = await cursor.fetchall()
    applied_versions = {row[0] for row in applied_rows}

    # Run pending migrations
    for migration in MIGRATIONS:
        if migration.version not in applied_versions:
            await migration.up(conn)
            await conn.execute(
                "INSERT INTO schema_migrations (version, name) VALUES (?, ?)",
                (migration.version, migration.name)
            )
            logger.info(f"Applied migration: {migration.version}_{migration.name}")
        else:
            logger.info(f"Migration already applied: {migration.version}_{migration.name}")


async def get_current_version(conn: Connection) -> str:
    """Get current schema version."""
    cursor = await conn.execute(
        "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1"
    )
    row = await cursor.fetchone()
    return row[0] if row else "000"
