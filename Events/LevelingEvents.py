import discord
from discord.ext import commands
from discord import ui
from discord.ui import LayoutView, Container, Section, TextDisplay, Separator, Thumbnail
from datetime import datetime, timezone
import random
import logging
from collections import defaultdict

logger = logging.getLogger('bot')

# Constants
COLOR = 0x2f3136
LEVELUP_COLOR = 0xffd700
BASE_XP = 15
MAX_XP = 25
COOLDOWN_SECONDS = 60

def calculate_level(xp: int) -> int:
    """Calculate level from XP"""
    return int((xp / 100) ** 0.5)

def xp_for_next_level(level: int) -> int:
    """Calculate XP needed for next level"""
    return ((level + 1) ** 2) * 100


class LevelingEvents(commands.Cog):
    """Event listener for leveling system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.xp_cooldowns = defaultdict(dict)
        
        # Get MongoDB from bot instance
        self.levels_collection = bot.db["levels"]
        self.birthdays_collection = bot.db["birthdays"]
        self.custom_roles_collection = bot.db["custom_roles"]
        self.message_stats_collection = bot.db["message_stats"]
        self.level_notifications_collection = bot.db["level_notifications"]
        
        logger.info("\x1b[38;5;197m[Cog]\x1b[0m LevelingEvents cog initialized")
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Track messages and award XP"""
        # Ignore bots and DMs
        if message.author.bot or not message.guild:
            return
        
        # Ignore commands (messages starting with slash only, not regular prefixes)
        if message.content.startswith('/'):
            return
        
        guild_id = message.guild.id
        user_id = message.author.id
        
        # logger.info(f"Processing message from {message.author} in {message.guild.name}: '{message.content[:50]}'")  # Commented out to reduce spam
        
        # Update message stats
        await self.update_message_stats(guild_id, user_id, message)
        
        # Check XP cooldown
        now = datetime.now(timezone.utc).timestamp()
        if user_id in self.xp_cooldowns.get(guild_id, {}):
            last_xp = self.xp_cooldowns[guild_id][user_id]
            if now - last_xp < COOLDOWN_SECONDS:
                # logger.info(f"User {message.author} is on XP cooldown")  # Commented out to reduce spam
                return  # User is on cooldown
        
        # Award XP
        xp_gained = random.randint(BASE_XP, MAX_XP)
        # logger.info(f"Awarding {xp_gained} XP to {message.author} in {message.guild.name}")  # Commented out to reduce spam
        await self.award_xp(message.author, guild_id, xp_gained, message.channel)
        
        # Update cooldown
        if guild_id not in self.xp_cooldowns:
            self.xp_cooldowns[guild_id] = {}
        self.xp_cooldowns[guild_id][user_id] = now
    
    async def update_message_stats(self, guild_id: int, user_id: int, message: discord.Message):
        """Update message statistics for a user"""
        try:
            await self.message_stats_collection.update_one(
                {"guild_id": guild_id, "user_id": user_id},
                {
                    "$inc": {
                        "total_messages": 1,
                        "total_characters": len(message.content)
                    },
                    "$set": {
                        "username": str(message.author),
                        "last_message_at": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error updating message stats: {e}")
    
    async def award_xp(self, member: discord.Member, guild_id: int, xp_amount: int, channel: discord.TextChannel):
        """Award XP to a user and check for level up"""
        try:
            # Get current data
            level_data = await self.levels_collection.find_one({
                "guild_id": guild_id,
                "user_id": member.id
            })
            
            old_xp = level_data["xp"] if level_data else 0
            old_level = calculate_level(old_xp)
            
            new_xp = old_xp + xp_amount
            new_level = calculate_level(new_xp)
            
            # Update database
            await self.levels_collection.update_one(
                {"guild_id": guild_id, "user_id": member.id},
                {
                    "$set": {
                        "xp": new_xp,
                        "username": str(member),
                        "updated_at": datetime.now(timezone.utc)
                    }
                },
                upsert=True
            )
            
            # Check for level up
            if new_level > old_level:
                await self.handle_level_up(member, guild_id, old_level, new_level, channel)
                
        except Exception as e:
            logger.error(f"Error awarding XP: {e}")
    
    async def handle_level_up(self, member: discord.Member, guild_id: int, old_level: int, new_level: int, channel: discord.TextChannel):
        """Handle level up announcement and role rewards"""
        try:
            # Create level up announcement
            view = LayoutView()
            container = Container()
            
            container.add_item(TextDisplay(f"## 🎉 Level Up!"))
            container.add_item(Separator())
            
            desc = f"Congratulations {member.name}!\n\n"
            desc += f"**Old Level:** {old_level}\n"
            desc += f"**New Level:** {new_level}\n"
            
            # Check for role rewards
            role_rewards = await self.custom_roles_collection.find({
                "guild_id": guild_id,
                "level": {"$lte": new_level, "$gt": old_level}
            }).to_list(None)
            
            roles_given = []
            for reward in role_rewards:
                role = member.guild.get_role(reward["role_id"])
                if role and role not in member.roles:
                    try:
                        await member.add_roles(role, reason=f"Level {reward['level']} reward")
                        roles_given.append(role.name)
                    except discord.Forbidden:
                        logger.warning(f"Cannot give role {role.name} to {member}")
                    except Exception as e:
                        logger.error(f"Error giving role: {e}")
            
            if roles_given:
                desc += f"\n**🎁 Rewards Unlocked:**\n" + ", ".join(roles_given)
            
            thumb = Thumbnail(member.display_avatar.url)
            section = Section(TextDisplay(desc), accessory=thumb)
            container.add_item(section)
            
            container.add_item(Separator())
            container.add_item(TextDisplay(f"-# Keep chatting to level up even more!"))
            
            view.add_item(container)
            
            # Check if notifications are enabled
            notification_data = await self.level_notifications_collection.find_one({
                "guild_id": guild_id
            })
            
            # Only send if notifications are enabled
            if notification_data and notification_data.get("enabled", False):
                target_channel = channel
                
                # If a specific channel is configured, use it; otherwise use message channel
                notification_channel = member.guild.get_channel(notification_data["channel_id"])
                if notification_channel:
                    target_channel = notification_channel
                
                # Send to target channel
                try:
                    await target_channel.send(view=view)
                except discord.Forbidden:
                    # If we can't send in this channel, try to DM the user
                    try:
                        await member.send(view=view)
                    except:
                        pass  # Silently fail if we can't DM either
                    
        except Exception as e:
            logger.error(f"Error handling level up: {e}")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Check for birthdays when bot starts"""
        await self.check_birthdays()
    
    async def check_birthdays(self):
        """Check and announce birthdays"""
        try:
            today = datetime.now()
            current_day = today.day
            current_month = today.month
            
            # Find all birthdays for today
            birthdays_today = await self.birthdays_collection.find({
                "day": current_day,
                "month": current_month
            }).to_list(None)
            
            for bday in birthdays_today:
                try:
                    guild = self.bot.get_guild(bday["guild_id"])
                    if not guild:
                        continue
                    
                    member = guild.get_member(bday["user_id"])
                    if not member:
                        continue
                    
                    # Find a suitable channel (general, announcements, or first text channel)
                    channel = None
                    for ch_name in ["general", "announcements", "birthdays"]:
                        channel = discord.utils.get(guild.text_channels, name=ch_name)
                        if channel:
                            break
                    
                    if not channel:
                        channel = guild.text_channels[0] if guild.text_channels else None
                    
                    if not channel:
                        continue
                    
                    # Create birthday announcement
                    view = LayoutView()
                    container = Container()
                    
                    container.add_item(TextDisplay(f"## 🎂 Happy Birthday!"))
                    container.add_item(Separator())
                    
                    age_text = ""
                    if bday.get("year"):
                        age = today.year - bday["year"]
                        age_text = f"\nTurning **{age}** years old today!"
                    
                    desc = f"Everyone wish {member.name} a happy birthday! 🎉{age_text}\n\n"
                    desc += f"Have an amazing day! 🎈🎁"
                    
                    thumb = Thumbnail(member.display_avatar.url)
                    section = Section(TextDisplay(desc), accessory=thumb)
                    container.add_item(section)
                    
                    container.add_item(Separator())
                    
                    view.add_item(container)
                    
                    await channel.send(view=view)
                    logger.info(f"Announced birthday for {member} in {guild.name}")
                    
                except Exception as e:
                    logger.error(f"Error announcing birthday: {e}")
                    
        except Exception as e:
            logger.error(f"Error checking birthdays: {e}")


async def setup(bot):
    await bot.add_cog(LevelingEvents(bot))
