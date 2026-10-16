import discord
from discord.ext import commands, tasks
from discord.ui import LayoutView, Container, Section, TextDisplay, Separator, Thumbnail
from typing import Optional
from datetime import datetime, timezone
import random
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
import aiohttp
import logging

logger = logging.getLogger('bot')

# Constants
COLOR = 0x2f3136
SUCCESS_COLOR = 0x00ff88
ERROR_COLOR = 0xff0033
BASE_XP = 15
MAX_XP = 25
COOLDOWN_SECONDS = 60

# Level calculation
def calculate_level(xp: int) -> int:
    """Calculate level from XP using quadratic formula"""
    return int((xp / 100) ** 0.5)

def xp_for_next_level(level: int) -> int:
    """Calculate XP needed for next level"""
    return ((level + 1) ** 2) * 100

async def create_rank_card(member: discord.Member, xp: int, rank: int) -> BytesIO:
    """Generate a beautiful rank card with PIL"""
    # Card dimensions
    width, height = 900, 300
    
    # Create image with gradient background
    img = Image.new('RGB', (width, height), color=(47, 49, 54))
    draw = ImageDraw.Draw(img)
    
    # Draw gradient background
    for i in range(height):
        r = int(47 + (88 - 47) * (i / height))
        g = int(49 + (101 - 49) * (i / height))
        b = int(54 + (242 - 54) * (i / height))
        draw.rectangle([(0, i), (width, i + 1)], fill=(r, g, b))
    
    # Calculate level and progress
    level = calculate_level(xp)
    next_level_xp = xp_for_next_level(level)
    current_level_xp = level ** 2 * 100
    progress_xp = xp - current_level_xp
    needed_xp = next_level_xp - current_level_xp
    progress_percent = (progress_xp / needed_xp) if needed_xp > 0 else 1.0
    
    # Load fonts (fallback to default if custom not available)
    try:
        font_large = ImageFont.truetype("fonts/notosans-black.ttf", 48)
        font_medium = ImageFont.truetype("fonts/notosans-black.ttf", 32)
        font_small = ImageFont.truetype("fonts/notosans-black.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Download and paste avatar
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(str(member.display_avatar.url)) as resp:
                avatar_data = await resp.read()
                avatar = Image.open(BytesIO(avatar_data)).convert('RGBA')
                avatar = avatar.resize((200, 200), Image.Resampling.LANCZOS)
                
                # Create circular mask
                mask = Image.new('L', (200, 200), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, 200, 200), fill=255)
                
                # Paste avatar with circular mask
                img.paste(avatar, (50, 50), mask)
    except:
        # Draw placeholder circle if avatar fails
        draw.ellipse((50, 50, 250, 250), fill=(100, 100, 100))
    
    # Draw username
    username = member.name[:20]
    draw.text((280, 60), username, fill=(255, 255, 255), font=font_large)
    
    # Draw rank and level
    draw.text((280, 120), f"Rank #{rank}", fill=(200, 200, 200), font=font_small)
    draw.text((280, 150), f"Level {level}", fill=(255, 215, 0), font=font_medium)
    
    # Draw XP progress bar
    bar_x, bar_y = 280, 210
    bar_width, bar_height = 570, 40
    
    # Background bar
    draw.rectangle(
        [(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)],
        fill=(40, 40, 40),
        outline=(255, 255, 255),
        width=2
    )
    
    # Progress bar
    progress_width = int(bar_width * progress_percent)
    if progress_width > 0:
        for i in range(bar_height):
            color_intensity = int(255 * (1 - i / bar_height))
            draw.rectangle(
                [(bar_x, bar_y + i), (bar_x + progress_width, bar_y + i + 1)],
                fill=(0, color_intensity, 255 - color_intensity)
            )
    
    # Draw XP text
    xp_text = f"{progress_xp:,} / {needed_xp:,} XP"
    draw.text((bar_x + bar_width // 2 - 50, bar_y + 10), xp_text, fill=(255, 255, 255), font=font_small)
    
    # Save to bytes
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

class LevelingSystem(commands.Cog):
    """Advanced XP and leveling system with rank cards"""
    
    def __init__(self, bot):
        self.bot = bot
        self.color = COLOR
        self.xp_cooldowns = defaultdict(dict)
        
        # Get MongoDB from bot instance
        self.levels_collection = bot.db["levels"]
        self.custom_roles_collection = bot.db["custom_roles"]
        self.message_stats_collection = bot.db["message_stats"]
        self.level_notifications_collection = bot.db["level_notifications"]
        
        # Start cooldown cleanup task
        self.cleanup_cooldowns.start()
    
    async def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.cleanup_cooldowns.cancel()
    
    @tasks.loop(minutes=10)
    async def cleanup_cooldowns(self):
        """Periodically clean up old cooldown entries"""
        now = datetime.now(timezone.utc).timestamp()
        for guild_id in list(self.xp_cooldowns.keys()):
            for user_id in list(self.xp_cooldowns[guild_id].keys()):
                if now - self.xp_cooldowns[guild_id][user_id] > COOLDOWN_SECONDS * 2:
                    del self.xp_cooldowns[guild_id][user_id]
            if not self.xp_cooldowns[guild_id]:
                del self.xp_cooldowns[guild_id]
    
    # ==================== CUSTOM ROLE REWARDS ====================
    
    @commands.hybrid_command(name="setlevelrole", aliases=["levelrole"])
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def setlevelrole(self, ctx, level: int = None, role: discord.Role = None):
        """Set a role reward for reaching a specific level (Admin only)"""
        if level is None or role is None:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ **Missing Arguments**\n\nUsage: `{ctx.prefix}setlevelrole <level> <@role>`\n\nExample: `{ctx.prefix}setlevelrole 10 @Member`"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        if level < 1 or level > 100:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ **Invalid Level**\n\nLevel must be between 1 and 100."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        # Save to database
        await self.custom_roles_collection.update_one(
            {"guild_id": ctx.guild.id, "level": level},
            {"$set": {
                "role_id": role.id,
                "role_name": role.name,
                "updated_at": datetime.now(timezone.utc)
            }},
            upsert=True
        )
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## 🎖️ Level Role Reward Set!"))
        container.add_item(Separator())
        
        desc = f"**Level:** {level}\n**Role:** {role.name}\n\n✅ Users will receive this role when they reach level {level}!"
        
        thumb = Thumbnail(ctx.guild.icon.url if ctx.guild.icon else ctx.author.display_avatar.url)
        section = Section(TextDisplay(desc), accessory=thumb)
        container.add_item(section)
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.hybrid_command(name="levelroles", aliases=["rolerewards"])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def levelroles(self, ctx):
        """View all level role rewards in this server"""
        roles = await self.custom_roles_collection.find({"guild_id": ctx.guild.id}).sort("level", 1).to_list(None)
        
        if not roles:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## 🎖️ No Role Rewards\n\nNo level role rewards have been set up yet!"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## 🎖️ Level Role Rewards - {ctx.guild.name}"))
        container.add_item(Separator())
        
        role_list = []
        for role_data in roles:
            role = ctx.guild.get_role(role_data["role_id"])
            if role:
                role_list.append(f"`Level {role_data['level']}` ➜ {role.name}")
            else:
                role_list.append(f"`Level {role_data['level']}` ➜ *Role Deleted*")
        
        container.add_item(TextDisplay("\n".join(role_list)))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Total: {len(roles)} role rewards"))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    # ==================== RANK & LEVEL COMMANDS ====================
    
    @commands.hybrid_command(name="rank", aliases=["level", "lvl"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def rank(self, ctx, member: Optional[discord.Member] = None):
        """View your or another member's rank card with XP and level"""
        member = member or ctx.author
        
        level_data = await self.levels_collection.find_one({
            "guild_id": ctx.guild.id,
            "user_id": member.id
        })
        
        if not level_data:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"## 📊 No Level Data\n\n{member.name} hasn't earned any XP yet!"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        xp = level_data.get("xp", 0)
        
        # Get rank
        all_levels = await self.levels_collection.find({"guild_id": ctx.guild.id}).sort("xp", -1).to_list(None)
        rank = next((i + 1 for i, l in enumerate(all_levels) if l["user_id"] == member.id), 0)
        
        # Generate rank card
        try:
            card_buffer = await create_rank_card(member, xp, rank)
            file = discord.File(card_buffer, filename="rank_card.png")
            await ctx.reply(file=file)
        except Exception as e:
            print(f"Error creating rank card: {e}")
            # Fallback to text-based rank display
            level = calculate_level(xp)
            next_level_xp = xp_for_next_level(level)
            current_level_xp = level ** 2 * 100
            progress_xp = xp - current_level_xp
            needed_xp = next_level_xp - current_level_xp
            progress_percent = int((progress_xp / needed_xp) * 100) if needed_xp > 0 else 100
            
            bar_length = 20
            filled = int((progress_percent / 100) * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            view = LayoutView()
            container = Container()
            
            container.add_item(TextDisplay(f"## 📊 Rank - {member.name}"))
            container.add_item(Separator())
            
            desc = f"**Level:** {level}\n"
            desc += f"**XP:** {xp:,}\n"
            desc += f"**Server Rank:** #{rank}\n\n"
            desc += f"**Progress to Level {level + 1}:**\n"
            desc += f"{bar} {progress_percent}%\n"
            desc += f"{progress_xp:,} / {needed_xp:,} XP"
            
            thumb = Thumbnail(member.display_avatar.url)
            section = Section(TextDisplay(desc), accessory=thumb)
            container.add_item(section)
            
            view.add_item(container)
            await ctx.reply(view=view)
    
    @commands.hybrid_command(name="leaderboard", aliases=["lb", "top"])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def leaderboard(self, ctx):
        """View the top ranked members in this server"""
        top_levels = await self.levels_collection.find({"guild_id": ctx.guild.id}).sort("xp", -1).limit(15).to_list(None)
        
        if not top_levels:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## 📊 No Leaderboard Data\n\nNo one has earned XP yet!"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## 📊 Level Leaderboard - {ctx.guild.name}"))
        container.add_item(Separator())
        
        leaderboard = []
        medals = ["🥇", "🥈", "🥉"]
        
        for i, level_data in enumerate(top_levels, 1):
            user = ctx.guild.get_member(level_data["user_id"])
            if not user:
                continue
            
            medal = medals[i - 1] if i <= 3 else f"`{i}.`"
            xp = level_data.get("xp", 0)
            level = calculate_level(xp)
            
            if user.id == ctx.author.id:
                leaderboard.append(f"{medal} **{user.name}** - Level **{level}** ({xp:,} XP) ⭐")
            else:
                leaderboard.append(f"{medal} **{user.name}** - Level {level} ({xp:,} XP)")
        
        if leaderboard:
            container.add_item(TextDisplay("\n".join(leaderboard)))
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Keep leveling up to reach the top!"))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.hybrid_command(name="resetlevel")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def resetlevel(self, ctx, member: discord.Member):
        """Reset a member's level and XP (Admin only)"""
        result = await self.levels_collection.delete_one({
            "guild_id": ctx.guild.id,
            "user_id": member.id
        })
        
        if result.deleted_count == 0:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ {member.name} doesn't have any level data to reset."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## ✅ Level Reset"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"{member.name}'s level and XP have been reset to 0."))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    # ==================== LEVEL NOTIFICATIONS ====================
    
    @commands.command(name="setlevelnotify", aliases=["levelnotify"])
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def setlevelnotify(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Set the channel where level-up announcements are posted"""
        if channel is None:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ **Missing Arguments**\n\nUsage: `{ctx.prefix}setlevelnotify <#channel>`\n\nExample: `{ctx.prefix}setlevelnotify #announcements`"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        # Check if bot can send messages in the channel
        if not channel.permissions_for(ctx.guild.me).send_messages:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ **No Permission**\n\nI don't have permission to send messages in {channel.name}"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        # Save to database
        await self.level_notifications_collection.update_one(
            {"guild_id": ctx.guild.id},
            {"$set": {
                "channel_id": channel.id,
                "channel_name": channel.name,
                "enabled": True,
                "updated_at": datetime.now(timezone.utc)
            }},
            upsert=True
        )
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## 🔔 Level Notification Channel Set!"))
        container.add_item(Separator())
        
        desc = f"**Channel:** {channel.name}\n\n✅ Level-up announcements will now be posted in {channel.name}!"
        
        thumb = Thumbnail(ctx.guild.icon.url if ctx.guild.icon else ctx.author.display_avatar.url)
        section = Section(TextDisplay(desc), accessory=thumb)
        container.add_item(section)
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="enablelevelnotify")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def enablelevelnotify(self, ctx):
        """Enable level-up notifications"""
        notification_data = await self.level_notifications_collection.find_one({
            "guild_id": ctx.guild.id
        })
        
        if notification_data and notification_data.get("enabled", False):
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("ℹ️ **Already Enabled**\n\nLevel notifications are already enabled!"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        # Enable notifications (create if doesn't exist)
        await self.level_notifications_collection.update_one(
            {"guild_id": ctx.guild.id},
            {"$set": {"enabled": True}},
            upsert=True
        )
        
        channel_text = ""
        if notification_data:
            channel = ctx.guild.get_channel(notification_data["channel_id"])
            channel_mention = channel.name if channel else f"Channel (ID: {notification_data['channel_id']})"
            channel_text = f" in {channel_mention}"
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## ✅ Level Notifications Enabled"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"Level-up announcements will now be posted{channel_text}!"))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="disablelevelnotify")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def disablelevelnotify(self, ctx):
        """Disable all level-up notifications"""
        notification_data = await self.level_notifications_collection.find_one({
            "guild_id": ctx.guild.id
        })
        
        if not notification_data or not notification_data.get("enabled", False):
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("ℹ️ **Already Disabled**\n\nLevel notifications are already disabled!"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        # Disable notifications
        await self.level_notifications_collection.update_one(
            {"guild_id": ctx.guild.id},
            {"$set": {"enabled": False}}
        )
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## ✅ Level Notifications Disabled"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"Users will no longer receive level-up announcements.\n\n-# Use `{ctx.prefix}enablelevelnotify` to turn them back on."))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="levelnotifyinfo", aliases=["levelnotifystatus"])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def levelnotifyinfo(self, ctx):
        """View the current level-up notification channel and status"""
        notification_data = await self.level_notifications_collection.find_one({
            "guild_id": ctx.guild.id
        })
        
        view = LayoutView()
        container = Container()
        
        if notification_data:
            channel = ctx.guild.get_channel(notification_data["channel_id"])
            channel_mention = channel.name if channel else f"*Channel deleted (ID: {notification_data['channel_id']})*"
            is_enabled = notification_data.get("enabled", False)
            status_emoji = "🟢" if is_enabled else "🔴"
            status_text = "Enabled" if is_enabled else "Disabled"
            
            container.add_item(TextDisplay("## 🔔 Level Notification Settings"))
            container.add_item(Separator())
            
            desc = f"**Channel:** {channel_mention}\n"
            desc += f"**Status:** {status_emoji} {status_text}"
            
            container.add_item(TextDisplay(desc))
        else:
            container.add_item(TextDisplay("## 🔔 Level Notification Settings"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"**Status:** Not configured\n\nUse `{ctx.prefix}setlevelnotify #channel` to set one!"))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="resetlevelnotify", aliases=["clearlevelnotify"])
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def resetlevelnotify(self, ctx):
        """Remove the level-up notification channel (announcements will appear in message channel)"""
        result = await self.level_notifications_collection.delete_one({
            "guild_id": ctx.guild.id
        })
        
        if result.deleted_count == 0:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ **No notification channel set**\n\nThere's nothing to reset!"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## ✅ Level Notification Reset"))
        container.add_item(Separator())
        container.add_item(TextDisplay("Level-up announcements will now appear in the channel where the user sends messages."))
        
        view.add_item(container)
        await ctx.reply(view=view)


async def setup(bot):
    await bot.add_cog(LevelingSystem(bot))
