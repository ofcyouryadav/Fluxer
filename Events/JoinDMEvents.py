import discord
from discord.ext import commands
from discord import ui
from discord.ui import LayoutView, Container, Section, TextDisplay, Separator, Thumbnail
import logging

logger = logging.getLogger('bot')

COLOR = 0x2f3136

class JoinDMEvents(commands.Cog):
    """Event listener for welcome DMs"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Get MongoDB from bot instance
        self.joindm_collection = bot.db["join_dm"]
        
        logger.info("\x1b[38;5;197m[Cog]\x1b[0m JoinDMEvents cog initialized")
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Send welcome DM when a member joins"""
        if member.bot:
            return
        
        try:
            # Get join DM settings
            settings = await self.joindm_collection.find_one({
                "guild_id": member.guild.id
            })
            
            if not settings or not settings.get("enabled", False):
                return
            
            message = settings.get("message", "")
            if not message:
                return
            
            # Format message
            formatted_message = message.format(
                user=member.name,
                username=member.name,
                server=member.guild.name,
                membercount=member.guild.member_count
            )
            
            # Create welcome DM view
            view = LayoutView()
            container = Container()
            
            container.add_item(TextDisplay(f"## 👋 Welcome to {member.guild.name}!"))
            container.add_item(Separator())
            
            thumb = Thumbnail(member.guild.icon.url if member.guild.icon else member.display_avatar.url)
            section = Section(TextDisplay(formatted_message), accessory=thumb)
            container.add_item(section)
            
            container.add_item(Separator())
            container.add_item(TextDisplay(f"-# Have a great time in {member.guild.name}! 🎉"))
            
            view.add_item(container)
            
            # Try to send DM
            try:
                await member.send(view=view)
                logger.info(f"Sent welcome DM to {member} for {member.guild.name}")
            except discord.Forbidden:
                logger.warning(f"Cannot send DM to {member} - DMs are disabled")
            except Exception as e:
                logger.error(f"Error sending welcome DM: {e}")
                
        except Exception as e:
            logger.error(f"Error in on_member_join for welcome DM: {e}")


async def setup(bot):
    await bot.add_cog(JoinDMEvents(bot))
