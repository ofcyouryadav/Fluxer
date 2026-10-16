import aiosqlite
import asyncio
import logging
from typing import Optional, Any, List, Dict
from contextlib import asynccontextmanager
from pathlib import Path

logger = logging.getLogger(__name__)

class AsyncDatabase:
    def __init__(self, db_path: str = "bot_database.db"):
        self.db_path = db_path
        self.pool: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize database and create tables"""
        async with self._get_connection() as db:
            # Create tables with proper indexing
            await db.execute("""
                CREATE TABLE IF NOT EXISTS channel_data (
                    guild_id INTEGER PRIMARY KEY,
                    voice_channel_id INTEGER,
                    text_channel_id INTEGER,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS music_settings (
                    guild_id INTEGER PRIMARY KEY,
                    volume INTEGER DEFAULT 100,
                    dj_role_id INTEGER,
                    auto_play BOOLEAN DEFAULT FALSE,
                    auto_shuffle BOOLEAN DEFAULT FALSE,
                    announce_songs BOOLEAN DEFAULT TRUE,
                    max_queue_length INTEGER DEFAULT 500,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    name TEXT NOT NULL,
                    tracks TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, user_id, name)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_prefixes (
                    guild_id INTEGER PRIMARY KEY,
                    prefix TEXT NOT NULL DEFAULT '!',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS dj_roles (
                    guild_id INTEGER PRIMARY KEY,
                    role_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS embed_settings (
                    guild_id INTEGER PRIMARY KEY,
                    embed_style TEXT DEFAULT 'default',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS mode_247_settings (
                    guild_id INTEGER PRIMARY KEY,
                    enabled BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS music_source_settings (
                    guild_id INTEGER PRIMARY KEY,
                    source TEXT DEFAULT 'ytmsearch',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS no_prefix_settings (
                    guild_id INTEGER PRIMARY KEY,
                    user_ids TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS ignored_channels (
                    guild_id INTEGER PRIMARY KEY,
                    channel_ids TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS ignore_bypass_roles (
                    guild_id INTEGER PRIMARY KEY,
                    role_ids TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            logger.info("Database tables initialized")
            await db.commit()

    @asynccontextmanager
    async def _get_connection(self):
        """Get a database connection with automatic cleanup"""
        if not self.pool:
            async with self._lock:
                if not self.pool:
                    self.pool = await aiosqlite.connect(
                        self.db_path,
                        isolation_level=None  # Enable autocommit mode
                    )
                    await self.pool.execute("PRAGMA journal_mode=WAL")
                    await self.pool.execute("PRAGMA synchronous=NORMAL")
                    await self.pool.execute("PRAGMA temp_store=MEMORY")
                    self.pool.row_factory = aiosqlite.Row

        try:
            yield self.pool
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise

    async def execute(self, query: str, params: tuple = ()) -> Any:
        """Execute a SQL query with parameters"""
        async with self._get_connection() as db:
            try:
                async with db.execute(query, params) as cursor:
                    await db.commit()
                    return cursor.lastrowid
            except Exception as e:
                logger.error(f"Error executing query: {query} with params {params}: {e}")
                raise

    async def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch a single row from the database"""
        async with self._get_connection() as db:
            try:
                async with db.execute(query, params) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
            except Exception as e:
                logger.error(f"Error fetching row: {query} with params {params}: {e}")
                raise

    async def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows from the database"""
        async with self._get_connection() as db:
            try:
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"Error fetching rows: {query} with params {params}: {e}")
                raise

    async def close(self) -> None:
        """Close the database connection"""
        if self.pool:
            await self.pool.close()
            self.pool = None

# Create global database instance
db = AsyncDatabase()

async def get_db() -> AsyncDatabase:
    """Get the database instance"""
    return db