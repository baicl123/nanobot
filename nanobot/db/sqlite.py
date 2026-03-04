"""SQLite implementation of database layer."""

import aiosqlite
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator
import logging

from nanobot.db.base import Database, DatabaseConnection

logger = logging.getLogger(__name__)


class SQLiteConnection(DatabaseConnection):
    """SQLite connection wrapper."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Establish SQLite connection."""
        # Use check_same_thread=False to allow cross-thread access
        self._conn = await aiosqlite.connect(self.db_path, check_same_thread=False)
        # Enable autocommit mode to avoid nested transaction issues
        # We'll manage transactions explicitly
        self._conn.isolation_level = None
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._conn.execute("PRAGMA journal_mode = WAL")
        await self._conn.execute("PRAGMA synchronous = NORMAL")

    async def disconnect(self) -> None:
        """Close SQLite connection."""
        if self._conn:
            await self._conn.close()

    @asynccontextmanager
    async def get_cursor(self, dict_cursor: bool = False):
        """Get SQLite cursor."""
        if self._conn is None:
            raise RuntimeError("Connection not established")

        # aiosqlite's row factory for dict-like access
        if dict_cursor:
            self._conn.row_factory = aiosqlite.Row
        else:
            self._conn.row_factory = None

        async with self._conn.cursor() as cursor:
            yield cursor

    async def execute(self, sql: str, params: tuple = None):
        """Execute SQL statement."""
        if self._conn is None:
            raise RuntimeError("Connection not established")
        return await self._conn.execute(sql, params or ())

    async def execute_many(self, sql: str, params_list: list):
        """Execute multiple SQL statements."""
        if self._conn is None:
            raise RuntimeError("Connection not established")
        return await self._conn.executemany(sql, params_list)

    async def executescript(self, sql: str):
        """Execute multiple SQL statements as a script."""
        if self._conn is None:
            raise RuntimeError("Connection not established")
        return await self._conn.executescript(sql)

    async def begin_transaction(self):
        """Begin transaction."""
        if self._conn is None:
            raise RuntimeError("Connection not established")
        await self._conn.execute("BEGIN")

    async def commit(self):
        """Commit transaction."""
        if self._conn is None:
            raise RuntimeError("Connection not established")
        await self._conn.commit()

    async def rollback(self):
        """Rollback transaction."""
        if self._conn is None:
            raise RuntimeError("Connection not established")
        await self._conn.rollback()


class SQLiteDatabase(Database):
    """SQLite database manager."""

    def __init__(self, db_path: str | Path, config: dict | None = None):
        super().__init__(config)
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: SQLiteConnection | None = None

    async def connect(self) -> None:
        """Initialize SQLite database."""
        self._connection = SQLiteConnection(self.db_path)
        await self._connection.connect()
        logger.info(f"SQLite database connected: {self.db_path}")

    async def disconnect(self) -> None:
        """Close SQLite database."""
        if self._connection:
            await self._connection.disconnect()

    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[SQLiteConnection]:
        """Get SQLite connection."""
        if self._connection is None:
            await self.connect()
        yield self._connection

    async def health_check(self) -> bool:
        """Check if SQLite database is accessible."""
        try:
            async with self.get_connection() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
