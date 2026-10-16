import discord
from discord.ext import commands
from discord import ui
from discord.ui import LayoutView, Container, TextDisplay, Separator, Button, Section, Thumbnail
import psutil
import time
import datetime
import asyncio
from utils.Tools import blacklist_check, ignore_check
from typing import Optional, Union

start_time = time.time()
color = 0x2f3136


class Extra(commands.Cog):
    """Extra utility commands"""

    def __init__(self, bot):
        self.bot = bot
        self.color = color

    @commands.group(name="banner", invoke_without_command=True)
    @blacklist_check()
    @ignore_check()
    async def banner(self, ctx):
        """View server or user banners"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @banner.command(name="server")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def banner_server(self, ctx):
        """Display server banner"""
        if not ctx.guild.banner:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## Server Banner"))
            container.add_item(Separator())
            container.add_item(TextDisplay("❌ This server does not have a banner."))
            view.add_item(container)
            return await ctx.reply(view=view)

        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## {ctx.guild.name}'s Banner"))
        container.add_item(Separator())
        
        # Add media gallery
        gallery = ui.MediaGallery()
        gallery.add_item(media=ctx.guild.banner.url)
        container.add_item(gallery)
        
        container.add_item(Separator())
        
        # Format links
        jpg = ctx.guild.banner.replace(format='jpg')
        png = ctx.guild.banner.replace(format='png')
        links = f"[PNG]({png}) | [JPG]({jpg})"
        if ctx.guild.banner.is_animated():
            gif = ctx.guild.banner.replace(format='gif')
            links += f" | [GIF]({gif})"
        
        container.add_item(TextDisplay(links))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Requested by {ctx.author.name}"))
        
        view.add_item(container)
        await ctx.reply(view=view)

    @banner.command(name="user")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def banner_user(self, ctx, member: Optional[Union[discord.Member, discord.User]] = None):
        """Display user banner"""
        if member is None:
            member = ctx.author
        
        bannerUser = await self.bot.fetch_user(member.id)
        
        if not bannerUser.banner:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## User Banner"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"❌ {member.name} does not have a banner."))
            view.add_item(container)
            return await ctx.reply(view=view)

        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## {member.name}'s Banner"))
        container.add_item(Separator())
        
        # Add media gallery
        gallery = ui.MediaGallery()
        gallery.add_item(media=bannerUser.banner.url)
        container.add_item(gallery)
        
        container.add_item(Separator())
        
        # Format links
        jpg = bannerUser.banner.replace(format='jpg')
        png = bannerUser.banner.replace(format='png')
        links = f"[PNG]({png}) | [JPG]({jpg})"
        if bannerUser.banner.is_animated():
            gif = bannerUser.banner.replace(format='gif')
            links += f" | [GIF]({gif})"
        
        container.add_item(TextDisplay(links))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Requested by {ctx.author.name}"))
        
        view.add_item(container)
        await ctx.reply(view=view)

    @commands.command(
        name="statistics",
        aliases=["botstats", "botinfos"],
        help="Shows useful statistics about the bot"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def stats(self, ctx):
        """Shows bot statistics using Component V2"""
        loading_view = LayoutView()
        loading_container = Container()
        loading_container.add_item(TextDisplay("## Loading Statistics"))
        loading_container.add_item(Separator())
        loading_container.add_item(TextDisplay("⏳ Fetching info from database..."))
        loading_view.add_item(loading_container)
        
        loading_message = await ctx.send(view=loading_view)
        
        # Calculate statistics
        server_count = len(self.bot.guilds)
        text_channels = sum(len(guild.text_channels) for guild in self.bot.guilds)
        voice_channels = sum(len(guild.voice_channels) for guild in self.bot.guilds)
        categories = sum(len(guild.categories) for guild in self.bot.guilds)
        total_channels = text_channels + voice_channels + categories
        
        cached_users = len(self.bot.users)
        total_members = sum(g.member_count for g in self.bot.guilds if g.member_count)
        
        used_memory = psutil.virtual_memory().percent
        cpu_used = psutil.cpu_percent()
        
        uptime_seconds = int(round(time.time() - start_time))
        uptime_str = str(datetime.timedelta(seconds=uptime_seconds))
        
        await asyncio.sleep(1)
        
        # Build stats view
        view = LayoutView()
        container = Container()
        
        # Header with bot thumbnail
        thumb = Thumbnail(self.bot.user.display_avatar.url)
        header_text = f"## About {self.bot.user.name}\n\nA Feature Rich Advanced Multipurpose Bot. Build The Community Of Your Dreams!"
        section = Section(TextDisplay(header_text), accessory=thumb)
        container.add_item(section)
        
        container.add_item(Separator())
        
        # Bot statistics
        bot_stats = (
            f"**Server Count:** {server_count:,} Guilds\n"
            f"**Total Users:** {total_members:,} Users | {cached_users:,} Cached\n\n"
            f"**Channels:**\n"
            f"• Total: {total_channels:,} Channels\n"
            f"• Text: {text_channels:,} Channels\n"
            f"• Voice: {voice_channels:,} Channels\n"
            f"• Categories: {categories:,} Channels"
        )
        container.add_item(TextDisplay(bot_stats))
        
        container.add_item(Separator())
        
        # Server usage
        server_stats = (
            f"**Server Usage:**\n"
            f"• CPU Usage: {cpu_used}%\n"
            f"• Memory Usage: {used_memory}%\n"
            f"• Uptime: {uptime_str}"
        )
        container.add_item(TextDisplay(server_stats))
        
        container.add_item(Separator())
        
        # Shard info
        if hasattr(self.bot, 'shard_count') and ctx.guild:
            shard_info = f"**Shard:** {ctx.guild.shard_id + 1}/{self.bot.shard_count}"
            container.add_item(TextDisplay(shard_info))
            container.add_item(Separator())
        
        # Add buttons
        button_row = ui.ActionRow()
        support_btn = Button(label="Support Server", url="https://discord.gg/support", style=discord.ButtonStyle.link)
        invite_btn = Button(label="Invite Me", url=f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot%20applications.commands", style=discord.ButtonStyle.link)
        button_row.add_item(support_btn)
        button_row.add_item(invite_btn)
        container.add_item(button_row)
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Requested by {ctx.author.name}"))
        
        view.add_item(container)
        
        await loading_message.delete()
        await ctx.send(view=view)

    @commands.command(name="botinvite", aliases=['binvite', 'invitebot'])
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def invite(self, ctx):
        """Get bot invite link"""
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## Invite {self.bot.user.name}"))
        container.add_item(Separator())
        
        invite_url = f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot%20applications.commands"
        support_url = "https://discord.gg/support"
        
        content = (
            f"**Invite Link:**\n"
            f"[Click Here To Invite {self.bot.user.name}]({invite_url})\n\n"
            f"**Support Server:**\n"
            f"[Click Here To Join Support Server]({support_url})"
        )
        container.add_item(TextDisplay(content))
        
        container.add_item(Separator())
        
        # Add buttons
        button_row = ui.ActionRow()
        support_btn = Button(label="Support Server", url=support_url, style=discord.ButtonStyle.link)
        invite_btn = Button(label="Invite Me", url=invite_url, style=discord.ButtonStyle.link)
        button_row.add_item(invite_btn)
        button_row.add_item(support_btn)
        container.add_item(button_row)
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Requested by {ctx.author.name}"))
        
        view.add_item(container)
        await ctx.reply(view=view)

    @commands.command(
        name="aboutbot",
        aliases=['bi'],
        help="Get information about the bot"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def botinfo(self, ctx):
        """Display bot information using Component V2"""
        users = sum(g.member_count for g in self.bot.guilds if g.member_count)
        channels = len(set(self.bot.get_all_channels()))
        commands_count = len(set(self.bot.walk_commands()))
        
        uptime_seconds = int(round(time.time() - start_time))
        uptime_str = str(datetime.timedelta(seconds=uptime_seconds))
        
        memory_usage = int((psutil.virtual_memory().total - psutil.virtual_memory().available) / 1024 / 1024)
        cpu_usage = round(psutil.cpu_percent())
        
        view = LayoutView()
        container = Container()
        
        # Header with bot thumbnail
        thumb = Thumbnail(self.bot.user.display_avatar.url)
        header_text = f"## {self.bot.user.name}'s Information"
        section = Section(TextDisplay(header_text), accessory=thumb)
        container.add_item(section)
        
        container.add_item(Separator())
        
        # Bot info
        bot_info = (
            f"**Bot Username:** {self.bot.user}\n"
            f"**Bot ID:** {self.bot.user.id}\n"
            f"**Total Guilds:** {len(self.bot.guilds):,}\n"
            f"**Total Users:** {users:,}\n"
            f"**Total Channels:** {channels:,}\n"
            f"**Total Commands:** {commands_count}\n"
            f"**Uptime:** {uptime_str}\n"
            f"**CPU Usage:** {cpu_usage}%\n"
            f"**Memory Usage:** {memory_usage} MB\n"
            f"**Websocket Latency:** {int(self.bot.latency * 1000)} ms\n"
            f"**Discord.py Version:** {discord.__version__}"
        )
        container.add_item(TextDisplay(bot_info))
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Requested by {ctx.author.name}"))
        
        view.add_item(container)
        await ctx.reply(view=view)

    @commands.command(
        name="serverinfos",
        aliases=["guildinfo"],
        help="Display server information"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def serverinfo(self, ctx):
        """Display server information using Component V2"""
        guild = ctx.guild
        c_at = int(guild.created_at.timestamp())
        
        # NSFW level
        nsfw_level_map = {
            'default': 'Default',
            'explicit': 'Explicit',
            'safe': 'Safe',
            'age_restricted': 'Age Restricted'
        }
        nsfw_level = nsfw_level_map.get(guild.nsfw_level.name, 'Unknown')
        
        # Count emojis and stickers
        total_emojis = len(guild.emojis)
        total_stickers = len(guild.stickers)
        
        # Boost info
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count or 0
        
        view = LayoutView()
        container = Container()
        
        # Header with server icon
        if guild.icon:
            thumb = Thumbnail(guild.icon.url)
            header_text = f"## {guild.name}'s Information"
            section = Section(TextDisplay(header_text), accessory=thumb)
            container.add_item(section)
        else:
            container.add_item(TextDisplay(f"## {guild.name}'s Information"))
        
        container.add_item(Separator())
        
        # About section
        about_info = (
            f"**Name:** {guild.name}\n"
            f"**ID:** {guild.id}\n"
            f"**Owner:** {guild.owner.name} ({guild.owner_id})\n"
            f"**Created At:** <t:{c_at}:F>\n"
            f"**Members:** {len(guild.members):,}"
        )
        container.add_item(TextDisplay(about_info))
        
        container.add_item(Separator())
        
        # Extras section
        extras_info = (
            f"**Verification Level:** {str(guild.verification_level).capitalize()}\n"
            f"**NSFW Level:** {nsfw_level}\n"
            f"**Boost Level:** Level {boost_level}\n"
            f"**Boost Count:** {boost_count}\n"
            f"**Emojis:** {total_emojis}\n"
            f"**Stickers:** {total_stickers}\n"
            f"**Roles:** {len(guild.roles)}\n"
            f"**Channels:** {len(guild.channels)}"
        )
        container.add_item(TextDisplay(extras_info))
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Requested by {ctx.author.name}"))
        
        view.add_item(container)
        await ctx.reply(view=view)

    @commands.command(
        name="totalusers",
        aliases=["tusers", "allusers"],
        help="Shows total users across all shards"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def totalusers(self, ctx):
        """Display total users across all shards using Component V2"""
        # Calculate total users across all shards
        total_members = sum(g.member_count for g in self.bot.guilds if g.member_count)
        total_guilds = len(self.bot.guilds)
        cached_users = len(self.bot.users)
        
        # Calculate shard information
        shard_count = getattr(self.bot, 'shard_count', 1)
        current_shard = ctx.guild.shard_id + 1 if ctx.guild and hasattr(ctx.guild, 'shard_id') else 1
        
        # Calculate per-shard statistics
        shard_stats = {}
        for guild in self.bot.guilds:
            shard_id = guild.shard_id if hasattr(guild, 'shard_id') else 0
            if shard_id not in shard_stats:
                shard_stats[shard_id] = {'guilds': 0, 'members': 0}
            shard_stats[shard_id]['guilds'] += 1
            shard_stats[shard_id]['members'] += guild.member_count or 0
        
        view = LayoutView()
        container = Container()
        
        # Header with bot thumbnail
        thumb = Thumbnail(self.bot.user.display_avatar.url)
        header_text = f"## {self.bot.user.name} - Total Users"
        section = Section(TextDisplay(header_text), accessory=thumb)
        container.add_item(section)
        
        container.add_item(Separator())
        
        # Overall statistics
        overall_stats = (
            f"**Total Statistics:**\n"
            f"• Total Members: **{total_members:,}**\n"
            f"• Cached Users: **{cached_users:,}**\n"
            f"• Total Guilds: **{total_guilds:,}**\n"
            f"• Total Shards: **{shard_count}**\n"
            f"• Current Shard: **{current_shard}/{shard_count}**"
        )
        container.add_item(TextDisplay(overall_stats))
        
        container.add_item(Separator())
        
        # Shard breakdown (show up to 10 shards)
        shard_breakdown = "**Shard Breakdown:**\n"
        for shard_id in sorted(shard_stats.keys())[:10]:
            stats = shard_stats[shard_id]
            shard_breakdown += (
                f"**Shard {shard_id + 1}:** "
                f"{stats['members']:,} members in {stats['guilds']} guilds\n"
            )
        
        if len(shard_stats) > 10:
            shard_breakdown += f"\n*...and {len(shard_stats) - 10} more shards*"
        
        container.add_item(TextDisplay(shard_breakdown))
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Requested by {ctx.author.name}"))
        
        view.add_item(container)
        await ctx.reply(view=view)


async def setup(bot):
    await bot.add_cog(Extra(bot))
