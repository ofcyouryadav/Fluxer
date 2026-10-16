import aiosqlite
import os
from typing import Optional, Dict

DB_PATH = 'db/boost.db'

async def initialize_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS boost_config (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER NOT NULL,
                enabled INTEGER DEFAULT 1,
                message TEXT DEFAULT '🚀 {user} just boosted **{server}**! Thank you for your support! 💎',
                embed_enabled INTEGER DEFAULT 1,
                embed_title TEXT DEFAULT '🚀 Server Boosted!',
                embed_description TEXT DEFAULT 'Thank you {user} for boosting **{server}**! 💎\n\nWe now have **{boostcount}** boosts at level **{boostlevel}**!',
                embed_color INTEGER DEFAULT 16738740,
                embed_thumbnail TEXT DEFAULT 'user_avatar',
                embed_image TEXT,
                embed_footer TEXT DEFAULT 'Boost #{boostcount}',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()

async def get_config(guild_id: int) -> Optional[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM boost_config WHERE guild_id = ?",
            (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

async def create_config(guild_id: int, channel_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            '''INSERT OR REPLACE INTO boost_config 
            (guild_id, channel_id, enabled, message, embed_enabled, embed_title, 
            embed_description, embed_color, embed_thumbnail, embed_image, embed_footer)
            VALUES (?, ?, 1, ?, 1, ?, ?, 16738740, 'user_avatar', NULL, ?)''',
            (guild_id, channel_id,
             '🚀 {user} just boosted **{server}**! Thank you for your support! 💎',
             '🚀 Server Boosted!',
             'Thank you {user} for boosting **{server}**! 💎\n\nWe now have **{boostcount}** boosts at level **{boostlevel}**!',
             'Boost #{boostcount}')
        )
        await db.commit()

async def update_channel(guild_id: int, channel_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE boost_config SET channel_id = ?, updated_at = CURRENT_TIMESTAMP WHERE guild_id = ?",
            (channel_id, guild_id)
        )
        await db.commit()

async def update_message(guild_id: int, message: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE boost_config SET message = ?, updated_at = CURRENT_TIMESTAMP WHERE guild_id = ?",
            (message, guild_id)
        )
        await db.commit()

async def update_embed_field(guild_id: int, field: str, value) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE boost_config SET {field} = ?, updated_at = CURRENT_TIMESTAMP WHERE guild_id = ?",
            (value, guild_id)
        )
        await db.commit()

async def toggle_enabled(guild_id: int, enabled: bool) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE boost_config SET enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE guild_id = ?",
            (1 if enabled else 0, guild_id)
        )
        await db.commit()

async def delete_config(guild_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM boost_config WHERE guild_id = ?", (guild_id,))
        await db.commit()
