"""Web channel module for nanobot."""

from nanobot.web.database import Database, get_database, init_database, close_database

__all__ = ["Database", "get_database", "init_database", "close_database"]
