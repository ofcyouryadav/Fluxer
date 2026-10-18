import discord
from discord.ext import commands
import logging
from Database.repositories import PrefixRepository, PlaylistRepository#, IgnoreRepository
from Database.utils import cache_manager, db_metrics
from typing import Optional

logger = logging.getLogger(__name__)

class GuildEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.prefix_repo = PrefixRepository()
        self.playlist_repo = PlaylistRepository()
      #  self.ignore_repo = IgnoreRepository()
        logger.info("\x1b[38;5;197m[Cog]\x1b[0m GuildEvents cog initialized")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Handle new guild join with proper database initialization"""
        try:
            logger.info(f"\x1b[38;5;197m[Guild Join]\x1b[0m Bot joined guild: {guild.name} (ID: {guild.id})")

            # Set default prefix
            success = await self.prefix_repo.set_prefix(guild.id, "+")
            if not success:
                logger.error(f"\x1b[38;5;197m[Error]\x1b[0m Failed to set default prefix for guild {guild.id}")
                return

            # Clear any existing cache entries for this guild
            cache_key = f"prefix:{guild.id}"
            await cache_manager.delete('prefix', cache_key)

            # Log metrics
            await db_metrics.record_operation("guild_join", 0.0, True)

            # Send welcome message if possible
            welcome_channel = self._get_welcome_channel(guild)
            if welcome_channel:
                from discord.ui import LayoutView, Container, Section, TextDisplay, Separator, Thumbnail, ActionRow, Button
                from discord import ButtonStyle
                
                view = LayoutView()
                container = Container()
                
                # Thanks message with bot icon
                thumb = Thumbnail(self.bot.user.avatar.url)
                welcome_text = f"## Thanks for adding me!\n\n"
                welcome_text += f"• Use `/help` to see all commands\n"
                welcome_text += f"• Default prefix is `+`\n"
                welcome_text += f"• Use `+setprefix` to change prefix"
                
                section = Section(TextDisplay(welcome_text), accessory=thumb)
                container.add_item(section)
                
                container.add_item(Separator())
                
                # Add invite/support buttons
                buttons = ActionRow()
                buttons.add_item(Button(
                    label="Support Server",
                    url="https://discord.gg/support",
                    style=ButtonStyle.link
                ))
                buttons.add_item(Button(
                    label="Invite Bot",
                    url=f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot%20applications.commands",
                    style=ButtonStyle.link
                ))
                container.add_item(buttons)
                
                view.add_item(container)
                
                try:
                    await welcome_channel.send(view=view)
                except discord.Forbidden:
                    logger.warning(f"\x1b[38;5;197m[Warning]\x1b[0m Cannot send welcome message in guild {guild.id}")

        except Exception as e:
            logger.error(f"\x1b[38;5;197m[Error]\x1b[0m Error handling guild join for {guild.id}: {e}")
            await db_metrics.record_operation("guild_join", 0.0, False)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """Clean up database entries when bot leaves a guild"""
        try:
            logger.info(f"\x1b[38;5;197m[Guild Leave]\x1b[0m Bot left guild: {guild.name} (ID: {guild.id})")

            # Clean up database entries with retries and proper error handling
            tasks = [
                ("prefix", self.prefix_repo.delete_prefix(guild.id))
            ]

            for task_name, task_coro in tasks:
                try:
                    await task_coro
                except Exception as e:
                    logger.error(f"\x1b[38;5;197m[Error]\x1b[0m Failed to delete {task_name} data for guild {guild.id}: {e}")

            # Clear cache entries
            await cache_manager.delete('prefix', f"prefix:{guild.id}")

            # Log metrics
            await db_metrics.record_operation("guild_remove", 0.0, True)

        except Exception as e:
            logger.error(f"\x1b[38;5;197m[Error]\x1b[0m Error handling guild remove for {guild.id}: {e}")
            await db_metrics.record_operation("guild_remove", 0.0, False)

    async def _safe_delete(self, name: str, coro) -> None:
        """Safely execute a delete operation with error handling"""
        try:
            await coro
            logger.debug(f"\x1b[38;5;197m[Delete]\x1b[0m Successfully deleted {name} data")
        except Exception as e:
            logger.error(f"\x1b[38;5;197m[Error]\x1b[0m Error deleting {name} data: {e}")
            raise

    def _get_welcome_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        """Find the best channel to send welcome message"""
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            return guild.system_channel

        # Look for a general channel
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                if 'general' in channel.name.lower():
                    return channel

        # Fall back to first available channel
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                return channel

        return None

async def setup(bot):
    await bot.add_cog(GuildEvents(bot))