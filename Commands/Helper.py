import os 
import discord
from discord.ext import commands
import datetime
import sys
import time
from utils.Tools import *
from discord.ext.commands import BucketType, cooldown
from typing import Optional, Union
from core import Cryptora, Context
from discord.ui import LayoutView, Container, TextDisplay, Separator, MediaGallery

start_time = time.time()

tick = "<:cryptora_tick:1404521529693306890>"
cross = "<:cryptora_cross:1404521609569501417>"

SUCCESS_COLOR = 0x00ff88
ERROR_COLOR = 0xff0033
INFO_COLOR = 0x2f3136


class Helper(commands.Cog):
    def __init__(self, bot: Cryptora):
        self.bot = bot
        self.color = 0x000000

    def create_response(self, title: str, description: str = "", color: int = INFO_COLOR):
        """Helper to create Component V2 responses"""
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## {title}"))
        if description:
            container.add_item(Separator())
            container.add_item(TextDisplay(description))
        view.add_item(container)
        return view

    @commands.command(name="uptime", description="Shows the Bot's Uptime.")
    @blacklist_check() 
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def uptime(self, ctx):
        uptime_seconds = int(round(time.time() - start_time))
        uptime_timedelta = datetime.timedelta(seconds=uptime_seconds)

        uptime_string = f"Up since {datetime.datetime.utcfromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')} UTC"
        uptime_duration_string = f"{uptime_timedelta.days} days, {uptime_timedelta.seconds // 3600} hours, {(uptime_timedelta.seconds // 60) % 60} minutes, {uptime_timedelta.seconds % 60} seconds"

        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay("## ⏱️ Bot Uptime"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"**UTC Time:** {uptime_string}"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"**Online Duration:**\n{uptime_duration_string}"))
        view.add_item(container)

        await ctx.send(view=view)

    @commands.hybrid_command(name="serverinfo", aliases=["sinfo", "si"], with_app_command=True)
    @blacklist_check() 
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def serverinfo(self, ctx):
        c_at = ctx.guild.created_at.strftime("%Y-%m-%d %H:%M:%S")

        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## 📊 {ctx.guild.name}'s Information"))
        container.add_item(Separator())

        # About Section
        container.add_item(TextDisplay(
            f"**__About__**\n"
            f"**Name:** {ctx.guild.name}\n"
            f"**ID:** {ctx.guild.id}\n"
            f"**Owner:** {ctx.guild.owner} (<@{ctx.guild.owner_id}>)\n"
            f"**Created At:** {c_at}\n"
            f"**Members:** {len(ctx.guild.members)}"
        ))
        container.add_item(Separator())

        # Description if exists
        if ctx.guild.description:
            container.add_item(TextDisplay(f"**__Description__**\n{ctx.guild.description}"))
            container.add_item(Separator())

        # General Stats
        container.add_item(TextDisplay(
            f"**__General Stats__**\n"
            f"**Verification Level:** {ctx.guild.verification_level}\n"
            f"**Channels:** {len(ctx.guild.channels)}\n"
            f"**Roles:** {len(ctx.guild.roles)}\n"
            f"**Emojis:** {len(ctx.guild.emojis)}\n"
            f"**Boost Level:** {ctx.guild.premium_tier} ({ctx.guild.premium_subscription_count} boosts)"
        ))
        container.add_item(Separator())

        # Features
        if ctx.guild.features:
            features = "\n".join([f"{tick} {feature[:1].upper() + feature[1:].lower().replace('_', ' ')}" for feature in ctx.guild.features])
            container.add_item(TextDisplay(
                f"**__Features__**\n{features if len(features) <= 1024 else features[0:1000] + '...and more'}"
            ))
            container.add_item(Separator())

        # Channels
        container.add_item(TextDisplay(
            f"**__Channels__**\n"
            f"**Total:** {len(ctx.guild.channels)}\n"
            f"**Text:** {len(ctx.guild.text_channels)}\n"
            f"**Voice:** {len(ctx.guild.voice_channels)}"
        ))
        container.add_item(Separator())

        # Emoji Info
        regular_emojis = [emoji for emoji in ctx.guild.emojis if not emoji.animated]
        animated_emojis = [emoji for emoji in ctx.guild.emojis if emoji.animated]
        container.add_item(TextDisplay(
            f"**__Emoji Info__**\n"
            f"**Regular:** {len(regular_emojis)}/100\n"
            f"**Animated:** {len(animated_emojis)}/100\n"
            f"**Total:** {len(ctx.guild.emojis)}/200"
        ))
        container.add_item(Separator())

        # Server Roles
        roles = ctx.guild.roles
        roles_list = [role.name for role in roles]
        roles_count = len(roles_list)
        roles_display = "\n".join(roles_list[:10])
        if roles_count > 10:
            roles_display += f"\n...and {roles_count - 10} more"

        container.add_item(TextDisplay(f"**__Server Roles [{roles_count}]__**\n{roles_display}"))

        # Add banner if exists
        if ctx.guild.banner:
            container.add_item(Separator())
            media_gallery = MediaGallery()
            media_gallery.add_item(media=ctx.guild.banner.url)
            container.add_item(media_gallery)

        view.add_item(container)
        await ctx.send(view=view)

    @commands.hybrid_command(name="userinfo", aliases=["whois", "ui"], usage="Userinfo [user]", with_app_command=True)
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    async def _userinfo(self, ctx, member: Optional[Union[discord.Member, discord.User]] = None):
        if member is None or member == "":
            member = ctx.author
        elif member not in ctx.guild.members:
            member = await self.bot.fetch_user(member.id)

        # Collect badges
        badges = []
        if member.public_flags.hypesquad:
            badges.append("HypeSquad Events")
        if member.public_flags.hypesquad_balance:
            badges.append("HypeSquad Balance")
        if member.public_flags.hypesquad_bravery:
            badges.append("HypeSquad Bravery")
        if member.public_flags.hypesquad_brilliance:
            badges.append("HypeSquad Brilliance")
        if member.public_flags.early_supporter:
            badges.append("Early Supporter")
        if member.public_flags.active_developer:
            badges.append("Active Developer")
        if member.public_flags.verified_bot_developer:
            badges.append("Early Verified Bot Developer")
        if member.public_flags.discord_certified_moderator:
            badges.append("Moderators Program Alumni")
        if member.public_flags.staff:
            badges.append("Discord Staff")
        if member.public_flags.partner:
            badges.append("Partnered Server Owner")

        badges_text = ", ".join(badges) if badges else cross

        # Member info
        if member in ctx.guild.members:
            nickk = member.nick if member.nick else "None"
            joinedat = f"<t:{round(member.joined_at.timestamp())}:R>"
        else:
            nickk = "None"
            joinedat = "None"

        # Permissions
        perms = []
        if member in ctx.guild.members:
            if member.guild_permissions.kick_members:
                perms.append("Kick Members")
            if member.guild_permissions.ban_members:
                perms.append("Ban Members")
            if member.guild_permissions.administrator:
                perms.append("Administrator")
            if member.guild_permissions.manage_guild:
                perms.append("Manage Server")
            if member.guild_permissions.manage_channels:
                perms.append("Manage Channels")
            if member.guild_permissions.manage_messages:
                perms.append("Manage Messages")
            if member.guild_permissions.mention_everyone:
                perms.append("Mention @everyone")
            if member.guild_permissions.manage_roles:
                perms.append("Manage Roles")
            if member.guild_permissions.manage_webhooks:
                perms.append("Manage Webhooks")

        perms_text = ", ".join(perms) if perms else cross

        # Create Component V2 response
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## 👤 {member.name}'s Information"))
        container.add_item(Separator())

        # Account Info
        container.add_item(TextDisplay(
            f"**__Account Info__**\n"
            f"**Username:** {member}\n"
            f"**ID:** {member.id}\n"
            f"**Created:** <t:{round(member.created_at.timestamp())}:R>"
        ))
        container.add_item(Separator())

        # Badges
        container.add_item(TextDisplay(f"**__Badges__**\n{badges_text}"))
        container.add_item(Separator())

        # Guild Member Info
        if member in ctx.guild.members:
            container.add_item(TextDisplay(
                f"**__Guild Member Info__**\n"
                f"**Nickname:** {nickk}\n"
                f"**Joined:** {joinedat}\n"
                f"**Roles:** {len(member.roles) - 1}"
            ))
            container.add_item(Separator())

            # Permissions
            container.add_item(TextDisplay(f"**__Permissions__**\n{perms_text}"))
            container.add_item(Separator())

        # Avatar
        if member.avatar:
            container.add_item(Separator())
            media_gallery = MediaGallery()
            media_gallery.add_item(media=member.avatar.url)
            container.add_item(media_gallery)

        view.add_item(container)
        await ctx.send(view=view)

    @commands.command(name="serverbanner")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    async def server_banner(self, ctx):
        if not ctx.guild.banner:
            view = self.create_response(
                "❌ No Banner",
                "This server doesn't have a banner.",
                ERROR_COLOR
            )
            await ctx.reply(view=view)
        else:
            webp = ctx.guild.banner.replace(format='webp')
            jpg = ctx.guild.banner.replace(format='jpg')
            png = ctx.guild.banner.replace(format='png')
            gif = ctx.guild.banner.replace(format='gif') if ctx.guild.banner.is_animated() else None

            links = f"[`PNG`]({png}) | [`JPG`]({jpg}) | [`WEBP`]({webp})"
            if gif:
                links += f" | [`GIF`]({gif})"

            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"## 🖼️ {ctx.guild.name}'s Banner"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"**Download Formats:**\n{links}"))
            container.add_item(Separator())
            media_gallery = MediaGallery()
            media_gallery.add_item(media=ctx.guild.banner.url)
            container.add_item(media_gallery)
            view.add_item(container)

            await ctx.reply(view=view)

    @commands.command(name="userbanner")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    async def user_banner(self, ctx, member: Optional[Union[discord.Member, discord.User]] = None):
        if member is None or member == "":
            member = ctx.author
        
        bannerUser = await self.bot.fetch_user(member.id)
        
        if not bannerUser.banner:
            view = self.create_response(
                "❌ No Banner",
                f"{member.name} doesn't have a banner.",
                ERROR_COLOR
            )
            await ctx.reply(view=view)
        else:
            webp = bannerUser.banner.replace(format='webp')
            jpg = bannerUser.banner.replace(format='jpg')
            png = bannerUser.banner.replace(format='png')
            gif = bannerUser.banner.replace(format='gif') if bannerUser.banner.is_animated() else None

            links = f"[`PNG`]({png}) | [`JPG`]({jpg}) | [`WEBP`]({webp})"
            if gif:
                links += f" | [`GIF`]({gif})"

            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"## 🖼️ {member.name}'s Banner"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"**Download Formats:**\n{links}"))
            container.add_item(Separator())
            media_gallery = MediaGallery()
            media_gallery.add_item(media=bannerUser.banner.url)
            container.add_item(media_gallery)
            view.add_item(container)

            await ctx.send(view=view)


async def setup(bot: Cryptora):
    await bot.add_cog(Helper(bot))
