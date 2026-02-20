"""Initialize seekdb database tables for nanobot web channel."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import nanobot modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from loguru import logger
from nanobot.config.loader import load_config
from nanobot.web.database import init_database, close_database


async def init_tables():
    """Create database tables if they don't exist."""

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.warning(f"Could not load config: {e}. Using default values.")
        # Use default values for testing
        db_config = type('obj', (object,), {
            'host': '127.0.0.1',
            'port': 2881,
            'user': 'root',
            'password': 'seekdb',
            'database': 'nanobot',
            'pool_size': 10
        })()
    else:
        db_config = config.database

    # Initialize database connection
    logger.info(f"Connecting to database at {db_config.host}:{db_config.port}/{db_config.database}")
    db = await init_database(
        host=db_config.host,
        port=db_config.port,
        user=db_config.user,
        password=db_config.password,
        db=db_config.database,
        pool_size=db_config.pool_size
    )

    # Create tables
    async with db.get_connection() as conn:
        async with conn.cursor() as cursor:
            # Create conversations table
            logger.info("Creating conversations table...")
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id VARCHAR(64) PRIMARY KEY COMMENT '会话ID (UUID)',
                    user_id VARCHAR(255) NOT NULL COMMENT '用户ID',
                    channel VARCHAR(50) NOT NULL COMMENT '渠道: web/telegram/whatsapp等',
                    title VARCHAR(500) NOT NULL DEFAULT '新对话' COMMENT '会话标题',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    message_count INT DEFAULT 0 COMMENT '消息数量',
                    metadata JSON COMMENT '元数据',
                    INDEX idx_user_updated (user_id, updated_at DESC),
                    INDEX idx_channel (channel)
                ) COMMENT='会话表'
            """)

            # Create messages table
            logger.info("Creating messages table...")
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id VARCHAR(64) PRIMARY KEY COMMENT '消息ID (UUID)',
                    conversation_id VARCHAR(64) NOT NULL COMMENT '会话ID',
                    role ENUM('user', 'assistant', 'system') NOT NULL COMMENT '角色',
                    content TEXT NOT NULL COMMENT '消息内容',
                    metadata JSON COMMENT '元数据',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    INDEX idx_conversation_created (conversation_id, created_at),
                    FULLTEXT INDEX ft_content (content) WITH (parser='ngram'),
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                ) COMMENT='消息表'
            """)

            await conn.commit()

    logger.success("✓ seekdb database tables initialized successfully")
    await close_database()


async def drop_tables():
    """Drop all tables (for testing/reset)."""
    logger.warning("This will drop all tables and data. Press Ctrl+C to cancel.")
    await asyncio.sleep(3)

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.warning(f"Could not load config: {e}. Using default values.")
        db_config = type('obj', (object,), {
            'host': '127.0.0.1',
            'port': 2881,
            'user': 'root',
            'password': 'seekdb',
            'database': 'nanobot',
        })()
    else:
        db_config = config.database

    # Initialize database connection
    db = await init_database(
        host=db_config.host,
        port=db_config.port,
        user=db_config.user,
        password=db_config.password,
        db=db_config.database,
        pool_size=1
    )

    async with db.get_connection() as conn:
        async with conn.cursor() as cursor:
            logger.info("Dropping messages table...")
            await cursor.execute("DROP TABLE IF EXISTS messages")
            logger.info("Dropping conversations table...")
            await cursor.execute("DROP TABLE IF EXISTS conversations")
            await conn.commit()

    logger.success("✓ Tables dropped successfully")
    await close_database()


async def show_tables():
    """Show existing tables."""
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        db_config = type('obj', (object,), {
            'host': '127.0.0.1',
            'port': 2881,
            'user': 'root',
            'password': 'seekdb',
            'database': 'nanobot',
        })()
    else:
        db_config = config.database

    db = await init_database(
        host=db_config.host,
        port=db_config.port,
        user=db_config.user,
        password=db_config.password,
        db=db_config.database,
        pool_size=1
    )

    async with db.get_connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SHOW TABLES")
            tables = await cursor.fetchall()
            if tables:
                logger.info(f"Tables in {db_config.database}:")
                for table in tables:
                    logger.info(f"  - {table[0]}")
            else:
                logger.info(f"No tables found in {db_config.database}")

    await close_database()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage nanobot seekdb database")
    parser.add_argument("command", choices=["init", "drop", "show"], help="Command to run")
    args = parser.parse_args()

    if args.command == "init":
        asyncio.run(init_tables())
    elif args.command == "drop":
        asyncio.run(drop_tables())
    elif args.command == "show":
        asyncio.run(show_tables())
