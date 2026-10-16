"""
Database initialization script for SQLite
"""
import aiosqlite
import asyncio
import logging
from pathlib import Path
from schemas import TABLES, INDEXES, TRIGGERS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def init_db():
    """Initialize the SQLite database with all required tables and indexes"""
    db_path = Path('bot_database.db')

    try:
        # Create database directory if it doesn't exist
        db_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(str(db_path)) as db:
            # Enable foreign keys and WAL mode for better concurrency
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute("PRAGMA journal_mode = WAL")
            await db.execute("PRAGMA synchronous = NORMAL")

            # Create tables
            for table_name, create_table_sql in TABLES.items():
                try:
                    await db.execute(create_table_sql)
                    logger.info(f"Created table: {table_name}")
                except Exception as e:
                    logger.error(f"Error creating table {table_name}: {e}")
                    raise

            # Create indexes
            for index_name, index_sql in INDEXES.items():
                try:
                    if isinstance(index_sql, list):
                        for sql in index_sql:
                            await db.execute(sql)
                    else:
                        await db.execute(index_sql)
                    logger.info(f"Created index: {index_name}")
                except Exception as e:
                    logger.error(f"Error creating index {index_name}: {e}")
                    raise

            # Create triggers
            for trigger_name, trigger_sql in TRIGGERS.items():
                try:
                    await db.execute(trigger_sql)
                    logger.info(f"Created trigger: {trigger_name}")
                except Exception as e:
                    logger.error(f"Error creating trigger {trigger_name}: {e}")
                    raise

            await db.commit()
            logger.info("Database initialization completed successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(init_db())
        logger.info("Database initialization script completed")
    except KeyboardInterrupt:
        logger.info("Database initialization interrupted by user")
    except Exception as e:
        logger.error(f"Database initialization script failed: {e}")
        raise