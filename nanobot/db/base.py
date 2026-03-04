"""Database abstraction layer for future database migration."""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator


class DatabaseConnection(ABC):
    """Abstract database connection interface."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish database connection."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    @asynccontextmanager
    async def get_cursor(self, dict_cursor: bool = False) -> AsyncIterator[Any]:
        """Get database cursor."""
        pass

    @abstractmethod
    async def execute(self, sql: str, params: tuple = None) -> Any:
        """Execute SQL statement."""
        pass

    @abstractmethod
    async def execute_many(self, sql: str, params_list: list) -> Any:
        """Execute multiple SQL statements."""
        pass

    @abstractmethod
    async def begin_transaction(self) -> Any:
        """Begin transaction."""
        pass

    @abstractmethod
    async def commit(self) -> Any:
        """Commit transaction."""
        pass

    @abstractmethod
    async def rollback(self) -> Any:
        """Rollback transaction."""
        pass


class Database(ABC):
    """Abstract database manager for supporting multiple databases."""

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self._connection: DatabaseConnection | None = None

    @abstractmethod
    async def connect(self) -> None:
        """Initialize database connection."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection."""
        pass

    @abstractmethod
    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[DatabaseConnection]:
        """Get database connection with context manager."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if database is accessible."""
        pass
