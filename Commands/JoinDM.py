import discord
from discord.ext import commands
from discord import ui
from discord.ui import LayoutView, Container, Section, TextDisplay, Separator, ActionRow, Button, Thumbnail
from typing import Optional
import logging

logger = logging.getLogger('bot')

COLOR = 0x2f3136
SUCCESS_COLOR = 0x00ff88
ERROR_COLOR = 0xff0033

class JoinDM(commands.Cog):
    """Welcome DM system for new members"""
    
    def __init__(self, bot):
        self.bot = bot
        self.color = COLOR
        
        # Get MongoDB from bot instance
        self.joindm_collection = bot.db["join_dm"]
        
        logger.info("\x1b[38;5;197m[Cog]\x1b[0m JoinDM cog initialized")
    
    @commands.hybrid_command(name="setjoindm", aliases=["joindm"])
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def setjoindm(self, ctx, *, message: str):
        """Set the welcome DM message for new members (Admin only)
        
        Variables you can use:
        {user} - Mentions the user
        {username} - User's name
        {server} - Server name
        {membercount} - Total member count
        """
        if len(message) > 1000:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ **Message Too Long**\n\nThe message must be under 1000 characters!"))
            view.add_item(container)
            await ctx.reply(view=view)
            return
        
        # Save to database
        await self.joindm_collection.update_one(
            {"guild_id": ctx.guild.id},
            {"$set": {
                "message": message,
                "enabled": True
            }},
            upsert=True
        )
        
        # Preview the message
        preview = message.format(
            user=ctx.author.name,
            username=ctx.author.name,
            server=ctx.guild.name,
            membercount=ctx.guild.member_count
        )
        
        # Create success view
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## 📬 Join DM Set!"))
        container.add_item(Separator())
        
        desc = f"**Preview:**\n{preview}\n\n✅ New members will receive this DM when they join!"
        
        thumb = Thumbnail(ctx.guild.icon.url if ctx.guild.icon else ctx.author.display_avatar.url)
        section = Section(TextDisplay(desc), accessory=thumb)
        container.add_item(section)
        
        container.add_item(Separator())
        container.add_item(TextDisplay("-# Use `/togglejoindm` to enable/disable"))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.hybrid_command(name="togglejoindm")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def togglejoindm(self, ctx):
        """Toggle the join DM system on/off (Admin only)"""
        settings = await self.joindm_collection.find_one({"guild_id": ctx.guild.id})
        
        if not settings:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ **No Join DM Set**\n\nUse `/setjoindm` first to set up a welcome message!"))
            view.add_item(container)
            await ctx.reply(view=view)
            return
        
        new_status = not settings.get("enabled", False)
        
        await self.joindm_collection.update_one(
            {"guild_id": ctx.guild.id},
            {"$set": {"enabled": new_status}}
        )
        
        # Create view
        view = LayoutView()
        container = Container()
        
        status_text = "Enabled ✅" if new_status else "Disabled ❌"
        container.add_item(TextDisplay(f"## 📬 Join DM {status_text}"))
        container.add_item(Separator())
        
        if new_status:
            container.add_item(TextDisplay(f"New members will now receive a welcome DM!"))
        else:
            container.add_item(TextDisplay(f"New members will no longer receive a welcome DM."))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.hybrid_command(name="joindmstatus", aliases=["dmstatus"])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def joindmstatus(self, ctx):
        """View the current join DM settings"""
        settings = await self.joindm_collection.find_one({"guild_id": ctx.guild.id})
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## 📬 Join DM Settings - {ctx.guild.name}"))
        container.add_item(Separator())
        
        if not settings:
            container.add_item(TextDisplay("**Status:** Not configured\n\nUse `/setjoindm` to set up a welcome message!"))
        else:
            enabled = settings.get("enabled", False)
            message = settings.get("message", "No message set")
            
            # Preview
            preview = message.format(
                user=ctx.author.name,
                username=ctx.author.name,
                server=ctx.guild.name,
                membercount=ctx.guild.member_count
            )
            
            status_emoji = "✅" if enabled else "❌"
            desc = f"**Status:** {status_emoji} {'Enabled' if enabled else 'Disabled'}\n\n**Message Preview:**\n{preview}"
            
            container.add_item(TextDisplay(desc))
        
        container.add_item(Separator())
        
        view.add_item(container)
        await ctx.reply(view=view)


async def setup(bot):
    await bot.add_cog(JoinDM(bot))
