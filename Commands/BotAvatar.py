import discord
from discord.ext import commands
import base64
import requests
import os
from utils.Tools import blacklist_check, ignore_check
from Config.Config import OWNER_IDS

class BotAvatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x7AAAFF

    def _get_bot_token(self):
        """Get bot token from environment variables"""
        return os.getenv("DISCORD_BOT_TOKEN")

    def _create_response_embed(self, title: str, success: bool, message: str) -> discord.Embed:
        """Create a standardized response embed"""
        color = self.color if success else 0xFF0000
        embed = discord.Embed(
            title=title,
            description=message,
            color=discord.Colour(color)
        )
        return embed

    async def _set_guild_avatar(self, guild_id: int, image_url: str) -> tuple[bool, str]:
        """Set bot avatar for a guild"""
        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code != 200:
                return False, "❌ Unable to fetch image. Please provide a valid URL."
            
            image_data = response.content
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            
            data = {'avatar': f"data:image/png;base64,{encoded_image}"}
            token = self._get_bot_token()
            headers = {'Authorization': f'Bot {token}'}
            url = f'https://discord.com/api/v10/guilds/{guild_id}/members/@me'
            
            response = requests.patch(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return True, "✅ Successfully updated bot avatar for this server!"
            else:
                error_text = response.text if hasattr(response, 'text') else str(response.status_code)
                return False, f"❌ Failed to update avatar (Status: {response.status_code})\n**Error:** {error_text[:100]}"
        except requests.exceptions.RequestException as e:
            return False, f"❌ Error fetching image: {str(e)[:100]}"
        except Exception as e:
            return False, f"❌ Unexpected error: {str(e)[:100]}"

    async def _set_guild_banner(self, guild_id: int, image_url: str) -> tuple[bool, str]:
        """Set bot banner for a guild"""
        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code != 200:
                return False, "❌ Unable to fetch image. Please provide a valid URL."
            
            image_data = response.content
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            
            data = {'banner': f"data:image/png;base64,{encoded_image}"}
            token = self._get_bot_token()
            headers = {'Authorization': f'Bot {token}'}
            url = f'https://discord.com/api/v10/guilds/{guild_id}/members/@me'
            
            response = requests.patch(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return True, "✅ Successfully updated bot banner for this server!"
            else:
                error_text = response.text if hasattr(response, 'text') else str(response.status_code)
                return False, f"❌ Failed to update banner (Status: {response.status_code})\n**Error:** {error_text[:100]}"
        except requests.exceptions.RequestException as e:
            return False, f"❌ Error fetching image: {str(e)[:100]}"
        except Exception as e:
            return False, f"❌ Unexpected error: {str(e)[:100]}"

    async def _reset_to_default(self, guild_id: int, avatar: bool = True) -> tuple[bool, str]:
        """Reset avatar/banner to default"""
        try:
            image_type = "avatar" if avatar else "banner"
            image_path = f"data/default{image_type}.png"
            
            if not os.path.exists(image_path):
                return False, f"❌ Default {image_type} image not found on server."
            
            with open(image_path, 'rb') as f:
                image_data = f.read()
                encoded_image = base64.b64encode(image_data).decode('utf-8')
            
            data = {image_type: f"data:image/png;base64,{encoded_image}"}
            token = self._get_bot_token()
            headers = {'Authorization': f'Bot {token}'}
            url = f'https://discord.com/api/v10/guilds/{guild_id}/members/@me'
            
            response = requests.patch(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return True, f"✅ Successfully reset bot {image_type} to default!"
            else:
                return False, f"❌ Failed to reset {image_type} (Status: {response.status_code})"
        except Exception as e:
            return False, f"❌ Error: {str(e)[:100]}"

    @commands.command(
        name="setavatar",
        aliases=["botsetav", "avatarset"],
        help="Set a custom avatar for the bot in this server"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def setavatar(self, ctx, image_url: str):
        """Set bot avatar for this server (Server Owner only)"""
        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in OWNER_IDS:
            embed = self._create_response_embed(
                "Avatar Update",
                False,
                "❌ You need **server owner permission** to use this command!"
            )
            return await ctx.reply(embed=embed)
        
        success, message = await self._set_guild_avatar(ctx.guild.id, image_url)
        embed = self._create_response_embed("Avatar Update", success, message)
        await ctx.reply(embed=embed)

    @commands.command(
        name="setbanner",
        aliases=["botsetbanner", "bannerset"],
        help="Set a custom banner for the bot in this server"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def setbanner(self, ctx, image_url: str):
        """Set bot banner for this server (Server Owner only)"""
        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in OWNER_IDS:
            embed = self._create_response_embed(
                "Banner Update",
                False,
                "❌ You need **server owner permission** to use this command!"
            )
            return await ctx.reply(embed=embed)
        
        success, message = await self._set_guild_banner(ctx.guild.id, image_url)
        embed = self._create_response_embed("Banner Update", success, message)
        await ctx.reply(embed=embed)

    @commands.command(
        name="resetavatar",
        aliases=["botresetav", "avatardefault"],
        help="Reset bot avatar to default"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def resetavatar(self, ctx):
        """Reset bot avatar to default (Server Owner only)"""
        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in OWNER_IDS:
            embed = self._create_response_embed(
                "Reset Avatar",
                False,
                "❌ You need **server owner permission** to use this command!"
            )
            return await ctx.reply(embed=embed)
        
        success, message = await self._reset_to_default(ctx.guild.id, avatar=True)
        embed = self._create_response_embed("Reset Avatar", success, message)
        await ctx.reply(embed=embed)

    @commands.command(
        name="resetbanner",
        aliases=["botresetbanner", "bannerdefault"],
        help="Reset bot banner to default"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def resetbanner(self, ctx):
        """Reset bot banner to default (Server Owner only)"""
        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in OWNER_IDS:
            embed = self._create_response_embed(
                "Reset Banner",
                False,
                "❌ You need **server owner permission** to use this command!"
            )
            return await ctx.reply(embed=embed)
        
        success, message = await self._reset_to_default(ctx.guild.id, avatar=False)
        embed = self._create_response_embed("Reset Banner", success, message)
        await ctx.reply(embed=embed)

    @commands.command(
        name="owneravatar",
        aliases=["ownersetav", "ownerbotav"],
        help="Set bot avatar globally (Owner only)"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def owneravatar(self, ctx, image_url: str):
        """Set bot avatar globally (Bot Owner only)"""
        if ctx.author.id not in OWNER_IDS:
            embed = self._create_response_embed(
                "Global Avatar",
                False,
                "❌ You don't have permission to use this command!"
            )
            return await ctx.reply(embed=embed)
        
        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code != 200:
                embed = self._create_response_embed(
                    "Global Avatar",
                    False,
                    "❌ Invalid image URL provided"
                )
                return await ctx.reply(embed=embed)
            
            image_data = response.content
            await self.bot.user.edit(avatar=image_data)
            embed = self._create_response_embed(
                "Global Avatar",
                True,
                "✅ Successfully updated bot avatar globally!"
            )
            await ctx.reply(embed=embed)
        except Exception as e:
            embed = self._create_response_embed(
                "Global Avatar",
                False,
                f"❌ Error: {str(e)[:100]}"
            )
            await ctx.reply(embed=embed)

    @commands.command(
        name="avatarstatus",
        aliases=["avatarinfo", "checkavatar"],
        help="Check current avatar/banner info"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def avatarstatus(self, ctx):
        """Show current bot avatar/banner status"""
        embed = discord.Embed(
            title=f"{self.bot.user.name} - Avatar Status",
            color=discord.Colour(self.color)
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        status_text = (
            f"**Current Avatar:**\n{self.bot.user.display_avatar.url}\n\n"
            f"**Server:** {ctx.guild.name}\n"
            f"**Bot Created:** <t:{int(self.bot.user.created_at.timestamp())}:R>\n\n"
            f"**Available Commands:**\n"
            f"• `setavatar <url>` - Set custom avatar\n"
            f"• `setbanner <url>` - Set custom banner\n"
            f"• `resetavatar` - Reset to default\n"
            f"• `resetbanner` - Reset to default\n"
            f"• `owneravatar <url>` - Set globally (Owner)"
        )
        embed.add_field(name="Commands", value=status_text, inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.name}")
        
        await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(BotAvatar(bot))
