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

class VCRoles(commands.Cog):
    """Voice channel role management system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.color = COLOR
        
        # Get MongoDB from bot instance
        self.vc_roles_collection = bot.db["vc_roles"]
        
        logger.info("\x1b[38;5;197m[Cog]\x1b[0m VCRoles cog initialized")
    
    @commands.hybrid_command(name="setvcrole", aliases=["vcrol"])
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def setvcrole(self, ctx, channel: discord.VoiceChannel, role: discord.Role):
        """Set a role to be given when users join a voice channel (Admin only)"""
        # Check bot permissions
        if role >= ctx.guild.me.top_role:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ **Permission Error**\n\nI cannot manage {role.name} as it's higher than my highest role!"))
            view.add_item(container)
            await ctx.reply(view=view)
            return
        
        # Save to database
        await self.vc_roles_collection.update_one(
            {"guild_id": ctx.guild.id, "channel_id": channel.id},
            {"$set": {
                "role_id": role.id,
                "role_name": role.name,
                "channel_name": channel.name
            }},
            upsert=True
        )
        
        # Create success view
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## 🎙️ VC Role Set!"))
        container.add_item(Separator())
        
        desc = f"**Voice Channel:** {channel.name}\n**Role:** {role.name}\n\n✅ Users will receive {role.name} when they join {channel.name}!"
        
        thumb = Thumbnail(ctx.guild.icon.url if ctx.guild.icon else ctx.author.display_avatar.url)
        section = Section(TextDisplay(desc), accessory=thumb)
        container.add_item(section)
        
        container.add_item(Separator())
        container.add_item(TextDisplay("-# The role will be removed when they leave the channel"))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.hybrid_command(name="removevcrole", aliases=["delvcrole"])
    @commands.has_permissions(manage_roles=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def removevcrole(self, ctx, channel: discord.VoiceChannel):
        """Remove the VC role for a specific voice channel (Admin only)"""
        result = await self.vc_roles_collection.delete_one({
            "guild_id": ctx.guild.id,
            "channel_id": channel.id
        })
        
        if result.deleted_count == 0:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ {channel.name} doesn't have a VC role set!"))
            view.add_item(container)
            await ctx.reply(view=view)
            return
        
        # Create success view
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## ✅ VC Role Removed"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"The VC role for {channel.name} has been removed."))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.hybrid_command(name="vcroles", aliases=["listv roles"])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def vcroles(self, ctx):
        """View all VC roles configured in this server"""
        vc_roles = await self.vc_roles_collection.find({"guild_id": ctx.guild.id}).to_list(None)
        
        if not vc_roles:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## 🎙️ No VC Roles\n\nNo VC roles have been set up yet!\n\nAdmins can use `/setvcrole` to add VC roles."))
            view.add_item(container)
            await ctx.reply(view=view)
            return
        
        # Create view
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## 🎙️ VC Roles - {ctx.guild.name}"))
        container.add_item(Separator())
        
        vc_list = []
        for vc_role in vc_roles:
            channel = ctx.guild.get_channel(vc_role["channel_id"])
            role = ctx.guild.get_role(vc_role["role_id"])
            
            if channel and role:
                vc_list.append(f"{channel.name} ➜ {role.name}")
            elif channel:
                vc_list.append(f"{channel.name} ➜ *Role Deleted*")
            else:
                vc_list.append(f"*Channel Deleted* ➜ {role.name if role else '*Role Deleted*'}")
        
        if vc_list:
            container.add_item(TextDisplay("\n".join(vc_list)))
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Total: {len(vc_roles)} VC roles"))
        
        view.add_item(container)
        await ctx.reply(view=view)


async def setup(bot):
    await bot.add_cog(VCRoles(bot))
