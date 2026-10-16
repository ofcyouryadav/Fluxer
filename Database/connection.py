"""Database connection handler with proper transaction management"""
import logging
import aiosqlite
import asyncio
from typing import Optional, Any, Callable
from functools import wraps
import os
from datetime import datetime
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class DatabaseConnection:
    _instance = None
    _connection: Optional[aiosqlite.Connection] = None
    _connection_lock = asyncio.Lock()
    _transaction_locks = {}  # Guild-specific transaction locks
    _health_check_interval = 300  # 5 minutes
    _last_health_check = 0

    def __init__(self):
        self.DB_PATH = os.getenv("DATABASE_FILE", "bot_database.db")
        self._retries = int(os.getenv("DB_RETRY_COUNT", "3"))
        self._retry_delay = int(os.getenv("DB_RETRY_DELAY", "1"))
        self._connection_attempts = 0
        self._last_error = None
        self._last_connected = None
        self._is_connected = False

    @classmethod
    async def get_instance(cls):
        """Get or create singleton instance with improved error handling"""
        if not cls._instance:
            async with cls._connection_lock:
                if not cls._instance:
                    cls._instance = DatabaseConnection()
                    try:
                        await cls._instance._connect()
                    except Exception as e:
                        logger.error(f"Failed to initialize database connection: {e}")
                        raise

        current_time = datetime.now().timestamp()
        if current_time - cls._last_health_check > cls._health_check_interval:
            await cls._instance._check_connection_health()
            cls._last_health_check = current_time

        return cls._instance

    async def _connect(self):
        """Establish database connection with proper configuration"""
        try:
            if self._is_connected and self._connection:
                await self._connection.close()
                logger.debug("Closed existing connection")

            self._connection = await aiosqlite.connect(
                self.DB_PATH,
                isolation_level=None,  # Enable autocommit mode
                detect_types=1  # Enable type detection
            )

            # Configure connection for better performance
            await self._connection.execute("PRAGMA journal_mode=WAL")
            await self._connection.execute("PRAGMA synchronous=NORMAL")
            await self._connection.execute("PRAGMA foreign_keys=ON")
            await self._connection.execute("PRAGMA temp_store=MEMORY")
            await self._connection.execute("PRAGMA cache_size=-2000")  # 2MB cache
            self._connection.row_factory = aiosqlite.Row

            self._is_connected = True
            self._last_connected = datetime.now().timestamp()
            logger.info("Successfully connected to SQLite database")

        except Exception as e:
            self._last_error = str(e)
            self._is_connected = False
            logger.error(f"Connection error: {e}")
            raise

    async def _check_connection_health(self):
        """Verify connection health with improved error handling"""
        try:
            if self._is_connected and self._connection:
                async with self._connection.execute("SELECT 1") as cursor:
                    await cursor.fetchone()
                    logger.debug("Database connection health check passed")
            else:
                logger.warning("No active connection during health check")
                await self._connect()
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            await self._connect()

    def get_transaction_lock(self, guild_id: int = None):
        """Get a guild-specific transaction lock"""
        if guild_id not in self._transaction_locks:
            self._transaction_locks[guild_id] = asyncio.Lock()
        return self._transaction_locks[guild_id]

    @asynccontextmanager
    async def transaction(self, guild_id: int = None):
        """Context manager for database transactions with guild-specific locking"""
        if not self._is_connected:
            await self._connect()

        transaction_lock = self.get_transaction_lock(guild_id)
        async with transaction_lock:
            try:
                await self._connection.execute("BEGIN")
                yield self._connection
                await self._connection.commit()
            except Exception as e:
                await self._connection.rollback()
                logger.error(f"Transaction failed for guild {guild_id}: {e}")
                raise

    async def execute(self, query: str, params: tuple = (), guild_id: int = None) -> Any:
        """Execute a query with proper transaction handling"""
        if not self._is_connected:
            await self._connect()

        transaction_lock = self.get_transaction_lock(guild_id)
        async with transaction_lock:
            async with self._connection.execute(query, params) as cursor:
                await self._connection.commit()
                return cursor.lastrowid

    async def fetch_one(self, query: str, params: tuple = (), guild_id: int = None) -> Optional[dict]:
        """Fetch a single row with proper cursor handling"""
        if not self._is_connected:
            await self._connect()

        transaction_lock = self.get_transaction_lock(guild_id)
        async with transaction_lock:
            async with self._connection.execute(query, params) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def fetch_all(self, query: str, params: tuple = (), guild_id: int = None) -> list:
        """Fetch all rows with proper cursor handling"""
        if not self._is_connected:
            await self._connect()

        transaction_lock = self.get_transaction_lock(guild_id)
        async with transaction_lock:
            async with self._connection.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def close(self):
        """Close the database connection with proper cleanup"""
        if self._is_connected and self._connection:
            async with self._connection_lock:
                try:
                    await self._connection.close()
                    self._connection = None
                    self._is_connected = False
                    logger.info("Database connection closed")
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")
                    raise

def db_operation(func: Callable):
    """Decorator for database operations with retry logic"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        instance = await DatabaseConnection.get_instance()
        max_retries = instance._retries
        retry_delay = instance._retry_delay
        guild_id = kwargs.get('guild_id')

        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Database operation failed (attempt {attempt + 1}/{max_retries}): {e}")

                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                    try:
                        await instance._check_connection_health()
                    except Exception:
                        await instance._connect()
                else:
                    raise

    return wrapper