import discord
from discord.ext import commands
from discord import ui
from discord.ui import LayoutView, Container, TextDisplay, Separator, Button, MediaGallery
import aiohttp
import datetime
import random
import requests
from utils.Tools import blacklist_check, ignore_check
from typing import Optional

color = 0x2f3136


class Fun(commands.Cog):
    """Fun and entertainment commands"""

    def __init__(self, bot):
        self.bot = bot
        self.color = color
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        """Clean up aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def get_anime_action(self, action: str):
        """Helper function to get anime action GIFs"""
        try:
            async with self.session.get(f"https://nekos.life/api/v2/img/{action}") as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get('url')
        except:
            pass
        return None

    @commands.command(
        name="cuddle",
        help="Cuddle mentioned user"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def cuddle(self, ctx, user: discord.Member = None):
        """Cuddle someone"""
        if user is None:
            return await ctx.send("You need to mention a user to cuddle.")
        if user == ctx.author:
            return await ctx.send("You can't cuddle yourself.")
        if user.bot:
            return await ctx.send("You can't cuddle bots.")
        
        image_url = await self.get_anime_action("cuddle")
        if not image_url:
            return await ctx.send("Failed to fetch cuddle image.")
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## Cuddle"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"{ctx.author.name} cuddles {user.name} 🤗"))
        container.add_item(Separator())
        
        gallery = MediaGallery()
        gallery.add_item(media=image_url)
        container.add_item(gallery)
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# {ctx.guild.name}"))
        
        view.add_item(container)
        await ctx.send(view=view)

    @commands.command(
        name="kiss",
        help="Kiss mentioned user"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def kiss(self, ctx, user: discord.Member = None):
        """Kiss someone"""
        if user is None:
            return await ctx.send("You need to mention a user to kiss.")
        if user == ctx.author:
            return await ctx.send("You can't kiss yourself.")
        if user.bot:
            return await ctx.send("You can't kiss bots.")
        
        image_url = await self.get_anime_action("kiss")
        if not image_url:
            return await ctx.send("Failed to fetch kiss image.")
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## Kiss"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"{ctx.author.name} kisses {user.name} 💋"))
        container.add_item(Separator())
        
        gallery = MediaGallery()
        gallery.add_item(media=image_url)
        container.add_item(gallery)
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# {ctx.guild.name}"))
        
        view.add_item(container)
        await ctx.send(view=view)

    @commands.command(
        name="hug",
        help="Hug mentioned user"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def hug(self, ctx, user: discord.Member = None):
        """Hug someone"""
        if user is None:
            return await ctx.send("You need to mention a user to hug.")
        if user == ctx.author:
            return await ctx.send("You can't hug yourself.")
        if user.bot:
            return await ctx.send("You can't hug bots.")
        
        image_url = await self.get_anime_action("hug")
        if not image_url:
            return await ctx.send("Failed to fetch hug image.")
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## Hug"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"{ctx.author.name} hugs {user.name} 🫂"))
        container.add_item(Separator())
        
        gallery = MediaGallery()
        gallery.add_item(media=image_url)
        container.add_item(gallery)
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# {ctx.guild.name}"))
        
        view.add_item(container)
        await ctx.send(view=view)

    @commands.command(
        name="slap",
        help="Slap mentioned user"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def slap(self, ctx, user: discord.Member = None):
        """Slap someone"""
        if user is None:
            return await ctx.send("You need to mention a user to slap.")
        
        image_url = await self.get_anime_action("slap")
        if not image_url:
            return await ctx.send("Failed to fetch slap image.")
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## Slap"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"{ctx.author.name} slapped {user.name} 👋"))
        container.add_item(Separator())
        
        gallery = MediaGallery()
        gallery.add_item(media=image_url)
        container.add_item(gallery)
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# {ctx.guild.name}"))
        
        view.add_item(container)
        await ctx.send(view=view)

    @commands.command(
        name="pat",
        help="Pat mentioned user"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def pat(self, ctx, user: discord.Member = None):
        """Pat someone"""
        if user is None:
            return await ctx.send("You need to mention a user to pat.")
        
        image_url = await self.get_anime_action("pat")
        if not image_url:
            return await ctx.send("Failed to fetch pat image.")
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## Pat"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"{ctx.author.name} pats {user.name} 🤗"))
        container.add_item(Separator())
        
        gallery = MediaGallery()
        gallery.add_item(media=image_url)
        container.add_item(gallery)
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# {ctx.guild.name}"))
        
        view.add_item(container)
        await ctx.send(view=view)

    @commands.command(
        name="feed",
        help="Feed mentioned user"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def feed(self, ctx, user: discord.Member = None):
        """Feed someone"""
        if user is None:
            return await ctx.send("You need to mention a user to feed.")
        
        image_url = await self.get_anime_action("feed")
        if not image_url:
            return await ctx.send("Failed to fetch feed image.")
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## Feed"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"{ctx.author.name} feeds {user.name} 🍽️"))
        container.add_item(Separator())
        
        gallery = MediaGallery()
        gallery.add_item(media=image_url)
        container.add_item(gallery)
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# {ctx.guild.name}"))
        
        view.add_item(container)
        await ctx.send(view=view)

    @commands.command(
        name="pet",
        help="Pet mentioned user"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def pet(self, ctx, user: discord.Member = None):
        """Pet someone"""
        if user is None:
            return await ctx.send("You need to mention a user to pet.")
        
        image_url = await self.get_anime_action("pat")
        if not image_url:
            return await ctx.send("Failed to fetch pet image.")
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## Pet"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"{ctx.author.name} pets {user.name} 🐾"))
        container.add_item(Separator())
        
        gallery = MediaGallery()
        gallery.add_item(media=image_url)
        container.add_item(gallery)
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# {ctx.guild.name}"))
        
        view.add_item(container)
        await ctx.send(view=view)

    @commands.command(
        name="howgay",
        aliases=['gay'],
        help="Check someone's gay percentage"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def howgay(self, ctx, *, person: str):
        """Check gay percentage"""
        responses = ['50', '75', '25', '1', '3', '5', '10', '65', '60', '85', '30', '40', '45', '80', '100']
        percentage = random.choice(responses)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## Gay Meter 🏳️‍🌈"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"**{person} is {percentage}% Gay**"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Requested by {ctx.author.name}"))
        
        view.add_item(container)
        await ctx.send(view=view)

    @commands.command(name="slots")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def slots(self, ctx):
        """Play slot machine"""
        emojis = "🍎🍊🍐🍋🍉🍇🍓🍒"
        a = random.choice(emojis)
        b = random.choice(emojis)
        c = random.choice(emojis)
        
        slotmachine = f"{a} {b} {c}"
        
        if a == b == c:
            result = "🎉 All Matching! You Won!"
            result_color = 0x00ff00
        elif a == b or a == c or b == c:
            result = "✨ 2 Matching! You Won!"
            result_color = 0xffff00
        else:
            result = "❌ No Matches! You Lost!"
            result_color = 0xff0000
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## Slot Machine 🎰"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"**[ {slotmachine} ]**\n\n{result}"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Played by {ctx.author.name}"))
        
        view.add_item(container)
        await ctx.send(view=view)

    @commands.command(
        name="penis",
        aliases=['dick'],
        help="Check someone's dick size"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def penis(self, ctx, user: discord.Member = None):
        """Check dick size"""
        if user is None:
            user = ctx.author
        
        size = random.randint(1, 15)
        dong = "=" * size
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## {user.display_name}'s Size 🍆"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"**8{dong}D**"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# What's {user.name}'s size?"))
        
        view.add_item(container)
        await ctx.send(view=view)

    @commands.command(
        name="funmeme",
        help="Get a random meme from Reddit",
        aliases=["rmeme", "randommeme"]
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def meme(self, ctx):
        """Get random meme from Reddit"""
        try:
            async with self.session.get('https://www.reddit.com/r/dankmemes/new.json?sort=hot') as r:
                if r.status == 200:
                    res = await r.json()
                    meme_url = res['data']['children'][random.randint(0, 25)]['data']['url']
                    
                    view = LayoutView()
                    container = Container()
                    
                    container.add_item(TextDisplay("## Random Meme 😂"))
                    container.add_item(Separator())
                    
                    gallery = MediaGallery()
                    gallery.add_item(media=meme_url)
                    container.add_item(gallery)
                    
                    container.add_item(Separator())
                    container.add_item(TextDisplay(f"-# Requested by {ctx.author.name}"))
                    
                    view.add_item(container)
                    await ctx.send(view=view)
        except Exception as e:
            await ctx.send(f"Failed to fetch meme: {str(e)}")

    @commands.command(
        name="iplookup",
        aliases=['ip', 'ipl'],
        help="Shows info about an IP address"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def iplookup(self, ctx, *, ip: str):
        """IP lookup information"""
        try:
            async with self.session.get(f"http://ipwhois.app/json/{ip}") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    view = LayoutView()
                    container = Container()
                    
                    container.add_item(TextDisplay(f"## IP Lookup: {ip}"))
                    container.add_item(Separator())
                    
                    location_info = (
                        f"**Location Info:**\n"
                        f"• Type: {data.get('type', 'N/A')}\n"
                        f"• Country: {data.get('country', 'N/A')} ({data.get('country_code', 'N/A')})\n"
                        f"• Region: {data.get('region', 'N/A')}\n"
                        f"• City: {data.get('city', 'N/A')}\n"
                        f"• Latitude: {data.get('latitude', 'N/A')}\n"
                        f"• Longitude: {data.get('longitude', 'N/A')}\n\n"
                        f"**Timezone Info:**\n"
                        f"• Timezone: {data.get('timezone', 'N/A')}\n"
                        f"• GMT: {data.get('timezone_gmt', 'N/A')}\n\n"
                        f"**ISP Info:**\n"
                        f"• ISP: {data.get('isp', 'N/A')}\n"
                        f"• Organization: {data.get('org', 'N/A')}"
                    )
                    container.add_item(TextDisplay(location_info))
                    
                    container.add_item(Separator())
                    container.add_item(TextDisplay(f"-# Requested by {ctx.author.name}"))
                    
                    view.add_item(container)
                    await ctx.send(view=view)
                else:
                    await ctx.send("Failed to lookup IP address.")
        except KeyError:
            await ctx.send("KeyError occurred. Perhaps this is a bogon or invalid IP address?")
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")


async def setup(bot):
    await bot.add_cog(Fun(bot))
