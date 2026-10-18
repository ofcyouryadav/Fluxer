import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta
import logging
from collections import defaultdict

logger = logging.getLogger('bot')

class ServerUtilityEvents(commands.Cog):
    """Event listeners for tracking invites, voice time, and messages"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Get MongoDB collections from bot instance
        self.invite_stats_collection = bot.db["invite_stats"]
        self.voice_stats_collection = bot.db["voice_stats"]
        self.message_stats_collection = bot.db["message_stats"]
        self.blacklist_channels_collection = bot.db["blacklist_channels"]
        
        # Cache for invite tracking
        self.guild_invites = {}
        
        # Cache for voice tracking (user_id: join_time)
        self.voice_sessions = {}
        
        # Track guilds we couldn't access invites for (to avoid spam)
        self.no_invite_access = set()
        
        # Start daily reset task
        self.reset_daily_stats.start()
        
        logger.info("\x1b[38;5;197m[Cog]\x1b[0m ServerUtilityEvents cog initialized")
    
    async def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.reset_daily_stats.cancel()
    
    @tasks.loop(hours=24)
    async def reset_daily_stats(self):
        """Reset daily stats at midnight"""
        try:
            # Reset daily messages
            await self.message_stats_collection.update_many(
                {},
                {"$set": {"daily_messages": 0}}
            )
            
            # Reset daily voice minutes
            await self.voice_stats_collection.update_many(
                {},
                {"$set": {"daily_minutes": 0}}
            )
            
            logger.info("Daily stats reset completed")
        except Exception as e:
            logger.error(f"Error resetting daily stats: {e}")
    
    @reset_daily_stats.before_loop
    async def before_reset_daily_stats(self):
        """Wait until bot is ready before starting the task"""
        await self.bot.wait_until_ready()
    
    # ==================== INVITE TRACKING ====================
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Cache invites when bot is ready"""
        try:
            for guild in self.bot.guilds:
                try:
                    self.guild_invites[guild.id] = await guild.invites()
                    # Remove from no-access list if we can now access it
                    self.no_invite_access.discard(guild.id)
                except discord.Forbidden:
                    # Only log once per guild to prevent spam
                    if guild.id not in self.no_invite_access:
                        self.no_invite_access.add(guild.id)
                except Exception as e:
                    logger.error(f"Error caching invites for {guild.name}: {e}")
        except Exception as e:
            logger.error(f"Error in invite caching on_ready: {e}")
    
    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        """Update invite cache when new invite is created"""
        try:
            if invite.guild and invite.guild.id in self.guild_invites:
                self.guild_invites[invite.guild.id].append(invite)
        except Exception as e:
            logger.error(f"Error updating invite cache: {e}")
    
    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        """Update invite cache when invite is deleted"""
        try:
            if invite.guild and invite.guild.id in self.guild_invites:
                self.guild_invites[invite.guild.id] = [
                    inv for inv in self.guild_invites[invite.guild.id] 
                    if inv.code != invite.code
                ]
        except Exception as e:
            logger.error(f"Error removing invite from cache: {e}")
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Track who invited a member"""
        if member.bot:
            return
        
        try:
            # Get current invites
            try:
                current_invites = await member.guild.invites()
            except discord.Forbidden:
                # Silently skip if no invite access
                return
            
            # Get cached invites
            cached_invites = self.guild_invites.get(member.guild.id, [])
            
            # Find which invite was used
            inviter_id = None
            for current_invite in current_invites:
                for cached_invite in cached_invites:
                    # Check if both uses are not None before comparing
                    if (current_invite.code == cached_invite.code and 
                        current_invite.uses is not None and 
                        cached_invite.uses is not None and 
                        current_invite.uses > cached_invite.uses):
                        inviter_id = current_invite.inviter.id if current_invite.inviter else None
                        break
                if inviter_id:
                    break
            
            # Update cache
            self.guild_invites[member.guild.id] = current_invites
            
            # Update inviter stats
            if inviter_id:
                await self.invite_stats_collection.update_one(
                    {"guild_id": member.guild.id, "user_id": inviter_id},
                    {
                        "$inc": {"total_invites": 1},
                        "$set": {"updated_at": datetime.now(timezone.utc)}
                    },
                    upsert=True
                )
                
                # Store who invited this member
                await self.invite_stats_collection.update_one(
                    {"guild_id": member.guild.id, "user_id": member.id},
                    {
                        "$set": {
                            "invited_by": inviter_id,
                            "joined_at": datetime.now(timezone.utc)
                        }
                    },
                    upsert=True
                )
                
                logger.info(f"{member} was invited by {inviter_id} in {member.guild.name}")
        
        except Exception as e:
            logger.error(f"Error tracking invite for {member}: {e}")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Track when invited members leave"""
        if member.bot:
            return
        
        try:
            # Get who invited this member
            member_stats = await self.invite_stats_collection.find_one({
                "guild_id": member.guild.id,
                "user_id": member.id
            })
            
            if member_stats and member_stats.get("invited_by"):
                inviter_id = member_stats["invited_by"]
                
                # Check if member joined recently (less than 7 days ago)
                joined_at = member_stats.get("joined_at")
                if joined_at and (datetime.now(timezone.utc) - joined_at).days < 7:
                    # Mark as fake invite (joined and left quickly)
                    await self.invite_stats_collection.update_one(
                        {"guild_id": member.guild.id, "user_id": inviter_id},
                        {"$inc": {"fake_invites": 1}},
                        upsert=True
                    )
                else:
                    # Mark as left invite (stayed for a while but left)
                    await self.invite_stats_collection.update_one(
                        {"guild_id": member.guild.id, "user_id": inviter_id},
                        {"$inc": {"left_invites": 1}},
                        upsert=True
                    )
                
                logger.info(f"{member} left - updating stats for inviter {inviter_id}")
        
        except Exception as e:
            logger.error(f"Error updating invite stats for leaving member {member}: {e}")
    
    # ==================== VOICE TRACKING ====================
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Track voice channel time"""
        if member.bot:
            return
        
        try:
            # Member joined voice
            if before.channel is None and after.channel is not None:
                session_key = f"{member.guild.id}:{member.id}"
                self.voice_sessions[session_key] = datetime.now(timezone.utc)
                # logger.info(f"{member} joined voice in {member.guild.name}")  # Commented out to reduce spam
            
            # Member left voice
            elif before.channel is not None and after.channel is None:
                session_key = f"{member.guild.id}:{member.id}"
                if session_key in self.voice_sessions:
                    join_time = self.voice_sessions.pop(session_key)
                    duration = datetime.now(timezone.utc) - join_time
                    minutes = int(duration.total_seconds() / 60)
                    
                    if minutes > 0:
                        # Update voice stats
                        await self.voice_stats_collection.update_one(
                            {"guild_id": member.guild.id, "user_id": member.id},
                            {
                                "$inc": {
                                    "total_minutes": minutes,
                                    "daily_minutes": minutes
                                },
                                "$set": {"updated_at": datetime.now(timezone.utc)}
                            },
                            upsert=True
                        )
                        
                        # logger.info(f"{member} spent {minutes} minutes in voice")  # Commented out to reduce spam
            
            # Member switched channels (still in voice)
            elif before.channel is not None and after.channel is not None and before.channel != after.channel:
                # Just log the channel switch, time continues counting
                # logger.info(f"{member} switched voice channels")  # Commented out to reduce spam
                pass  # Keep elif block valid
        
        except Exception as e:
            logger.error(f"Error tracking voice for {member}: {e}")
    
    # ==================== MESSAGE TRACKING ====================
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Track message statistics"""
        # Ignore bots and DMs
        if message.author.bot or not message.guild:
            return
        
        try:
            # Check if channel is blacklisted
            blacklisted = await self.blacklist_channels_collection.find_one({
                "guild_id": message.guild.id,
                "channel_id": message.channel.id
            })
            
            if blacklisted:
                return
            
            # Update message stats
            message_length = len(message.content)
            
            await self.message_stats_collection.update_one(
                {"guild_id": message.guild.id, "user_id": message.author.id},
                {
                    "$inc": {
                        "total_messages": 1,
                        "total_characters": message_length,
                        "daily_messages": 1
                    },
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                },
                upsert=True
            )
        
        except Exception as e:
            logger.error(f"Error tracking message stats: {e}")


async def setup(bot):
    await bot.add_cog(ServerUtilityEvents(bot))
