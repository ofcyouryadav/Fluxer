import discord
from discord.ext import commands, tasks
from discord.ui import LayoutView, Container, TextDisplay, Separator, MediaGallery
from typing import Optional
from datetime import datetime, timezone
import aiohttp
import asyncio
import random

COLOR = 0x2f3136
SUCCESS_COLOR = 0x00ff88
ERROR_COLOR = 0xff0033

class AutoPFP(commands.Cog):
    """Automated profile picture posting system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.color = COLOR
        self.auto_pfp_collection = bot.db["auto_pfp"]
        self.post_pfp_task.start()
    
    def cog_unload(self):
        self.post_pfp_task.cancel()
    
    @tasks.loop(minutes=1)
    async def post_pfp_task(self):
        """Check for and post scheduled PFPs"""
        try:
            active_configs = await self.auto_pfp_collection.find({
                "enabled": True
            }).to_list(None)
            
            for config in active_configs:
                try:
                    guild = self.bot.get_guild(config["guild_id"])
                    if not guild:
                        continue
                    
                    channel = guild.get_channel(config["channel_id"])
                    if not channel:
                        continue
                    
                    pfp_type = config["pfp_type"]
                    
                    image_url = await self.fetch_pfp(pfp_type)
                    if image_url:
                        view = LayoutView()
                        container = Container()
                        
                        type_names = {
                            "anime_girl": " Anime Girl PFP",
                            "anime_boy": " Anime Boy PFP",
                            "real_girl": "🦰 Real Girl PFP",
                            "real_boy": "🦰 Real Boy PFP",
                            "couples_anime": " Anime Couples PFP",
                            "couples_real": " Couples PFP"
                        }
                        
                        container.add_item(TextDisplay(f"## {type_names.get(pfp_type, 'Profile Picture')}"))
                        container.add_item(Separator())
                        
                        gallery = MediaGallery(discord.MediaGalleryItem(image_url))
                        container.add_item(gallery)
                        container.add_item(Separator())
                        container.add_item(TextDisplay("-# Auto PFP by Fluxer"))
                        
                        view.add_item(container)
                        await channel.send(view=view)
                        
                except Exception as e:
                    print(f"Error posting auto PFP: {e}")
                    
        except Exception as e:
            print(f"Error in post_pfp_task: {e}")
    
    @post_pfp_task.before_loop
    async def before_post_pfp_task(self):
        await self.bot.wait_until_ready()
    
    async def fetch_pfp(self, pfp_type: str) -> Optional[str]:
        """Fetch a random PFP from various sources"""
        apis = {
            "girls": [
                "https://api.waifu.pics/sfw/waifu",
                "https://nekos.best/api/v2/neko"
            ],
            "boys": [
                "https://nekos.best/api/v2/husbando"
            ],
            "couple": [
                "https://api.waifu.pics/sfw/waifu",
                "https://nekos.best/api/v2/neko"
            ],
            "anime": [
                "https://api.waifu.pics/sfw/waifu",
                "https://nekos.best/api/v2/neko"
            ],
            "faceless": [
                "https://api.waifu.pics/sfw/waifu",
                "https://nekos.best/api/v2/neko"
            ],
            "anime_girl": [
                "https://api.waifu.pics/sfw/waifu",
                "https://nekos.best/api/v2/neko"
            ],
            "anime_boy": [
                "https://nekos.best/api/v2/husbando"
            ],
            "real_girl": [
                "https://randomuser.me/api/?gender=female&random=RANDOM"
            ],
            "real_boy": [
                "https://randomuser.me/api/?gender=male&random=RANDOM"
            ],
            "couples_anime": [
                "https://api.waifu.pics/sfw/neko",
                "https://nekos.best/api/v2/neko"
            ],
            "couples_real": [
                "https://randomuser.me/api/?random=RANDOM"
            ]
        }
        
        api_url = random.choice(apis.get(pfp_type, apis["anime"]))
        
        # Replace RANDOM for RandomUser
        if "randomuser.me" in api_url:
            api_url = api_url.replace("RANDOM", str(random.randint(0, 1000)))
        
        should_close = False
        try:
            if hasattr(self.bot, 'session') and self.bot.session:
                session = self.bot.session
            else:
                session = aiohttp.ClientSession()
                should_close = True
            
            try:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if "url" in data:
                            return data["url"]
                        elif "results" in data and len(data["results"]) > 0:
                            result = data["results"][0]
                            if "picture" in result and isinstance(result["picture"], dict):
                                img_url = result["picture"].get("large") or result["picture"].get("medium") or result["picture"].get("thumbnail")
                                if img_url:
                                    return img_url
                            elif "url" in result:
                                return result.get("url")
                    else:
                        print(f"PFP API returned status {resp.status} for {pfp_type}")
            finally:
                if should_close:
                    await session.close()
        except asyncio.TimeoutError:
            print(f"Timeout fetching PFP for type {pfp_type}")
        except Exception as e:
            print(f"Error fetching PFP for {pfp_type}: {e}")
        
        return None
    
    @commands.hybrid_group(name="autopfp", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def autopfp(self, ctx):
        """Manage auto PFP posting"""
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## 📸 Auto PFP Commands"))
        container.add_item(Separator())
        
        desc = (
            "**Available Commands:**\n"
            "`autopfp setup <type> <channel>` - Setup auto posting\n"
            "`autopfp disable <type>` - Disable auto posting\n"
            "`autopfp remove <type>` - Remove channel config completely\n"
            "`autopfp list` - List all active configs\n"
            "`autopfp post <type>` - Manually post a PFP\n\n"
            "**Types:** anime_girl, anime_boy, real_girl, real_boy, couples_anime, couples_real"
        )
        
        container.add_item(TextDisplay(desc))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @autopfp.command(name="setup")
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def setup(self, ctx, pfp_type: str, channel: discord.TextChannel):
        """Setup auto PFP posting in a channel"""
        valid_types = ["anime_girl", "anime_boy", "real_girl", "real_boy", "couples_anime", "couples_real"]
        
        if pfp_type.lower() not in valid_types:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f" **Invalid Type**\n\nValid types: {', '.join(valid_types)}"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        existing = await self.auto_pfp_collection.find_one({
            "guild_id": ctx.guild.id,
            "pfp_type": pfp_type.lower()
        })
        
        if existing:
            await self.auto_pfp_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "channel_id": channel.id,
                    "enabled": True,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
        else:
            await self.auto_pfp_collection.insert_one({
                "guild_id": ctx.guild.id,
                "channel_id": channel.id,
                "pfp_type": pfp_type.lower(),
                "enabled": True,
                "created_at": datetime.now(timezone.utc)
            })
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(
            f" **Auto PFP Setup Complete**\n\n"
            f"**Type:** {pfp_type.replace('_', ' ').title()}\n"
            f"**Channel:** {channel.name}\n"
            f"**Frequency:** Every 1 minute"
        ))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @autopfp.command(name="disable")
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def disable(self, ctx, pfp_type: str):
        """Disable auto PFP posting for a type"""
        result = await self.auto_pfp_collection.update_one(
            {
                "guild_id": ctx.guild.id,
                "pfp_type": pfp_type.lower()
            },
            {"$set": {"enabled": False}}
        )
        
        if result.matched_count == 0:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f" No auto PFP config found for **{pfp_type}**."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f" Auto PFP posting disabled for **{pfp_type}**."))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @autopfp.command(name="remove")
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def remove(self, ctx, pfp_type: str):
        """Completely remove auto PFP channel configuration for a type"""
        result = await self.auto_pfp_collection.delete_one({
            "guild_id": ctx.guild.id,
            "pfp_type": pfp_type.lower()
        })
        
        if result.deleted_count == 0:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f" No auto PFP config found for **{pfp_type}**."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(
            f"##  Config Removed\n\n"
            f"Auto PFP configuration for **{pfp_type}** has been completely removed.\n\n"
            f"-# Use `autopfp setup` to create a new configuration."
        ))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @autopfp.command(name="list")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def list_configs(self, ctx):
        """List all auto PFP configurations"""
        configs = await self.auto_pfp_collection.find({
            "guild_id": ctx.guild.id
        }).to_list(None)
        
        if not configs:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## 📸 No Auto PFP Configs\n\nUse `autopfp setup` to create one."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## 📸 Auto PFP Configurations"))
        container.add_item(Separator())
        
        config_list = []
        for config in configs:
            channel = ctx.guild.get_channel(config["channel_id"])
            channel_mention = channel.name if channel else "Unknown"
            status = " Enabled" if config.get("enabled", False) else " Disabled"
            
            config_list.append(
                f"**{config['pfp_type'].capitalize()}** - {status}\n"
                f"Channel: {channel_mention}"
            )
        
        container.add_item(TextDisplay("\n\n".join(config_list)))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @autopfp.command(name="post")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def post_manual(self, ctx, pfp_type: str):
        """Manually post a PFP"""
        valid_types = ["anime_girl", "anime_boy", "real_girl", "real_boy", "couples_anime", "couples_real"]
        
        if pfp_type.lower() not in valid_types:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f" **Invalid Type**\n\nValid types: {', '.join(valid_types)}"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        image_url = await self.fetch_pfp(pfp_type.lower())
        
        if not image_url:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(" Failed to fetch PFP. Please try again."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        view = LayoutView()
        container = Container()
        
        type_names = {
            "anime_girl": " Anime Girl PFP",
            "anime_boy": " Anime Boy PFP",
            "real_girl": " Real Girl PFP",
            "real_boy": " Real Boy PFP",
            "couples_anime": " Anime Couples PFP",
            "couples_real": " Couples PFP"
        }
        
        container.add_item(TextDisplay(f"## {type_names.get(pfp_type.lower(), 'Profile Picture')}"))
        container.add_item(Separator())
        
        gallery = MediaGallery(discord.MediaGalleryItem(image_url))
        container.add_item(gallery)
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Requested by {ctx.author.name}"))
        
        view.add_item(container)
        await ctx.send(view=view)


async def setup(bot):
    await bot.add_cog(AutoPFP(bot))
