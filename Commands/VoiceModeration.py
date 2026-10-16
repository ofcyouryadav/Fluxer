import discord
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay, Separator, Section, Thumbnail
from typing import Optional, List
import asyncio

COLOR = 0x2f3136
SUCCESS_COLOR = 0x00ff88
ERROR_COLOR = 0xff0033

class VoiceModeration(commands.Cog):
    """Voice moderation and control commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.color = COLOR
    
    async def cog_check(self, ctx):
        """Require manage channels permission for all commands"""
        return ctx.author.guild_permissions.manage_channels or ctx.author.guild_permissions.move_members
    
    # ====================DEAFEN COMMANDS====================
    
    @commands.hybrid_command(name="vcdeafen", aliases=["vcd"])
    @commands.has_permissions(mute_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def vcdeafen(self, ctx, member: discord.Member):
        """Server deafen a member in voice channel"""
        if not member.voice:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ {member.name} is not in a voice channel."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        await member.edit(deafen=True)
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## ✅ Member Deafened"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"**{member.name}** has been server deafened."))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.hybrid_command(name="vcdeafenall")
    @commands.has_permissions(mute_members=True)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def vcdeafenall(self, ctx, channel: Optional[discord.VoiceChannel] = None):
        """Server deafen all members in a voice channel"""
        if not channel:
            if ctx.author.voice:
                channel = ctx.author.voice.channel
            else:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("❌ Please join a voice channel or specify one."))
                view.add_item(container)
                return await ctx.reply(view=view)
        
        deafened_count = 0
        for member in channel.members:
            if not member.bot and not member.voice.deaf:
                try:
                    await member.edit(deafen=True)
                    deafened_count += 1
                except:
                    pass
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## ✅ Bulk Deafen Complete"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"Server deafened **{deafened_count}** members in {channel.name}."))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.hybrid_command(name="vcundeafen", aliases=["vcud"])
    @commands.has_permissions(mute_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def vcundeafen(self, ctx, member: discord.Member):
        """Undeafen a member in voice channel"""
        if not member.voice:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ {member.name} is not in a voice channel."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        await member.edit(deafen=False)
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## ✅ Member Undeafened"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"**{member.name}** has been undeafened."))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.hybrid_command(name="vcundeafenall")
    @commands.has_permissions(mute_members=True)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def vcundeafenall(self, ctx, channel: Optional[discord.VoiceChannel] = None):
        """Undeafen all members in a voice channel"""
        if not channel:
            if ctx.author.voice:
                channel = ctx.author.voice.channel
            else:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("❌ Please join a voice channel or specify one."))
                view.add_item(container)
                return await ctx.reply(view=view)
        
        undeafened_count = 0
        for member in channel.members:
            if member.voice.deaf:
                try:
                    await member.edit(deafen=False)
                    undeafened_count += 1
                except:
                    pass
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## ✅ Bulk Undeafen Complete"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"Undeafened **{undeafened_count}** members in {channel.name}."))
        view.add_item(container)
        await ctx.reply(view=view)
    
    # ====================MUTE COMMANDS====================
    
    @commands.hybrid_command(name="vcmute", aliases=["vcm"])
    @commands.has_permissions(mute_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def vcmute(self, ctx, member: discord.Member):
        """Server mute a member in voice channel"""
        if not member.voice:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ {member.name} is not in a voice channel."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        await member.edit(mute=True)
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## ✅ Member Muted"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"**{member.name}** has been server muted."))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.hybrid_command(name="vcmuteall")
    @commands.has_permissions(mute_members=True)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def vcmuteall(self, ctx, channel: Optional[discord.VoiceChannel] = None):
        """Server mute all members in a voice channel"""
        if not channel:
            if ctx.author.voice:
                channel = ctx.author.voice.channel
            else:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("❌ Please join a voice channel or specify one."))
                view.add_item(container)
                return await ctx.reply(view=view)
        
        muted_count = 0
        for member in channel.members:
            if not member.bot and not member.voice.mute:
                try:
                    await member.edit(mute=True)
                    muted_count += 1
                except:
                    pass
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## ✅ Bulk Mute Complete"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"Server muted **{muted_count}** members in {channel.name}."))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.hybrid_command(name="vcunmute", aliases=["vcum"])
    @commands.has_permissions(mute_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def vcunmute(self, ctx, member: discord.Member):
        """Unmute a member in voice channel"""
        if not member.voice:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ {member.name} is not in a voice channel."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        await member.edit(mute=False)
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## ✅ Member Unmuted"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"**{member.name}** has been unmuted."))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.hybrid_command(name="vcunmuteall")
    @commands.has_permissions(mute_members=True)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def vcunmuteall(self, ctx, channel: Optional[discord.VoiceChannel] = None):
        """Unmute all members in a voice channel"""
        if not channel:
            if ctx.author.voice:
                channel = ctx.author.voice.channel
            else:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("❌ Please join a voice channel or specify one."))
                view.add_item(container)
                return await ctx.reply(view=view)
        
        unmuted_count = 0
        for member in channel.members:
            if member.voice.mute:
                try:
                    await member.edit(mute=False)
                    unmuted_count += 1
                except:
                    pass
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## ✅ Bulk Unmute Complete"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"Unmuted **{unmuted_count}** members in {channel.name}."))
        view.add_item(container)
        await ctx.reply(view=view)
    
    # ====================KICK COMMANDS====================
    
    @commands.hybrid_command(name="vckick", aliases=["voicekick"])
    @commands.has_permissions(move_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def vckick(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member from voice channel"""
        if not member.voice:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ {member.name} is not in a voice channel."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        channel_name = member.voice.channel.name
        await member.move_to(None, reason=reason)
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## ✅ Member Kicked"))
        container.add_item(Separator())
        desc = f"**Member:** {member.name}\n**Channel:** {channel_name}\n**Reason:** {reason}"
        container.add_item(TextDisplay(desc))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.hybrid_command(name="vckickall")
    @commands.has_permissions(move_members=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def vckickall(self, ctx, channel: Optional[discord.VoiceChannel] = None):
        """Kick all members from a voice channel"""
        if not channel:
            if ctx.author.voice:
                channel = ctx.author.voice.channel
            else:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("❌ Please join a voice channel or specify one."))
                view.add_item(container)
                return await ctx.reply(view=view)
        
        kicked_count = 0
        for member in list(channel.members):
            if member != ctx.author and not member.bot:
                try:
                    await member.move_to(None)
                    kicked_count += 1
                except:
                    pass
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## ✅ Channel Cleared"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"Kicked **{kicked_count}** members from {channel.name}."))
        view.add_item(container)
        await ctx.reply(view=view)
    
    # ====================MOVE COMMANDS====================
    
    @commands.hybrid_command(name="vcmove", aliases=["vmove"])
    @commands.has_permissions(move_members=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def vcmove(self, ctx, member: discord.Member, channel: discord.VoiceChannel):
        """Move a member to another voice channel"""
        if not member.voice:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ {member.name} is not in a voice channel."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        old_channel = member.voice.channel.name
        await member.move_to(channel)
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## ✅ Member Moved"))
        container.add_item(Separator())
        desc = f"**Member:** {member.name}\n**From:** {old_channel}\n**To:** {channel.name}"
        container.add_item(TextDisplay(desc))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.hybrid_command(name="vcmoveall")
    @commands.has_permissions(move_members=True)
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def vcmoveall(self, ctx, from_channel: discord.VoiceChannel, to_channel: discord.VoiceChannel):
        """Move all members from one voice channel to another"""
        moved_count = 0
        for member in list(from_channel.members):
            try:
                await member.move_to(to_channel)
                moved_count += 1
            except:
                pass
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## ✅ Bulk Move Complete"))
        container.add_item(Separator())
        desc = f"Moved **{moved_count}** members\n**From:** {from_channel.name}\n**To:** {to_channel.name}"
        container.add_item(TextDisplay(desc))
        view.add_item(container)
        await ctx.reply(view=view)
    
    # ====================INFO COMMANDS====================
    
    @commands.hybrid_command(name="vclist", aliases=["voicelist"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def vclist(self, ctx, channel: Optional[discord.VoiceChannel] = None):
        """List all members in a voice channel"""
        if not channel:
            if ctx.author.voice:
                channel = ctx.author.voice.channel
            else:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("❌ Please join a voice channel or specify one."))
                view.add_item(container)
                return await ctx.reply(view=view)
        
        if not channel.members:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"## 🎙️ {channel.name}\n\nNo members in this channel."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        # Create member list
        members_list = []
        for i, member in enumerate(channel.members, 1):
            status = []
            if member.voice.self_mute:
                status.append("🔇")
            if member.voice.self_deaf:
                status.append("🔉")
            if member.voice.mute:
                status.append("🔴")
            if member.voice.deaf:
                status.append("🔕")
            if member.voice.self_stream:
                status.append("📹")
            if member.voice.self_video:
                status.append("🎥")
            
            status_str = " ".join(status) if status else ""
            members_list.append(f"`{i}.` {member.name} {status_str}")
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## 🎙️ Voice Channel - {channel.name}"))
        container.add_item(Separator())
        container.add_item(TextDisplay("\n".join(members_list)))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Total: {len(channel.members)} members"))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.hybrid_command(name="vcrole")
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def vcrole(self, ctx, role: discord.Role, channel: Optional[discord.VoiceChannel] = None):
        """Give a role to everyone in a voice channel"""
        if not channel:
            if ctx.author.voice:
                channel = ctx.author.voice.channel
            else:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("❌ Please join a voice channel or specify one."))
                view.add_item(container)
                return await ctx.reply(view=view)
        
        added_count = 0
        for member in channel.members:
            if role not in member.roles:
                try:
                    await member.add_roles(role, reason=f"Voice channel role by {ctx.author}")
                    added_count += 1
                except:
                    pass
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## ✅ Role Added"))
        container.add_item(Separator())
        desc = f"Added {role.name} to **{added_count}** members in {channel.name}."
        container.add_item(TextDisplay(desc))
        view.add_item(container)
        await ctx.reply(view=view)


async def setup(bot):
    await bot.add_cog(VoiceModeration(bot))
