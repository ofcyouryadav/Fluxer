import discord
import aiohttp
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class WebhookLogger:
    """Centralized webhook logging for all bot events"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def set_session(self, session: aiohttp.ClientSession):
        """Set the aiohttp session for webhook requests"""
        self.session = session
    
    async def send_to_webhook(self, webhook_url: str, **kwargs):
        """Send an embed or content to a webhook"""
        if not webhook_url or not self.session:
            return
        
        try:
            webhook = discord.Webhook.from_url(webhook_url, session=self.session)
            await webhook.send(**kwargs)
        except Exception as e:
            logger.error(f"Failed to send webhook to {webhook_url}: {e}")
    
    async def log_command(self, ctx, command_name: str, success: bool = True, error: Optional[str] = None, webhook_url: Optional[str] = None):
        """Log command execution to webhook"""
        if not webhook_url:
            return
        
        color = discord.Color.green() if success else discord.Color.red()
        status = "Success" if success else "Failed"
        
        embed = discord.Embed(
            title=f"Command Executed - {status}",
            description=f"**Command:** `{command_name}`",
            color=color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="User", value=f"{ctx.author} ({ctx.author.id})", inline=False)
        embed.add_field(name="Guild", value=ctx.guild.name if ctx.guild else "DM", inline=False)
        embed.add_field(name="Channel", value=f"{ctx.channel}", inline=False)
        
        if error:
            embed.add_field(name="Error", value=f"```{error[:200]}```", inline=False)
        
        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        await self.send_to_webhook(webhook_url, embed=embed)
    
    async def log_guild_join(self, guild: discord.Guild, webhook_url: Optional[str] = None):
        """Log guild join event"""
        if not webhook_url:
            return
        
        embed = discord.Embed(
            title="Guild Joined",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Guild Name", value=guild.name, inline=False)
        embed.add_field(name="Guild ID", value=guild.id, inline=False)
        embed.add_field(name="Member Count", value=str(guild.member_count), inline=False)
        embed.add_field(name="Owner", value=f"{guild.owner} ({guild.owner_id})", inline=False)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        await self.send_to_webhook(webhook_url, embed=embed)
    
    async def log_guild_leave(self, guild: discord.Guild, webhook_url: Optional[str] = None):
        """Log guild leave event"""
        if not webhook_url:
            return
        
        embed = discord.Embed(
            title="Guild Left",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Guild Name", value=guild.name, inline=False)
        embed.add_field(name="Guild ID", value=guild.id, inline=False)
        embed.add_field(name="Member Count", value=str(guild.member_count), inline=False)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        await self.send_to_webhook(webhook_url, embed=embed)
    
    async def log_error(self, error: str, webhook_url: Optional[str] = None):
        """Log an error to webhook"""
        if not webhook_url:
            return
        
        embed = discord.Embed(
            title="Bot Error",
            description=f"```{error[:2000]}```",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        await self.send_to_webhook(webhook_url, embed=embed)

# Global instance
webhook_logger = WebhookLogger()
