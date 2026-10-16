import discord
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay, Separator, MediaGallery
from typing import Optional
from discord.ext.commands import BucketType, cooldown
import db.boost as boost_db

SUCCESS_COLOR = 0x00ff00
ERROR_COLOR = 0xff0000
INFO_COLOR = 0x3498db

class Boost(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 3.0, commands.BucketType.user)
    
    async def cog_load(self):
        await boost_db.initialize_db()

    async def cog_check(self, ctx: commands.Context):
        bucket = self.cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(bucket, retry_after, commands.BucketType.user)
        return True

    @commands.group(name="boost", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def boost(self, ctx):
        """Configure boost notifications for your server"""
        if ctx.invoked_subcommand is None:
            view = LayoutView()
            container = Container()
            
            container.add_item(TextDisplay("## 🚀 Boost Notifier Commands"))
            container.add_item(Separator())
            
            help_text = (
                "**Available Commands:**\n"
                "`boost setup #channel` - Set up boost notifications\n"
                "`boost message <text>` - Set custom boost message\n"
                "`boost embed <field> <value>` - Configure embed\n"
                "`boost config` - View current configuration\n"
                "`boost test` - Test the boost notification\n"
                "`boost toggle` - Enable/disable boost notifications\n"
                "`boost disable` - Disable boost notifications\n\n"
                "**Available Variables:**\n"
                "`{user}` - Mention the booster\n"
                "`{username}` - Booster's username\n"
                "`{server}` - Server name\n"
                "`{boostcount}` - Current boost count\n"
                "`{boostlevel}` - Current boost level"
            )
            
            container.add_item(TextDisplay(help_text))
            
            view.add_item(container)
            await ctx.reply(view=view)

    @boost.command(name="setup")
    @commands.has_permissions(manage_guild=True)
    async def boost_setup(self, ctx, channel: discord.TextChannel):
        """Set up boost notifications in a specific channel"""
        
        existing_config = await boost_db.get_config(ctx.guild.id)
        
        if existing_config:
            await boost_db.update_channel(ctx.guild.id, channel.id)
            message = f"Boost notifications channel updated to {channel.name}"
        else:
            await boost_db.create_config(ctx.guild.id, channel.id)
            message = f"Boost notifications set up in {channel.name}"
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## ✅ Boost Setup Complete"))
        container.add_item(Separator())
        container.add_item(TextDisplay(message))
        container.add_item(Separator())
        container.add_item(TextDisplay("Use `boost test` to preview your notification!"))
        
        view.add_item(container)
        await ctx.reply(view=view)

    @boost.command(name="message")
    @commands.has_permissions(manage_guild=True)
    async def boost_message(self, ctx, *, message: str):
        """Set a custom boost notification message
        
        Available variables: {user}, {username}, {server}, {boostcount}, {boostlevel}
        
        Usage: boost message 🚀 {user} just boosted {server}! We're at {boostcount} boosts!"""
        
        config = await boost_db.get_config(ctx.guild.id)
        
        if not config:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Please set up boost notifications first using `boost setup #channel`"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        await boost_db.update_message(ctx.guild.id, message)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## ✅ Message Updated"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"**New Message:**\n{message}"))
        container.add_item(Separator())
        container.add_item(TextDisplay("Use `boost test` to preview!"))
        
        view.add_item(container)
        await ctx.reply(view=view)

    @boost.command(name="embed")
    @commands.has_permissions(manage_guild=True)
    async def boost_embed(self, ctx, field: str, *, value: str = None):
        """Configure the boost notification embed
        
        Fields:
        - title: Set embed title
        - description: Set embed description
        - color: Set embed color (hex code)
        - thumbnail: user_avatar, server_icon, or none
        - image: URL or none
        - footer: Set footer text
        - toggle: Enable/disable embed (on/off)
        
        Usage: boost embed title 🚀 New Boost!
        Usage: boost embed color #ff69b4
        Usage: boost embed toggle off"""
        
        config = await boost_db.get_config(ctx.guild.id)
        
        if not config:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Please set up boost notifications first using `boost setup #channel`"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        field = field.lower()
        
        if field == "title":
            await boost_db.update_embed_field(ctx.guild.id, "embed_title", value)
            message = f"Embed title set to: **{value}**"
        
        elif field == "description":
            await boost_db.update_embed_field(ctx.guild.id, "embed_description", value)
            message = f"Embed description updated"
        
        elif field == "color":
            if value.startswith("#"):
                value = value[1:]
            try:
                color = int(value, 16)
                await boost_db.update_embed_field(ctx.guild.id, "embed_color", color)
                message = f"Embed color set to: #{value}"
            except ValueError:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("❌ Invalid color hex code. Use format: #00ff00"))
                view.add_item(container)
                return await ctx.reply(view=view)
        
        elif field == "thumbnail":
            if value.lower() in ["user_avatar", "server_icon", "none"]:
                await boost_db.update_embed_field(ctx.guild.id, "embed_thumbnail", value.lower())
                message = f"Thumbnail set to: **{value.lower()}**"
            else:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("❌ Invalid option. Choose: user_avatar, server_icon, or none"))
                view.add_item(container)
                return await ctx.reply(view=view)
        
        elif field == "image":
            if value and value.lower() == "none":
                value = None
            
            await boost_db.update_embed_field(ctx.guild.id, "embed_image", value)
            message = f"Image {'removed' if not value else 'set'}"
        
        elif field == "footer":
            await boost_db.update_embed_field(ctx.guild.id, "embed_footer", value)
            message = f"Footer set to: **{value}**"
        
        elif field == "toggle":
            if value.lower() in ["on", "off"]:
                enabled = 1 if value.lower() == "on" else 0
                await boost_db.update_embed_field(ctx.guild.id, "embed_enabled", enabled)
                message = f"Embed mode {'enabled' if enabled else 'disabled'}"
            else:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("❌ Use 'on' or 'off'"))
                view.add_item(container)
                return await ctx.reply(view=view)
        else:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Invalid field. Choose: title, description, color, thumbnail, image, footer, toggle"))
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

    @boost.command(name="config")
    @commands.has_permissions(manage_guild=True)
    async def boost_config(self, ctx):
        """View current boost notification configuration"""
        
        config = await boost_db.get_config(ctx.guild.id)
        
        if not config:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Boost notifications not configured. Use `boost setup #channel` to get started."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        channel = ctx.guild.get_channel(config.get("channel_id"))
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## 📋 Boost Notification Configuration"))
        container.add_item(Separator())
        
        config_text = (
            f"**Channel:** {channel.name if channel else 'Not Set'}\n"
            f"**Status:** {'✅ Enabled' if config.get('enabled', 1) else '❌ Disabled'}\n"
            f"**Embed Mode:** {'✅ Enabled' if config.get('embed_enabled', 1) else '❌ Disabled'}\n\n"
        )
        
        if config.get('embed_enabled', 1):
            config_text += (
                f"**Embed Title:** {config.get('embed_title', '🚀 Server Boosted!')}\n"
                f"**Embed Color:** #{config.get('embed_color', 0xff69b4):06x}\n"
                f"**Thumbnail:** {config.get('embed_thumbnail', 'user_avatar')}\n"
                f"**Footer:** {config.get('embed_footer', 'Boost #{boostcount}')}\n"
            )
        else:
            config_text += f"**Message:** {config.get('message', 'Not set')}\n"
        
        container.add_item(TextDisplay(config_text))
        container.add_item(Separator())
        
        view.add_item(container)
        await ctx.reply(view=view)

    @boost.command(name="test")
    @commands.has_permissions(manage_guild=True)
    async def boost_test(self, ctx):
        """Test your boost notification setup"""
        
        config = await boost_db.get_config(ctx.guild.id)
        
        if not config:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Boost notifications not configured. Use `boost setup #channel` to get started."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        channel = ctx.guild.get_channel(config.get("channel_id"))
        
        if not channel:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Notification channel not found. Please run `boost setup #channel` again."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        await self._send_boost_notification(ctx.author, ctx.guild, test=True, test_channel=channel)
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"✅ Test notification sent to {channel.name}"))
        view.add_item(container)
        await ctx.reply(view=view, ephemeral=True)

    @boost.command(name="toggle")
    @commands.has_permissions(manage_guild=True)
    async def boost_toggle(self, ctx):
        """Toggle boost notifications on/off"""
        
        config = await boost_db.get_config(ctx.guild.id)
        
        if not config:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Boost notifications not configured. Use `boost setup #channel` to get started."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        new_status = not config.get("enabled", 1)
        
        await boost_db.toggle_enabled(ctx.guild.id, new_status)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## {'✅ Enabled' if new_status else '❌ Disabled'}"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"Boost notifications are now **{'enabled' if new_status else 'disabled'}**."))
        
        view.add_item(container)
        await ctx.reply(view=view)

    @boost.command(name="disable")
    @commands.has_permissions(manage_guild=True)
    async def boost_disable(self, ctx):
        """Disable boost notifications"""
        
        config = await boost_db.get_config(ctx.guild.id)
        
        if not config:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Boost notifications are not set up."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        await boost_db.delete_config(ctx.guild.id)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## ✅ Boost Notifications Disabled"))
        container.add_item(Separator())
        container.add_item(TextDisplay("All boost notification settings have been removed."))
        
        view.add_item(container)
        await ctx.reply(view=view)

    async def _send_boost_notification(self, member: discord.Member, guild: discord.Guild, test: bool = False, test_channel: discord.TextChannel = None):
        """Internal method to send boost notification"""
        config = await boost_db.get_config(guild.id)
        
        if not config or not config.get("enabled", 1):
            return
        
        if test:
            channel = test_channel
        else:
            channel = guild.get_channel(config.get("channel_id"))
        
        if not channel:
            return
        
        message_text = config.get("message") or "🚀 {user} just boosted **{server}**! Thank you for your support! 💎"
        embed_title = config.get("embed_title") or "🚀 Server Boosted!"
        embed_description = config.get("embed_description") or "Thank you {user} for boosting **{server}**! 💎\n\nWe now have **{boostcount}** boosts at level **{boostlevel}**!"
        embed_footer = config.get("embed_footer") or "Boost #{boostcount}"
        
        replacements = {
            "{user}": member.name,
            "{username}": member.name,
            "{server}": guild.name,
            "{boostcount}": str(guild.premium_subscription_count),
            "{boostlevel}": str(guild.premium_tier)
        }
        
        if message_text:
            for old, new in replacements.items():
                message_text = message_text.replace(old, new)
        if embed_title:
            for old, new in replacements.items():
                embed_title = embed_title.replace(old, new)
        if embed_description:
            for old, new in replacements.items():
                embed_description = embed_description.replace(old, new)
        if embed_footer:
            for old, new in replacements.items():
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
            elif thumbnail == "server_icon" and guild.icon:
                container.add_item(Separator())
                gallery = MediaGallery()
                gallery.add_item(media=guild.icon.url)
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
                await channel.send("**🧪 Test Boost Notification:**")
            await channel.send(view=view)
        else:
            message_text = message_text or "🚀 {user} just boosted **{server}**!"
            if test:
                await channel.send(f"**🧪 Test Boost Notification:**\n{message_text}")
            else:
                await channel.send(message_text)

async def setup(bot: commands.Bot):
    await bot.add_cog(Boost(bot))
