import discord
from discord.ext import commands
from discord import ui
from discord.ui import LayoutView
from typing import Optional, Union
from datetime import datetime, timezone
from utils.LayoutHelpers import UserLayoutTemplates, ServerLayoutTemplates, BotLayoutTemplates, LayoutHelpers

color = 0x2f3136


class V2(commands.Cog):
    """Component V2 commands using new LayoutView system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.color = color
   
    @commands.command(
        usage="`avatar [member]`",
        name='avatar',
        aliases=['av', 'pfp'],
        help="Get user profile picture or avatar."
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def avatar(self, ctx, member: Optional[Union[discord.Member, discord.User]] = None):
        """Display user avatar using Component V2"""
        if member is None:
            member = ctx.author
        
        view = UserLayoutTemplates.avatar_view(member, self.bot)
        await ctx.reply(view=view)
    
    @commands.command(
        name="enlarge",
        usage="`enlarge <emoji>`",
        help="Enlarge an emoji"
    )
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def enlarge(self, ctx, emoji: Union[discord.Emoji, discord.PartialEmoji, str]):
        """Enlarge emoji using Component V2"""
        view = LayoutView()
        container = ui.Container()
        
        container.add_item(ui.TextDisplay("## Enlarge Emoji"))
        container.add_item(ui.Separator())
        
        # Media gallery
        gallery = ui.MediaGallery()
        gallery.add_item(media=emoji.url)
        container.add_item(gallery)
        
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# executed by {ctx.author.name}"))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.hybrid_command(
        name="users",
        help="Check how many users the bot is serving"
    )
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=False)
    async def users(self, ctx: commands.Context):
        """Show total users using Component V2"""
        total_users = sum(g.member_count for g in self.bot.guilds if g.member_count)
        
        view = LayoutView()
        container = ui.Container()
        
        container.add_item(ui.TextDisplay(f"## {self.bot.user.name} Users"))
        container.add_item(ui.Separator())
        
        thumb = ui.Thumbnail(self.bot.user.avatar.url)
        text = f"**{self.bot.user.name} Currently Serving `{total_users:,}` Active Users 💖**"
        section = ui.Section(ui.TextDisplay(text), accessory=thumb)
        container.add_item(section)
        
        container.add_item(ui.Separator())
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(
        name="servericon",
        help="Shows server icon"
    )
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.max_concurrency(1, per=commands.BucketType.guild, wait=False)
    async def servericon(self, ctx: commands.Context):
        """Show server icon using Component V2"""
        view = ServerLayoutTemplates.server_icon_view(ctx.guild)
        await ctx.reply(view=view)
    
    @commands.command(
        name="accountage",
        usage="`accage @user`",
        aliases=["accage"],
        help="Check account creation date"
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    async def accountage(self, ctx: commands.Context, member: discord.Member = None):
        """Show account age using Component V2"""
        member = member or ctx.author
        
        current_time = datetime.now(timezone.utc)
        account_creation = member.created_at
        delta = current_time - account_creation
        
        years = delta.days // 365
        months = (delta.days % 365) // 30
        weeks = (delta.days % 365 % 30) // 7
        days = (delta.days % 365 % 30) % 7
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        seconds = delta.seconds % 60
        
        age_str = (
            f"**{years}** years, **{months}** months, **{weeks}** weeks, "
            f"**{days}** days, **{hours}** hours, **{minutes}** mins, **{seconds}** secs"
        )
        timestamp = f"<t:{int(account_creation.timestamp())}:R> [<t:{int(account_creation.timestamp())}:F>]"
        
        view = LayoutView()
        container = ui.Container()
        
        container.add_item(ui.TextDisplay(f"## Account Age for {member.name}"))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"**Age:**\n{age_str}\n\n**Timestamp:**\n{timestamp}"))
        container.add_item(ui.Separator())
        
        view.add_item(container)
        await ctx.reply(view=view)


async def setup(bot):
    await bot.add_cog(V2(bot))