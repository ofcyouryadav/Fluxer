import discord
from discord.ext import commands
from discord.ui import LayoutView, Container, Section, TextDisplay, Separator, Thumbnail
from typing import Optional
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger('bot')

# Constants
COLOR = 0x2f3136
SUCCESS_COLOR = 0x00ff88
ERROR_COLOR = 0xff0033

class ServerUtility(commands.Cog):
    """Advanced server utility commands for tracking invites, voice, messages, and more"""
    
    def __init__(self, bot):
        self.bot = bot
        self.color = COLOR
        
        # Get MongoDB collections from bot instance
        self.invite_stats_collection = bot.db["invite_stats"]
        self.voice_stats_collection = bot.db["voice_stats"]
        self.message_stats_collection = bot.db["message_stats"]
        self.blacklist_channels_collection = bot.db["blacklist_channels"]
        
        logger.info("\x1b[38;5;197m[Cog]\x1b[0m ServerUtility cog initialized")
    
    # ==================== INVITE COMMANDS ====================
    
    @commands.command(name="invites", aliases=["invs"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def invites(self, ctx, member: Optional[discord.Member] = None):
        """Check how many people someone has invited"""
        member = member or ctx.author
        
        stats = await self.invite_stats_collection.find_one({
            "guild_id": ctx.guild.id,
            "user_id": member.id
        })
        
        invites = stats.get("total_invites", 0) if stats else 0
        fake = stats.get("fake_invites", 0) if stats else 0
        left = stats.get("left_invites", 0) if stats else 0
        real = invites - fake - left
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## 📨 Invite Statistics - {member.name}"))
        container.add_item(Separator())
        
        desc = f"**Total Invites:** {invites:,}\n"
        desc += f"**Real Invites:** {real:,}\n"
        desc += f"**Fake Invites:** {fake:,}\n"
        desc += f"**Left Invites:** {left:,}"
        
        thumb = Thumbnail(member.display_avatar.url)
        section = Section(TextDisplay(desc), accessory=thumb)
        container.add_item(section)
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="addinvite", aliases=["addinv"])
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def addinvite(self, ctx, member: discord.Member, amount: int = 1):
        """Add invites to a member (Admin only)"""
        if amount < 1:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Amount must be greater than 0"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        await self.invite_stats_collection.update_one(
            {"guild_id": ctx.guild.id, "user_id": member.id},
            {"$inc": {"total_invites": amount}},
            upsert=True
        )
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"✅ Added **{amount}** invite(s) to {member.name}"))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="removeinvite", aliases=["reminv"])
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def removeinvite(self, ctx, member: discord.Member, amount: int = 1):
        """Remove invites from a member (Admin only)"""
        if amount < 1:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Amount must be greater than 0"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        await self.invite_stats_collection.update_one(
            {"guild_id": ctx.guild.id, "user_id": member.id},
            {"$inc": {"total_invites": -amount}},
            upsert=True
        )
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"✅ Removed **{amount}** invite(s) from {member.name}"))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="resetmyinvite", aliases=["resetmyinv"])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def resetmyinvite(self, ctx):
        """Reset your own invite count"""
        result = await self.invite_stats_collection.delete_one({
            "guild_id": ctx.guild.id,
            "user_id": ctx.author.id
        })
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"✅ Your invite count has been reset!"))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="resetinvites", aliases=["resetinvs"])
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 120, commands.BucketType.guild)
    async def resetinvites(self, ctx):
        """Reset all invite counts in the server (Admin only)"""
        result = await self.invite_stats_collection.delete_many({
            "guild_id": ctx.guild.id
        })
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"✅ Reset **{result.deleted_count}** invite records!"))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="invited")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def invited(self, ctx, member: Optional[discord.Member] = None):
        """Check who invited a member"""
        member = member or ctx.author
        
        stats = await self.invite_stats_collection.find_one({
            "guild_id": ctx.guild.id,
            "user_id": member.id
        })
        
        view = LayoutView()
        container = Container()
        
        if not stats or not stats.get("invited_by"):
            container.add_item(TextDisplay(f"## 📨 Invite Info\n\nCouldn't find who invited {member.name}"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        inviter = ctx.guild.get_member(stats["invited_by"])
        inviter_name = inviter.name if inviter else "Unknown User"
        
        container.add_item(TextDisplay(f"## 📨 Invite Info"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"{member.name} was invited by {inviter_name}"))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="inviter")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def inviter(self, ctx, member: Optional[discord.Member] = None):
        """Check who invited you or another member"""
        await self.invited(ctx, member)
    
    @commands.command(name="inviteinfo", aliases=["invinfo"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def inviteinfo(self, ctx, member: Optional[discord.Member] = None):
        """Get detailed invite information about a member"""
        member = member or ctx.author
        
        stats = await self.invite_stats_collection.find_one({
            "guild_id": ctx.guild.id,
            "user_id": member.id
        })
        
        invites = stats.get("total_invites", 0) if stats else 0
        fake = stats.get("fake_invites", 0) if stats else 0
        left = stats.get("left_invites", 0) if stats else 0
        real = invites - fake - left
        invited_by = stats.get("invited_by") if stats else None
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## 📨 Detailed Invite Info - {member.name}"))
        container.add_item(Separator())
        
        desc = f"**Total Invites:** {invites:,}\n"
        desc += f"**Real Invites:** {real:,}\n"
        desc += f"**Fake Invites:** {fake:,}\n"
        desc += f"**Left Invites:** {left:,}\n\n"
        
        if invited_by:
            inviter = ctx.guild.get_member(invited_by)
            desc += f"**Invited By:** {inviter.name if inviter else 'Unknown User'}"
        else:
            desc += "**Invited By:** Unknown"
        
        thumb = Thumbnail(member.display_avatar.url)
        section = Section(TextDisplay(desc), accessory=thumb)
        container.add_item(section)
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    # ==================== VOICE COMMANDS ====================
    
    @commands.command(name="checkvoice", aliases=["voicestats"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def checkvoice(self, ctx, member: Optional[discord.Member] = None):
        """Check voice chat time statistics"""
        member = member or ctx.author
        
        stats = await self.voice_stats_collection.find_one({
            "guild_id": ctx.guild.id,
            "user_id": member.id
        })
        
        if not stats:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"## 🎤 No Voice Data\n\n{member.name} hasn't spent time in voice yet!"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        total_minutes = stats.get("total_minutes", 0)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## 🎤 Voice Statistics - {member.name}"))
        container.add_item(Separator())
        
        desc = f"**Total Time:** {hours}h {minutes}m\n"
        desc += f"**Total Minutes:** {total_minutes:,}"
        
        thumb = Thumbnail(member.display_avatar.url)
        section = Section(TextDisplay(desc), accessory=thumb)
        container.add_item(section)
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="addvoice")
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def addvoice(self, ctx, member: discord.Member, minutes: int = 1):
        """Add voice minutes to a member (Admin only)"""
        if minutes < 1:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Minutes must be greater than 0"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        await self.voice_stats_collection.update_one(
            {"guild_id": ctx.guild.id, "user_id": member.id},
            {"$inc": {"total_minutes": minutes}},
            upsert=True
        )
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"✅ Added **{minutes}** minute(s) to {member.name}"))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="removevoice")
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def removevoice(self, ctx, member: discord.Member, minutes: int = 1):
        """Remove voice minutes from a member (Admin only)"""
        if minutes < 1:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Minutes must be greater than 0"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        await self.voice_stats_collection.update_one(
            {"guild_id": ctx.guild.id, "user_id": member.id},
            {"$inc": {"total_minutes": -minutes}},
            upsert=True
        )
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"✅ Removed **{minutes}** minute(s) from {member.name}"))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="resetmyvoice")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def resetmyvoice(self, ctx):
        """Reset your own voice time"""
        await self.voice_stats_collection.delete_one({
            "guild_id": ctx.guild.id,
            "user_id": ctx.author.id
        })
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"✅ Your voice time has been reset!"))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="resetvoice")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 120, commands.BucketType.guild)
    async def resetvoice(self, ctx):
        """Reset all voice time in the server (Admin only)"""
        result = await self.voice_stats_collection.delete_many({
            "guild_id": ctx.guild.id
        })
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"✅ Reset **{result.deleted_count}** voice records!"))
        view.add_item(container)
        await ctx.reply(view=view)
    
    # ==================== MESSAGE COMMANDS ====================
    
    @commands.command(name="messages", aliases=["msgcount"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def messages(self, ctx, member: Optional[discord.Member] = None):
        """View message count for yourself or another member"""
        member = member or ctx.author
        
        stats = await self.message_stats_collection.find_one({
            "guild_id": ctx.guild.id,
            "user_id": member.id
        })
        
        if not stats:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"## 📊 No Stats Available\n\n{member.name} hasn't sent any messages yet!"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        total_msgs = stats.get("total_messages", 0)
        total_chars = stats.get("total_characters", 0)
        avg_chars = total_chars // total_msgs if total_msgs > 0 else 0
        
        all_stats = await self.message_stats_collection.find({"guild_id": ctx.guild.id}).sort("total_messages", -1).to_list(None)
        rank = next((i + 1 for i, s in enumerate(all_stats) if s["user_id"] == member.id), 0)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## 📊 Message Statistics - {member.name}"))
        container.add_item(Separator())
        
        desc = f"**Total Messages:** {total_msgs:,}\n"
        desc += f"**Total Characters:** {total_chars:,}\n"
        desc += f"**Average Characters:** {avg_chars:,}\n"
        desc += f"**Server Rank:** #{rank}"
        
        thumb = Thumbnail(member.display_avatar.url)
        section = Section(TextDisplay(desc), accessory=thumb)
        container.add_item(section)
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="addmessage", aliases=["addmsg"])
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def addmessage(self, ctx, member: discord.Member, amount: int = 1):
        """Add message count to a member (Admin only)"""
        if amount < 1:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Amount must be greater than 0"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        await self.message_stats_collection.update_one(
            {"guild_id": ctx.guild.id, "user_id": member.id},
            {"$inc": {"total_messages": amount}},
            upsert=True
        )
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"✅ Added **{amount}** message(s) to {member.name}"))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="removemessage", aliases=["remmsg"])
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def removemessage(self, ctx, member: discord.Member, amount: int = 1):
        """Remove message count from a member (Admin only)"""
        if amount < 1:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Amount must be greater than 0"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        await self.message_stats_collection.update_one(
            {"guild_id": ctx.guild.id, "user_id": member.id},
            {"$inc": {"total_messages": -amount}},
            upsert=True
        )
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"✅ Removed **{amount}** message(s) from {member.name}"))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="resetmymessages", aliases=["resetmymsg"])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def resetmymessages(self, ctx):
        """Reset your own message count"""
        await self.message_stats_collection.delete_one({
            "guild_id": ctx.guild.id,
            "user_id": ctx.author.id
        })
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"✅ Your message count has been reset!"))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="resetmessages", aliases=["resetmsgs"])
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 120, commands.BucketType.guild)
    async def resetmessages(self, ctx):
        """Reset all message counts in the server (Admin only)"""
        result = await self.message_stats_collection.delete_many({
            "guild_id": ctx.guild.id
        })
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"✅ Reset **{result.deleted_count}** message records!"))
        view.add_item(container)
        await ctx.reply(view=view)
    
    # ==================== LEADERBOARD COMMANDS ====================
    
    @commands.group(name="serverlb", aliases=["slb", "serverleaderboard"])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def leaderboard(self, ctx):
        """View various server statistic leaderboards"""
        if ctx.invoked_subcommand is None:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## 📊 Server Leaderboard Commands"))
            container.add_item(Separator())
            desc = (
                f"**Available Leaderboards:**\n\n"
                f"`{ctx.prefix}serverlb messages` - Message count\n"
                f"`{ctx.prefix}serverlb voice` - Voice time\n"
                f"`{ctx.prefix}serverlb invites` - Invite count\n"
                f"`{ctx.prefix}serverlb dailymessages` - Daily messages\n"
                f"`{ctx.prefix}serverlb dailyvoice` - Daily voice time"
            )
            container.add_item(TextDisplay(desc))
            view.add_item(container)
            await ctx.send(view=view)
    
    @leaderboard.command(name="messages", aliases=["msgs", "msg"])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def leaderboard_messages(self, ctx):
        """View message count leaderboard"""
        top_stats = await self.message_stats_collection.find({"guild_id": ctx.guild.id}).sort("total_messages", -1).limit(15).to_list(None)
        
        if not top_stats:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## 📊 No Data\n\nNo message data available yet!"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## 📊 Message Leaderboard - {ctx.guild.name}"))
        container.add_item(Separator())
        
        leaderboard = []
        medals = ["🥇", "🥈", "🥉"]
        
        for i, stats in enumerate(top_stats, 1):
            user = ctx.guild.get_member(stats["user_id"])
            if not user:
                continue
            
            medal = medals[i - 1] if i <= 3 else f"`{i}.`"
            total_msgs = stats.get("total_messages", 0)
            
            if user.id == ctx.author.id:
                leaderboard.append(f"{medal} **{user.name}** - **{total_msgs:,}** messages ⭐")
            else:
                leaderboard.append(f"{medal} **{user.name}** - {total_msgs:,} messages")
        
        if leaderboard:
            container.add_item(TextDisplay("\n".join(leaderboard)))
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Keep chatting to reach the top!"))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @leaderboard.command(name="voice", aliases=["vc"])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def leaderboard_voice(self, ctx):
        """View voice time leaderboard"""
        top_stats = await self.voice_stats_collection.find({"guild_id": ctx.guild.id}).sort("total_minutes", -1).limit(15).to_list(None)
        
        if not top_stats:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## 📊 No Data\n\nNo voice data available yet!"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## 🎤 Voice Leaderboard - {ctx.guild.name}"))
        container.add_item(Separator())
        
        leaderboard = []
        medals = ["🥇", "🥈", "🥉"]
        
        for i, stats in enumerate(top_stats, 1):
            user = ctx.guild.get_member(stats["user_id"])
            if not user:
                continue
            
            medal = medals[i - 1] if i <= 3 else f"`{i}.`"
            total_minutes = stats.get("total_minutes", 0)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            
            if user.id == ctx.author.id:
                leaderboard.append(f"{medal} **{user.name}** - **{hours}h {minutes}m** ⭐")
            else:
                leaderboard.append(f"{medal} **{user.name}** - {hours}h {minutes}m")
        
        if leaderboard:
            container.add_item(TextDisplay("\n".join(leaderboard)))
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Keep talking to reach the top!"))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @leaderboard.command(name="invites", aliases=["invs"])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def leaderboard_invites(self, ctx):
        """View invite count leaderboard"""
        top_stats = await self.invite_stats_collection.find({"guild_id": ctx.guild.id}).sort("total_invites", -1).limit(15).to_list(None)
        
        if not top_stats:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## 📊 No Data\n\nNo invite data available yet!"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## 📨 Invite Leaderboard - {ctx.guild.name}"))
        container.add_item(Separator())
        
        leaderboard = []
        medals = ["🥇", "🥈", "🥉"]
        
        for i, stats in enumerate(top_stats, 1):
            user = ctx.guild.get_member(stats["user_id"])
            if not user:
                continue
            
            medal = medals[i - 1] if i <= 3 else f"`{i}.`"
            total_invites = stats.get("total_invites", 0)
            
            if user.id == ctx.author.id:
                leaderboard.append(f"{medal} **{user.name}** - **{total_invites:,}** invites ⭐")
            else:
                leaderboard.append(f"{medal} **{user.name}** - {total_invites:,} invites")
        
        if leaderboard:
            container.add_item(TextDisplay("\n".join(leaderboard)))
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Keep inviting to reach the top!"))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @leaderboard.command(name="dailymessages", aliases=["dailymsg"])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def leaderboard_dailymessages(self, ctx):
        """View daily message count leaderboard"""
        top_stats = await self.message_stats_collection.find({"guild_id": ctx.guild.id}).sort("daily_messages", -1).limit(15).to_list(None)
        
        if not top_stats:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## 📊 No Data\n\nNo daily message data available yet!"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## 📊 Daily Message Leaderboard - {ctx.guild.name}"))
        container.add_item(Separator())
        
        leaderboard = []
        medals = ["🥇", "🥈", "🥉"]
        
        for i, stats in enumerate(top_stats, 1):
            user = ctx.guild.get_member(stats["user_id"])
            if not user:
                continue
            
            medal = medals[i - 1] if i <= 3 else f"`{i}.`"
            daily_msgs = stats.get("daily_messages", 0)
            
            if daily_msgs == 0:
                continue
            
            if user.id == ctx.author.id:
                leaderboard.append(f"{medal} **{user.name}** - **{daily_msgs:,}** messages today ⭐")
            else:
                leaderboard.append(f"{medal} **{user.name}** - {daily_msgs:,} messages today")
        
        if leaderboard:
            container.add_item(TextDisplay("\n".join(leaderboard)))
        else:
            container.add_item(TextDisplay("No daily message data available yet!"))
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Daily stats reset at midnight!"))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @leaderboard.command(name="dailyvoice", aliases=["dailyvc"])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def leaderboard_dailyvoice(self, ctx):
        """View daily voice time leaderboard"""
        top_stats = await self.voice_stats_collection.find({"guild_id": ctx.guild.id}).sort("daily_minutes", -1).limit(15).to_list(None)
        
        if not top_stats:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## 📊 No Data\n\nNo daily voice data available yet!"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## 🎤 Daily Voice Leaderboard - {ctx.guild.name}"))
        container.add_item(Separator())
        
        leaderboard = []
        medals = ["🥇", "🥈", "🥉"]
        
        for i, stats in enumerate(top_stats, 1):
            user = ctx.guild.get_member(stats["user_id"])
            if not user:
                continue
            
            medal = medals[i - 1] if i <= 3 else f"`{i}.`"
            daily_minutes = stats.get("daily_minutes", 0)
            
            if daily_minutes == 0:
                continue
            
            hours = daily_minutes // 60
            minutes = daily_minutes % 60
            
            if user.id == ctx.author.id:
                leaderboard.append(f"{medal} **{user.name}** - **{hours}h {minutes}m** today ⭐")
            else:
                leaderboard.append(f"{medal} **{user.name}** - {hours}h {minutes}m today")
        
        if leaderboard:
            container.add_item(TextDisplay("\n".join(leaderboard)))
        else:
            container.add_item(TextDisplay("No daily voice data available yet!"))
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Daily stats reset at midnight!"))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    # ==================== BLACKLIST CHANNEL COMMANDS ====================
    
    @commands.group(name="blacklistchannel", aliases=["blc"])
    @commands.has_permissions(manage_channels=True)
    async def blacklistchannel(self, ctx):
        """Blacklist channels from tracking stats"""
        if ctx.invoked_subcommand is None:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## 🚫 Blacklist Channel Commands"))
            container.add_item(Separator())
            desc = (
                f"**Available Commands:**\n\n"
                f"`{ctx.prefix}blacklistchannel add <#channel>` - Blacklist a channel\n"
                f"`{ctx.prefix}blacklistchannel remove <#channel>` - Remove from blacklist\n"
                f"`{ctx.prefix}blacklistchannel list` - View blacklisted channels\n"
                f"`{ctx.prefix}blacklistchannel reset` - Clear all blacklisted channels"
            )
            container.add_item(TextDisplay(desc))
            view.add_item(container)
            await ctx.send(view=view)
    
    @blacklistchannel.command(name="add")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def blacklistchannel_add(self, ctx, channel: discord.TextChannel):
        """Add a channel to the blacklist"""
        await self.blacklist_channels_collection.update_one(
            {"guild_id": ctx.guild.id, "channel_id": channel.id},
            {"$set": {"channel_name": channel.name, "added_at": datetime.now(timezone.utc)}},
            upsert=True
        )
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"✅ {channel.name} has been blacklisted from stat tracking!"))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @blacklistchannel.command(name="remove")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def blacklistchannel_remove(self, ctx, channel: discord.TextChannel):
        """Remove a channel from the blacklist"""
        result = await self.blacklist_channels_collection.delete_one({
            "guild_id": ctx.guild.id,
            "channel_id": channel.id
        })
        
        if result.deleted_count == 0:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ {channel.name} is not blacklisted!"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"✅ {channel.name} has been removed from blacklist!"))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @blacklistchannel.command(name="list")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def blacklistchannel_list(self, ctx):
        """View all blacklisted channels"""
        blacklisted = await self.blacklist_channels_collection.find({"guild_id": ctx.guild.id}).to_list(None)
        
        if not blacklisted:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## 🚫 No Blacklisted Channels\n\nNo channels are currently blacklisted!"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## 🚫 Blacklisted Channels - {ctx.guild.name}"))
        container.add_item(Separator())
        
        channel_list = []
        for bl in blacklisted:
            channel = ctx.guild.get_channel(bl["channel_id"])
            if channel:
                channel_list.append(f"• {channel.name}")
            else:
                channel_list.append(f"• *Deleted Channel* (`{bl['channel_id']}`)")
        
        container.add_item(TextDisplay("\n".join(channel_list)))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Total: {len(blacklisted)} blacklisted channels"))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @blacklistchannel.command(name="reset")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def blacklistchannel_reset(self, ctx):
        """Clear all blacklisted channels"""
        result = await self.blacklist_channels_collection.delete_many({
            "guild_id": ctx.guild.id
        })
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"✅ Removed **{result.deleted_count}** channels from blacklist!"))
        view.add_item(container)
        await ctx.reply(view=view)


async def setup(bot):
    await bot.add_cog(ServerUtility(bot))
