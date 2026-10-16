import discord
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay, Separator
from typing import Optional
from discord.ext.commands import BucketType, cooldown

SUCCESS_COLOR = 0x00ff00
ERROR_COLOR = 0xff0000
INFO_COLOR = 0x3498db

class MediaChannel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 3.0, commands.BucketType.user)

    async def cog_check(self, ctx: commands.Context):
        bucket = self.cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(bucket, retry_after, commands.BucketType.user)
        return True

    @commands.group(name="mediachannel", aliases=["mediach"], invoke_without_command=True)
    @commands.has_permissions(manage_channels=True)
    async def mediachannel(self, ctx):
        """Manage media channels for sharing images, videos, and content"""
        if ctx.invoked_subcommand is None:
            view = LayoutView()
            container = Container()
            
            container.add_item(TextDisplay("## 📸 Media Channel Commands"))
            container.add_item(Separator())
            
            help_text = (
                "**Available Commands:**\n"
                "`mediachannel setup <name>` - Create a new media channel\n"
                "`mediachannel list` - List all media channels\n"
                "`mediachannel delete <channel>` - Delete a media channel\n"
                "`mediachannel configure <channel>` - Configure media channel settings\n\n"
                "**What are Media Channels?**\n"
                "Media channels are forum-style channels designed for sharing:\n"
                "• Images and photos\n"
                "• Videos and clips\n"
                "• Art and creative content\n"
                "• Memes and media"
            )
            
            container.add_item(TextDisplay(help_text))
            
            view.add_item(container)
            await ctx.reply(view=view)

    @mediachannel.command(name="setup")
    @commands.has_permissions(manage_channels=True)
    async def media_setup(self, ctx, name: str, category: Optional[discord.CategoryChannel] = None):
        """Create a new media/forum channel
        
        Usage: mediachannel setup <channel_name> [category]
        Example: mediachannel setup media-sharing"""
        
        try:
            # Create forum tags for media organization
            tags = [
                discord.ForumTag(name="Images", emoji="🖼️"),
                discord.ForumTag(name="Videos", emoji="🎥"),
                discord.ForumTag(name="Art", emoji="🎨"),
                discord.ForumTag(name="Memes", emoji="😂"),
                discord.ForumTag(name="Photography", emoji="📸")
            ]
            
            # Create the media channel (forum channel)
            media_channel = await ctx.guild.create_forum_channel(
                name=name,
                category=category or ctx.channel.category,
                topic="Share your images, videos, and media content here!",
                available_tags=tags,
                default_auto_archive_duration=1440,  # 24 hours
                slowmode_delay=5,  # 5 second cooldown to prevent spam
                reason=f"Media channel created by {ctx.author}"
            )
            
            view = LayoutView()
            container = Container()
            
            container.add_item(TextDisplay("## ✅ Media Channel Created"))
            container.add_item(Separator())
            
            info_text = (
                f"**Channel:** {media_channel.name}\n"
                f"**Category:** {media_channel.category.name if media_channel.category else 'None'}\n"
                f"**Slowmode:** 5 seconds\n"
                f"**Auto-archive:** 24 hours\n\n"
                f"**Available Tags:**\n"
                f"🖼️ Images • 🎥 Videos • 🎨 Art • 😂 Memes • 📸 Photography"
            )
            
            container.add_item(TextDisplay(info_text))
            container.add_item(Separator())
            container.add_item(TextDisplay("Users can now create posts with media in this channel!"))
            
            view.add_item(container)
            await ctx.reply(view=view)
            
        except discord.Forbidden:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ I don't have permission to create channels!"))
            container.add_item(Separator())
            container.add_item(TextDisplay("Please ensure I have the `Manage Channels` permission."))
            view.add_item(container)
            await ctx.reply(view=view)
            
        except Exception as e:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ Error creating media channel: {str(e)}"))
            view.add_item(container)
            await ctx.reply(view=view)

    @mediachannel.command(name="list")
    @commands.has_permissions(manage_channels=True)
    async def media_list(self, ctx):
        """List all forum/media channels in the server"""
        
        # Get all forum channels
        forum_channels = [ch for ch in ctx.guild.channels if isinstance(ch, discord.ForumChannel)]
        
        if not forum_channels:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## 📋 Media Channels"))
            container.add_item(Separator())
            container.add_item(TextDisplay("No media/forum channels found in this server."))
            container.add_item(Separator())
            container.add_item(TextDisplay("Use `mediachannel setup <name>` to create one!"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## 📋 Media Channels ({len(forum_channels)})"))
        container.add_item(Separator())
        
        channels_text = ""
        for i, channel in enumerate(forum_channels, 1):
            category_name = channel.category.name if channel.category else "No Category"
            tags_count = len(channel.available_tags) if channel.available_tags else 0
            channels_text += f"**{i}.** {channel.name} - *{category_name}* ({tags_count} tags)\n"
        
        container.add_item(TextDisplay(channels_text))
        container.add_item(Separator())
        
        view.add_item(container)
        await ctx.reply(view=view)

    @mediachannel.command(name="delete")
    @commands.has_permissions(manage_channels=True)
    async def media_delete(self, ctx, channel: discord.ForumChannel):
        """Delete a media/forum channel
        
        Usage: mediachannel delete #channel-name
        Example: mediachannel delete #media-sharing"""
        
        try:
            channel_name = channel.name
            channel_id = channel.id
            
            await channel.delete(reason=f"Media channel deleted by {ctx.author}")
            
            view = LayoutView()
            container = Container()
            
            container.add_item(TextDisplay("## ✅ Media Channel Deleted"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Successfully deleted **{channel_name}** (ID: {channel_id})"))
            
            view.add_item(container)
            await ctx.reply(view=view)
            
        except discord.Forbidden:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ I don't have permission to delete this channel!"))
            view.add_item(container)
            await ctx.reply(view=view)
            
        except Exception as e:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ Error deleting channel: {str(e)}"))
            view.add_item(container)
            await ctx.reply(view=view)

    @mediachannel.command(name="configure", aliases=["config"])
    @commands.has_permissions(manage_channels=True)
    async def media_configure(self, ctx, channel: discord.ForumChannel, setting: str, value: str):
        """Configure media channel settings
        
        Settings:
        - slowmode: Set slowmode delay (in seconds)
        - topic: Change channel topic/description
        - archive: Set auto-archive duration (60, 1440, 4320, 10080)
        
        Usage: mediachannel configure #channel slowmode 10
        Example: mediachannel configure #media topic New description here"""
        
        setting = setting.lower()
        
        try:
            if setting == "slowmode":
                delay = int(value)
                if delay < 0 or delay > 21600:
                    raise ValueError("Slowmode must be between 0 and 21600 seconds")
                
                await channel.edit(slowmode_delay=delay)
                message = f"Slowmode set to **{delay} seconds**"
                
            elif setting == "topic":
                await channel.edit(topic=value)
                message = f"Topic updated to: **{value}**"
                
            elif setting == "archive":
                duration = int(value)
                if duration not in [60, 1440, 4320, 10080]:
                    raise ValueError("Archive duration must be 60, 1440, 4320, or 10080 minutes")
                
                await channel.edit(default_auto_archive_duration=duration)
                hours = duration // 60
                message = f"Auto-archive duration set to **{hours} hours**"
                
            else:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("❌ Invalid setting. Choose: slowmode, topic, or archive"))
                view.add_item(container)
                return await ctx.reply(view=view)
            
            view = LayoutView()
            container = Container()
            
            container.add_item(TextDisplay("## ✅ Channel Configured"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"**Channel:** {channel.name}\n{message}"))
            
            view.add_item(container)
            await ctx.reply(view=view)
            
        except ValueError as e:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ Invalid value: {str(e)}"))
            view.add_item(container)
            await ctx.reply(view=view)
            
        except discord.Forbidden:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ I don't have permission to edit this channel!"))
            view.add_item(container)
            await ctx.reply(view=view)
            
        except Exception as e:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ Error: {str(e)}"))
            view.add_item(container)
            await ctx.reply(view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(MediaChannel(bot))
