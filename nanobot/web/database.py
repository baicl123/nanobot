"""Database connection pool for seekdb."""

import aiomysql
from contextlib import asynccontextmanager
from loguru import logger
from typing import AsyncGenerator, Optional


class Database:
    """Database connection pool manager."""

    def __init__(self, host: str, port: int, user: str, password: str, db: str, pool_size: int = 10):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db
        self.pool_size = pool_size
        self.pool: Optional[aiomysql.Pool] = None

    async def create_pool(self) -> None:
        """Create the database connection pool."""
        try:
            self.pool = await aiomysql.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=self.db,
                minsize=5,
                maxsize=self.pool_size,
                autocommit=False,
                charset='utf8mb4'
            )
            logger.info(f"Database connection pool created: {self.host}:{self.port}/{self.db}")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[aiomysql.Connection, None]:
        """Get a database connection from the pool."""
        if self.pool is None:
            raise RuntimeError("Database pool not initialized. Call create_pool() first.")

        async with self.pool.acquire() as conn:
            yield conn

    async def close(self) -> None:
        """Close the database connection pool."""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            logger.info("Database connection pool closed")

    async def health_check(self) -> bool:
        """Check if database connection is healthy."""
        try:
            async with self.get_connection() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    result = await cursor.fetchone()
                    return result is not None
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database instance (will be initialized with config)
_db: Optional[Database] = None


def get_database() -> Optional[Database]:
    """Get the global database instance."""
    return _db


async def init_database(host: str, port: int, user: str, password: str, db: str, pool_size: int = 10) -> Database:
    """Initialize the global database instance."""
    global _db
    _db = Database(host, port, user, password, db, pool_size)
    await _db.create_pool()
    return _db


async def close_database() -> None:
    """Close the global database instance."""
    global _db
    if _db:
        await _db.close()
        _db = None
