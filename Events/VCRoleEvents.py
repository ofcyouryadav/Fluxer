import discord
from discord.ext import commands
import logging

logger = logging.getLogger('bot')

class VCRoleEvents(commands.Cog):
    """Event listener for VC role management"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Get MongoDB from bot instance
        self.vc_roles_collection = bot.db["vc_roles"]
        
        logger.info("\x1b[38;5;197m[Cog]\x1b[0m VCRoleEvents cog initialized")
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Handle voice channel joins/leaves"""
        if member.bot:
            return
        
        # User joined a voice channel
        if after.channel and before.channel != after.channel:
            await self.handle_vc_join(member, after.channel)
        
        # User left a voice channel
        if before.channel and before.channel != after.channel:
            await self.handle_vc_leave(member, before.channel)
    
    async def handle_vc_join(self, member: discord.Member, channel: discord.VoiceChannel):
        """Give role when user joins VC"""
        try:
            # Check if this channel has a VC role
            vc_role_data = await self.vc_roles_collection.find_one({
                "guild_id": member.guild.id,
                "channel_id": channel.id
            })
            
            if not vc_role_data:
                return
            
            role = member.guild.get_role(vc_role_data["role_id"])
            if not role:
                # Role was deleted, remove from database
                await self.vc_roles_collection.delete_one({
                    "guild_id": member.guild.id,
                    "channel_id": channel.id
                })
                return
            
            # Give role if member doesn't have it
            if role not in member.roles:
                try:
                    await member.add_roles(role, reason=f"Joined VC: {channel.name}")
                    # logger.info(f"Gave {role.name} to {member} for joining {channel.name}")  # Commented out to reduce spam
                except discord.Forbidden:
                    logger.warning(f"Cannot give role {role.name} to {member} - missing permissions")
                except Exception as e:
                    logger.error(f"Error giving VC role: {e}")
                    
        except Exception as e:
            logger.error(f"Error in handle_vc_join: {e}")
    
    async def handle_vc_leave(self, member: discord.Member, channel: discord.VoiceChannel):
        """Remove role when user leaves VC"""
        try:
            # Check if this channel has a VC role
            vc_role_data = await self.vc_roles_collection.find_one({
                "guild_id": member.guild.id,
                "channel_id": channel.id
            })
            
            if not vc_role_data:
                return
            
            role = member.guild.get_role(vc_role_data["role_id"])
            if not role:
                return
            
            # Remove role if member has it
            if role in member.roles:
                try:
                    await member.remove_roles(role, reason=f"Left VC: {channel.name}")
                    # logger.info(f"Removed {role.name} from {member} for leaving {channel.name}")  # Commented out to reduce spam
                except discord.Forbidden:
                    logger.warning(f"Cannot remove role {role.name} from {member} - missing permissions")
                except Exception as e:
                    logger.error(f"Error removing VC role: {e}")
                    
        except Exception as e:
            logger.error(f"Error in handle_vc_leave: {e}")


async def setup(bot):
    await bot.add_cog(VCRoleEvents(bot))
