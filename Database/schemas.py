"""
SQLite database schema definitions and table creation scripts
"""
from typing import Dict, List
import logging
import aiosqlite
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Table creation SQL statements
TABLES = {
    'dj_roles': """
        CREATE TABLE IF NOT EXISTS dj_roles (
            guild_id INTEGER PRIMARY KEY,
            role_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,

    'prefixes': """
        CREATE TABLE IF NOT EXISTS prefixes (
            guild_id INTEGER PRIMARY KEY,
            prefix TEXT NOT NULL CHECK(length(prefix) <= 5),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,

    'playlists': """
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL CHECK(length(name) <= 100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(guild_id, user_id, name)
        )
    """,

    'playlist_tracks': """
        CREATE TABLE IF NOT EXISTS playlist_tracks (
            playlist_id INTEGER,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            duration INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(playlist_id) REFERENCES playlists(id) ON DELETE CASCADE
        )
    """,

    'music_settings': """
        CREATE TABLE IF NOT EXISTS music_settings (
            guild_id INTEGER PRIMARY KEY,
            volume INTEGER NOT NULL CHECK(volume BETWEEN 0 AND 100),
            dj_role INTEGER,
            auto_play BOOLEAN DEFAULT FALSE,
            auto_shuffle BOOLEAN DEFAULT FALSE,
            announce_songs BOOLEAN DEFAULT TRUE,
            max_queue_length INTEGER DEFAULT 500 CHECK(max_queue_length > 0),
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,

    'config': """
        CREATE TABLE IF NOT EXISTS config (
            guild_id INTEGER PRIMARY KEY,
            embed_id TEXT NOT NULL,
            button_status BOOLEAN DEFAULT TRUE,
            mode_247 BOOLEAN DEFAULT FALSE,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,

    'spotify': """
        CREATE TABLE IF NOT EXISTS spotify (
            guild_id INTEGER PRIMARY KEY,
            access_token TEXT NOT NULL,
            refresh_token TEXT NOT NULL,
            token_type TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,

    'ignore_channels': """
        CREATE TABLE IF NOT EXISTS ignore_channels (
            guild_id INTEGER PRIMARY KEY,
            channel_ids TEXT DEFAULT '[]',
            bypass_role_ids TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,

    'channel_data': """
        CREATE TABLE IF NOT EXISTS channel_data (
            guild_id INTEGER PRIMARY KEY,
            voice_channel_id INTEGER,
            text_channel_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    'embed_settings': """
        CREATE TABLE IF NOT EXISTS embed_settings (
            guild_id INTEGER PRIMARY KEY,
            embed_style TEXT DEFAULT 'default',
            button_status BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
}

# Indexes for optimization
INDEXES = {
    'dj_roles_idx': 'CREATE INDEX IF NOT EXISTS idx_dj_roles_guild ON dj_roles(guild_id)',
    'prefixes_idx': 'CREATE INDEX IF NOT EXISTS idx_prefixes_guild ON prefixes(guild_id)',
    'playlists_idx': [
        'CREATE INDEX IF NOT EXISTS idx_playlists_guild ON playlists(guild_id)',
        'CREATE INDEX IF NOT EXISTS idx_playlists_user ON playlists(user_id)',
        'CREATE INDEX IF NOT EXISTS idx_playlists_name ON playlists(name)'
    ],
    'playlist_tracks_idx': 'CREATE INDEX IF NOT EXISTS idx_playlist_tracks_playlist ON playlist_tracks(playlist_id)',
    'music_settings_idx': 'CREATE INDEX IF NOT EXISTS idx_music_settings_guild ON music_settings(guild_id)',
    'config_idx': 'CREATE INDEX IF NOT EXISTS idx_config_guild ON config(guild_id)',
    'spotify_idx': 'CREATE INDEX IF NOT EXISTS idx_spotify_guild ON spotify(guild_id)',
    'ignore_channels_idx': 'CREATE INDEX IF NOT EXISTS idx_ignore_channels_guild ON ignore_channels(guild_id)',
    'channel_data_idx': 'CREATE INDEX IF NOT EXISTS idx_channel_data_guild ON channel_data(guild_id)',
    'embed_settings_idx': 'CREATE INDEX IF NOT EXISTS idx_embed_settings_guild ON embed_settings(guild_id)'
}

# Triggers for updating timestamps
TRIGGERS = {
    'update_dj_roles_timestamp': """
        CREATE TRIGGER IF NOT EXISTS update_dj_roles_timestamp 
        AFTER UPDATE ON dj_roles
        BEGIN
            UPDATE dj_roles SET updated_at = CURRENT_TIMESTAMP WHERE guild_id = NEW.guild_id;
        END;
    """,
    'update_prefixes_timestamp': """
        CREATE TRIGGER IF NOT EXISTS update_prefixes_timestamp 
        AFTER UPDATE ON prefixes
        BEGIN
            UPDATE prefixes SET updated_at = CURRENT_TIMESTAMP WHERE guild_id = NEW.guild_id;
        END;
    """,
    'update_playlists_timestamp': """
        CREATE TRIGGER IF NOT EXISTS update_playlists_timestamp 
        AFTER UPDATE ON playlists
        BEGIN
            UPDATE playlists SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END;
    """,
    'update_channel_data_timestamp': """
        CREATE TRIGGER IF NOT EXISTS update_channel_data_timestamp 
        AFTER UPDATE ON channel_data
        BEGIN
            UPDATE channel_data SET updated_at = CURRENT_TIMESTAMP WHERE guild_id = NEW.guild_id;
        END;
    """,
    'update_embed_settings_timestamp': """
    CREATE TRIGGER IF NOT EXISTS update_embed_settings_timestamp 
    AFTER UPDATE ON embed_settings
    BEGIN
        UPDATE embed_settings SET updated_at = CURRENT_TIMESTAMP WHERE guild_id = NEW.guild_id;
    END;
"""
}

async def initialize_database(db_connection) -> bool:
    """Initialize database with all tables, indexes and triggers"""
    try:
        # Get the underlying aiosqlite connection
        connection = getattr(db_connection, '_connection', None)
        if not connection:
            logger.error("No valid database connection available")
            return False

        async with connection.cursor() as cursor:
            # Start transaction
            await cursor.execute("BEGIN TRANSACTION")

            try:
                # Create tables
                for table_name, create_table_sql in TABLES.items():
                    logger.info(f"Creating table: {table_name}")
                    await cursor.execute(create_table_sql)

                # Create indexes
                for index_name, index_sql in INDEXES.items():
                    logger.info(f"Creating index: {index_name}")
                    if isinstance(index_sql, list):
                        for sql in index_sql:
                            await cursor.execute(sql)
                    else:
                        await cursor.execute(index_sql)

                # Create triggers
                for trigger_name, trigger_sql in TRIGGERS.items():
                    logger.info(f"Creating trigger: {trigger_name}")
                    await cursor.execute(trigger_sql)

                # Commit transaction
                await connection.commit()
                logger.info("Database initialization completed successfully")
                return True

            except Exception as e:
                # Rollback on error
                await connection.rollback()
                logger.error(f"Error during database initialization: {e}")
                return False

    except Exception as e:
        logger.error(f"Critical error initializing database: {e}")
        return False