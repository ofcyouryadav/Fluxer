import discord
from discord.ext import commands
import aiosqlite
import os
import logging
from utils.Tools import blacklist_check, ignore_check
from Config.Config import OWNER_IDS

logger = logging.getLogger('bot')

BADGE_URLS = {
    "owner": "https://cdn.discordapp.com/emojis/1228227536207740989.png",
    "staff": "https://cdn.discordapp.com/emojis/1228227884481515613.png",
    "partner": "https://cdn.discordapp.com/emojis/1228228301089144976.png",
    "sponsor": "https://cdn.discordapp.com/emojis/1228246375180013678.png",
    "friend": "https://cdn.discordapp.com/emojis/1228229690376982549.png",
    "early": "https://cdn.discordapp.com/emojis/1228241490246111302.png",
    "vip": "https://cdn.discordapp.com/emojis/1228230884583276584.png",
    "bug": "https://cdn.discordapp.com/emojis/1228231513456382015.png"
}

BADGE_NAMES = {
    "owner": "Owner",
    "staff": "Staff",
    "partner": "Partner",
    "sponsor": "Sponsor",
    "friend": "Owner's Friend",
    "early": "Early Supporter",
    "vip": "VIP",
    "bug": "Bug Hunter"
}

DB_FOLDER = 'db'
DB_FILE = 'badges.db'
DB_PATH = os.path.join(DB_FOLDER, DB_FILE)

class Badges(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = DB_PATH
        self.bot.loop.create_task(self.initialize_db())

    async def initialize_db(self):
        """Initialize badge database"""
        os.makedirs(DB_FOLDER, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS badges (
                    user_id INTEGER PRIMARY KEY,
                    owner INTEGER DEFAULT 0,
                    staff INTEGER DEFAULT 0,
                    partner INTEGER DEFAULT 0,
                    sponsor INTEGER DEFAULT 0,
                    friend INTEGER DEFAULT 0,
                    early INTEGER DEFAULT 0,
                    vip INTEGER DEFAULT 0,
                    bug INTEGER DEFAULT 0
                )
            ''')
            await db.commit()

    async def add_badge(self, user_id: int, badge: str) -> bool:
        """Add a badge to user"""
        if badge not in BADGE_NAMES:
            return False
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"INSERT OR IGNORE INTO badges (user_id) VALUES (?)", (user_id,))
            await db.execute(f"UPDATE badges SET {badge} = 1 WHERE user_id = ?", (user_id,))
            await db.commit()
        return True

    async def remove_badge(self, user_id: int, badge: str) -> bool:
        """Remove a badge from user"""
        if badge not in BADGE_NAMES:
            return False
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"UPDATE badges SET {badge} = 0 WHERE user_id = ?", (user_id,))
            await db.commit()
        return True

    async def get_user_badges(self, user_id: int) -> dict:
        """Get all badges for user"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM badges WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
        
        if not row:
            return {badge: False for badge in BADGE_NAMES.keys()}
        
        badges = {}
        cursor_description = ['user_id', 'owner', 'staff', 'partner', 'sponsor', 'friend', 'early', 'vip', 'bug']
        for i, badge_type in enumerate(cursor_description[1:], 1):
            badges[badge_type] = bool(row[i])
        return badges

    @commands.group(name="badge", invoke_without_command=True)
    @commands.is_owner()
    async def badge(self, ctx):
        """Badge management commands (Owner only)"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="Badge Management",
                description="Use subcommands to manage user badges",
                color=0x7AAAFF
            )
            embed.add_field(
                name="Subcommands",
                value="`badge add <user> <badge_type>` - Add a badge\n"
                      "`badge remove <user> <badge_type>` - Remove a badge\n"
                      "`badge list <user>` - List user badges\n"
                      "`badge types` - Show available badge types",
                inline=False
            )
            await ctx.send(embed=embed)

    @badge.command(name="add")
    @commands.is_owner()
    async def badge_add(self, ctx, user: discord.User, badge_type: str):
        """Add a badge to user"""
        badge_type = badge_type.lower()
        
        if badge_type not in BADGE_NAMES:
            await ctx.send(f"❌ Invalid badge type. Available: {', '.join(BADGE_NAMES.keys())}")
            return
        
        if await self.add_badge(user.id, badge_type):
            embed = discord.Embed(
                title="✅ Badge Added",
                description=f"Added **{BADGE_NAMES[badge_type]}** badge to {user.mention}",
                color=0x00FF00
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to add badge",
                color=0xFF0000
            )
            await ctx.send(embed=embed)

    @badge.command(name="remove")
    @commands.is_owner()
    async def badge_remove(self, ctx, user: discord.User, badge_type: str):
        """Remove a badge from user"""
        badge_type = badge_type.lower()
        
        if badge_type not in BADGE_NAMES:
            await ctx.send(f"❌ Invalid badge type. Available: {', '.join(BADGE_NAMES.keys())}")
            return
        
        if await self.remove_badge(user.id, badge_type):
            embed = discord.Embed(
                title="✅ Badge Removed",
                description=f"Removed **{BADGE_NAMES[badge_type]}** badge from {user.mention}",
                color=0x00FF00
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to remove badge",
                color=0xFF0000
            )
            await ctx.send(embed=embed)

    @badge.command(name="list")
    @commands.is_owner()
    async def badge_list(self, ctx, user: discord.User):
        """List all badges for a user"""
        badges = await self.get_user_badges(user.id)
        user_badges = [BADGE_NAMES[badge] for badge, has_badge in badges.items() if has_badge]
        
        if not user_badges:
            description = "No badges"
        else:
            description = ", ".join(user_badges)
        
        embed = discord.Embed(
            title=f"Badges for {user.name}",
            description=description,
            color=0x7AAAFF
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        await ctx.send(embed=embed)

    @badge.command(name="types")
    @commands.is_owner()
    async def badge_types(self, ctx):
        """Show all available badge types"""
        embed = discord.Embed(
            title="Available Badges",
            description="Badge types you can assign:",
            color=0x7AAAFF
        )
        
        for badge_key, badge_name in BADGE_NAMES.items():
            embed.add_field(name=badge_name, value=f"`{badge_key}`", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="mybadges", aliases=["badges"])
    @commands.is_owner()
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def mybadges(self, ctx, user: discord.User = None):
        """Check your badges or another user's badges"""
        if user is None:
            user = ctx.author
        
        badges = await self.get_user_badges(user.id)
        user_badges = [BADGE_NAMES[badge] for badge, has_badge in badges.items() if has_badge]
        
        if not user_badges:
            description = "No badges yet"
        else:
            description = "\n".join([f"✨ {badge}" for badge in user_badges])
        
        embed = discord.Embed(
            title=f"{user.name}'s Badges",
            description=description,
            color=0x7AAAFF
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"Total: {len(user_badges)} badge(s)")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Badges(bot))
