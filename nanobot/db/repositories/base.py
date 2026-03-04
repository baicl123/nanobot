"""Base repository class for memory operations."""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator
import json

from loguru import logger


class BaseMemoryRepository(ABC):
    """Base repository with dual-write (SQLite + filesystem)."""

    def __init__(self, workspace: Path, db):
        self.workspace = workspace
        self.db = db

    @asynccontextmanager
    async def _transaction(self):
        """Transaction context with rollback on error."""
        async with self.db.get_connection() as conn:
            try:
                await conn.begin_transaction()
                yield conn
                await conn.commit()
            except Exception as e:
                await conn.rollback()
                logger.error(f"Transaction rolled back: {e}")
                raise

    async def _write_file_backup(self, file_path: Path, content: str) -> bool:
        """Write backup to filesystem (non-blocking)."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')
            return True
        except Exception as e:
            logger.warning(f"Filesystem backup failed: {e}")
            return False

    def _generate_id(self) -> str:
        """Generate unique ID."""
        import uuid
        return str(uuid.uuid4())
