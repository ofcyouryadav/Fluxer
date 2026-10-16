import discord
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay, Separator, MediaGallery
from typing import Optional
import db.greet as greet_db

SUCCESS_COLOR = 0x00ff00
ERROR_COLOR = 0xff0000
INFO_COLOR = 0x3498db

class Greet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_load(self):
        await greet_db.initialize_db()
    
    @commands.group(name="greet", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def greet(self, ctx):
        """Configure welcome messages for new members"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
    
    @greet.command(name="setup")
    @commands.has_permissions(manage_guild=True)
    async def greet_setup(self, ctx, channel: discord.TextChannel):
        """Set up the welcome channel for greeting new members
        
        Usage: greet setup #channel"""
        
        existing = await greet_db.get_config(ctx.guild.id)
        
        if existing:
            await greet_db.update_channel(ctx.guild.id, channel.id)
        else:
            await greet_db.create_config(ctx.guild.id, channel.id)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## ✅ Greet Setup Complete"))
        container.add_item(Separator())
        container.add_item(TextDisplay(
            f"**Channel:** {channel.name}\n"
            f"**Status:** Enabled\n\n"
            f"New members will be greeted in {channel.name}!\n\n"
            f"**Next Steps:**\n"
            f"• Use `greet message` to customize the welcome message\n"
            f"• Use `greet embed` to customize the embed\n"
            f"• Use `greet test` to preview the welcome message"
        ))
        container.add_item(Separator())
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @greet.command(name="message")
    @commands.has_permissions(manage_guild=True)
    async def greet_message(self, ctx, *, message: str):
        """Set a custom welcome message
        
        Variables:
        {user} - Mentions the user
        {username} - User's name
        {server} - Server name
        {membercount} - Total member count
        
        Usage: greet message Welcome {user} to {server}!"""
        
        config = await greet_db.get_config(ctx.guild.id)
        
        if not config:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Please set up greet first using `greet setup #channel`"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        await greet_db.update_message(ctx.guild.id, message)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## ✅ Welcome Message Updated"))
        container.add_item(Separator())
        container.add_item(TextDisplay(
            f"**New Message:**\n{message}\n\n"
            f"**Available Variables:**\n"
            f"`{{user}}` - Mentions the user\n"
            f"`{{username}}` - User's name\n"
            f"`{{server}}` - Server name\n"
            f"`{{membercount}}` - Total member count"
        ))
        container.add_item(Separator())
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @greet.command(name="embed")
    @commands.has_permissions(manage_guild=True)
    async def greet_embed(self, ctx, field: str, *, value: str = None):
        """Configure the welcome embed
        
        Fields:
        - title: Set embed title
        - description: Set embed description
        - color: Set embed color (hex code)
        - thumbnail: user_avatar, server_icon, or none
        - image: URL or none
        - footer: Set footer text
        - toggle: Enable/disable embed (on/off)
        
        Usage: greet embed title Welcome to {server}!
        Usage: greet embed color #00ff00
        Usage: greet embed toggle off"""
        
        config = await greet_db.get_config(ctx.guild.id)
        
        if not config:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Please set up greet first using `greet setup #channel`"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        field = field.lower()
        
        if field == "title":
            await greet_db.update_embed_field(ctx.guild.id, "embed_title", value)
            message = f"Embed title set to: **{value}**"
        
        elif field == "description":
            await greet_db.update_embed_field(ctx.guild.id, "embed_description", value)
            message = f"Embed description updated"
        
        elif field == "color":
            if value.startswith("#"):
                value = value[1:]
            try:
                color = int(value, 16)
                await greet_db.update_embed_field(ctx.guild.id, "embed_color", color)
                message = f"Embed color set to: #{value}"
            except ValueError:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("❌ Invalid color hex code. Use format: #00ff00"))
                view.add_item(container)
                return await ctx.reply(view=view)
        
        elif field == "thumbnail":
            if value.lower() in ["user_avatar", "server_icon", "none"]:
                await greet_db.update_embed_field(ctx.guild.id, "embed_thumbnail", value.lower())
                message = f"Embed thumbnail set to: **{value}**"
            else:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("❌ Thumbnail must be: user_avatar, server_icon, or none"))
                view.add_item(container)
                return await ctx.reply(view=view)
        
        elif field == "image":
            if value and value.lower() == "none":
                value = None
            await greet_db.update_embed_field(ctx.guild.id, "embed_image", value)
            message = f"Embed image {'removed' if value is None else 'set'}"
        
        elif field == "footer":
            await greet_db.update_embed_field(ctx.guild.id, "embed_footer", value)
            message = f"Embed footer set to: **{value}**"
        
        elif field == "toggle":
            if value.lower() in ["on", "enable", "true"]:
                await greet_db.update_embed_field(ctx.guild.id, "embed_enabled", 1)
                message = "Embed mode **enabled**"
            elif value.lower() in ["off", "disable", "false"]:
                await greet_db.update_embed_field(ctx.guild.id, "embed_enabled", 0)
                message = "Embed mode **disabled**"
            else:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("❌ Toggle value must be: on or off"))
                view.add_item(container)
                return await ctx.reply(view=view)
        
        else:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(
                "❌ Invalid field. Available fields:\n"
                "`title`, `description`, `color`, `thumbnail`, `image`, `footer`, `toggle`"
            ))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## ✅ Embed Configuration Updated"))
        container.add_item(Separator())
        container.add_item(TextDisplay(message))
        container.add_item(Separator())
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @greet.command(name="config")
    @commands.has_permissions(manage_guild=True)
    async def greet_config(self, ctx):
        """View current greet configuration"""
        
        config = await greet_db.get_config(ctx.guild.id)
        
        if not config:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Greet is not configured. Use `greet setup #channel` to get started."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        channel = ctx.guild.get_channel(config.get("channel_id"))
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## 📋 Greet Configuration"))
        container.add_item(Separator())
        
        config_text = (
            f"**Channel:** {channel.name if channel else 'Not Set'}\n"
            f"**Status:** {'✅ Enabled' if config.get('enabled', 1) else '❌ Disabled'}\n"
            f"**Embed Mode:** {'✅ Enabled' if config.get('embed_enabled', 1) else '❌ Disabled'}\n\n"
        )
        
        if config.get('embed_enabled', 1):
            config_text += (
                f"**Embed Title:** {config.get('embed_title', 'Welcome!')}\n"
                f"**Embed Color:** #{config.get('embed_color', SUCCESS_COLOR):06x}\n"
                f"**Thumbnail:** {config.get('embed_thumbnail', 'user_avatar')}\n"
                f"**Footer:** {config.get('embed_footer', 'Member #{membercount}')}\n"
            )
        else:
            config_text += f"**Message:** {config.get('message', 'Not set')}\n"
        
        container.add_item(TextDisplay(config_text))
        container.add_item(Separator())
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @greet.command(name="test")
    @commands.has_permissions(manage_guild=True)
    async def greet_test(self, ctx):
        """Test the welcome message"""
        
        config = await greet_db.get_config(ctx.guild.id)
        
        if not config:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Greet is not configured. Use `greet setup #channel` to get started."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        await self._send_welcome(ctx.author, test=True, test_channel=ctx.channel)
    
    @greet.command(name="toggle")
    @commands.has_permissions(manage_guild=True)
    async def greet_toggle(self, ctx):
        """Enable or disable the greet system"""
        
        config = await greet_db.get_config(ctx.guild.id)
        
        if not config:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Greet is not configured. Use `greet setup #channel` to get started."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        new_status = not config.get("enabled", 1)
        
        await greet_db.toggle_enabled(ctx.guild.id, new_status)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## {'✅ Greet Enabled' if new_status else '❌ Greet Disabled'}"))
        container.add_item(Separator())
        container.add_item(TextDisplay(
            f"Welcome messages are now **{'enabled' if new_status else 'disabled'}**."
        ))
        container.add_item(Separator())
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @greet.command(name="disable")
    @commands.has_permissions(manage_guild=True)
    async def greet_disable(self, ctx):
        """Completely remove greet configuration"""
        
        config = await greet_db.get_config(ctx.guild.id)
        
        if not config:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Greet is not configured."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        await greet_db.delete_config(ctx.guild.id)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## ✅ Greet Disabled"))
        container.add_item(Separator())
        container.add_item(TextDisplay("Greet configuration has been removed from this server."))
        container.add_item(Separator())
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    async def _send_welcome(self, member: discord.Member, test: bool = False, test_channel: discord.TextChannel = None):
        """Internal method to send welcome message"""
        config = await greet_db.get_config(member.guild.id)
        
        if not config or not config.get("enabled", 1):
            return
        
        if test:
            channel = test_channel
        else:
            channel = member.guild.get_channel(config.get("channel_id"))
        
        if not channel:
            return
        
        message_text = config.get("message") or "Welcome {user} to **{server}**!"
        embed_title = config.get("embed_title") or "Welcome!"
        embed_description = config.get("embed_description") or "Welcome {user} to **{server}**! 🎉"
        embed_footer = config.get("embed_footer") or "Member #{membercount}"
        
        replacements = {
            "{user}": member.name,
            "{username}": member.name,
            "{server}": member.guild.name,
            "{membercount}": str(member.guild.member_count)
        }
        
        for old, new in replacements.items():
            message_text = message_text.replace(old, new)
            embed_title = embed_title.replace(old, new)
            embed_description = embed_description.replace(old, new)
            embed_footer = embed_footer.replace(old, new)
        
        if config.get("embed_enabled", 1):
            view = LayoutView()
            container = Container()
            
            container.add_item(TextDisplay(f"## {embed_title}"))
            container.add_item(Separator())
            container.add_item(TextDisplay(embed_description))
            
            thumbnail = config.get("embed_thumbnail", "user_avatar")
            if thumbnail == "user_avatar" and member.avatar:
                container.add_item(Separator())
                gallery = MediaGallery()
                gallery.add_item(media=member.avatar.url)
                container.add_item(gallery)
            elif thumbnail == "server_icon" and member.guild.icon:
                container.add_item(Separator())
                gallery = MediaGallery()
                gallery.add_item(media=member.guild.icon.url)
                container.add_item(gallery)
            
            embed_image = config.get("embed_image")
            if embed_image:
                container.add_item(Separator())
                gallery = MediaGallery()
                gallery.add_item(media=embed_image)
                container.add_item(gallery)
            
            container.add_item(Separator())
            container.add_item(TextDisplay(f"*{embed_footer}*"))
            
            view.add_item(container)
            
            if test:
                await channel.send("**🧪 Test Welcome Message:**")
            await channel.send(view=view)
        else:
            message_text = message_text or "Welcome {user} to **{server}**!"
            if test:
                await channel.send(f"**🧪 Test Welcome Message:**\n{message_text}")
            else:
                await channel.send(message_text)

async def setup(bot):
    await bot.add_cog(Greet(bot))
