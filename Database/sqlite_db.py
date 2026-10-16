import sqlite3
import logging

logger = logging.getLogger(__name__)

# Initialize SQLite database
db = sqlite3.connect("bot_database.db")
cursor = db.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS channel_data (
    guild_id INTEGER PRIMARY KEY,
    voice_channel_id INTEGER,
    text_channel_id INTEGER
)
""")
db.commit()

def save_ctx(guild_id, voice_channel_id, text_channel_id):
    """Save the current voice and text channel context for a guild"""
    try:
        cursor.execute("""
        INSERT INTO channel_data (guild_id, voice_channel_id, text_channel_id)
        VALUES (?, ?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET 
            voice_channel_id = excluded.voice_channel_id,
            text_channel_id = excluded.text_channel_id
        """, (guild_id, voice_channel_id, text_channel_id))
        db.commit()
    except Exception as e:
        logger.error(f"Error saving context to SQLite: {e}")

def Rex(guild_id):
    """Get the last saved voice and text channel IDs for a guild"""
    try:
        cursor.execute("SELECT voice_channel_id, text_channel_id FROM channel_data WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
        return result if result else (None, None)
    except Exception as e:
        logger.error(f"Error retrieving context from SQLite: {e}")
        return (None, None)
