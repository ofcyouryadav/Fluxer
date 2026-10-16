from __future__ import annotations
import discord
import datetime
from discord.ext import commands
from utils.Tools import *
import aiohttp

color = 0x2f3136


class Nsfw(commands.Cog):
    """NSFW commands"""

    def __init__(self, client):
        self.client = client
        self.color = color
        self.session = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    def help_custom(self):
        emoji = '<:codez_nsfw:1148119095213051954>'
        label = "Nsfw"
        description = "Shows You Nsfw Commands."
        return emoji, label, description

    @commands.group(name="nsfw", invoke_without_command=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @blacklist_check()
    @ignore_check()
    async def nsfw(self, ctx: commands.Context):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    async def _check_nsfw_and_send(self, ctx, image_url):
        """Helper to check NSFW channel and send image"""
        if not ctx.channel.is_nsfw():
            await ctx.reply(embed=discord.Embed(
                description="Please Enable The NSFW Option From Channel Setting To Continue Forward:",
                color=self.color,
                timestamp=datetime.datetime.utcnow()
            ).set_image(
                url="https://support.discord.com/hc/article_attachments/4580654542103/unnamed.png"
            ).set_thumbnail(url=ctx.author.display_avatar.url))
            return
        
        embed = discord.Embed(color=self.color, timestamp=datetime.datetime.utcnow())
        embed.set_image(url=image_url)
        await ctx.send(embed=embed)

    async def _fetch_nekos_fun(self, category: str):
        """Helper to fetch from nekos.fun API"""
        try:
            async with self.session.get(
                f"http://api.nekos.fun:8080/api/{category}",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("image")
        except:
            pass
        return None

    @nsfw.command(name="4k")
    @blacklist_check()
    @ignore_check()
    async def _4k(self, ctx):
        """Get 4K NSFW image"""
        image = await self._fetch_nekos_fun("4k")
        if image:
            await self._check_nsfw_and_send(ctx, image)
        else:
            await ctx.send("Failed to fetch image.")

    @nsfw.command(name="pussy")
    @blacklist_check()
    @ignore_check()
    async def _pussy(self, ctx):
        """Get pussy NSFW image"""
        image = await self._fetch_nekos_fun("pussy")
        if image:
            await self._check_nsfw_and_send(ctx, image)
        else:
            await ctx.send("Failed to fetch image.")

    @nsfw.command(name="boobs")
    @blacklist_check()
    @ignore_check()
    async def _boobs(self, ctx):
        """Get boobs NSFW image"""
        image = await self._fetch_nekos_fun("boobs")
        if image:
            await self._check_nsfw_and_send(ctx, image)
        else:
            await ctx.send("Failed to fetch image.")

    @nsfw.command(name="lewd")
    @blacklist_check()
    @ignore_check()
    async def _lewd(self, ctx):
        """Get lewd NSFW image"""
        image = await self._fetch_nekos_fun("lewd")
        if image:
            await self._check_nsfw_and_send(ctx, image)
        else:
            await ctx.send("Failed to fetch image.")

    @nsfw.command(name="lesbian")
    @blacklist_check()
    @ignore_check()
    async def _lesbian(self, ctx):
        """Get lesbian NSFW image"""
        image = await self._fetch_nekos_fun("lesbian")
        if image:
            await self._check_nsfw_and_send(ctx, image)
        else:
            await ctx.send("Failed to fetch image.")

    @nsfw.command(name="blowjob")
    @blacklist_check()
    @ignore_check()
    async def _blowjob(self, ctx):
        """Get blowjob NSFW image"""
        image = await self._fetch_nekos_fun("blowjob")
        if image:
            await self._check_nsfw_and_send(ctx, image)
        else:
            await ctx.send("Failed to fetch image.")

    @nsfw.command(name="cum")
    @blacklist_check()
    @ignore_check()
    async def _cum(self, ctx):
        """Get cum NSFW image"""
        image = await self._fetch_nekos_fun("cum")
        if image:
            await self._check_nsfw_and_send(ctx, image)
        else:
            await ctx.send("Failed to fetch image.")

    @nsfw.command(name="gasm")
    @blacklist_check()
    @ignore_check()
    async def _gasm(self, ctx):
        """Get gasm NSFW image"""
        image = await self._fetch_nekos_fun("gasm")
        if image:
            await self._check_nsfw_and_send(ctx, image)
        else:
            await ctx.send("Failed to fetch image.")

    @nsfw.command(name="hentai")
    @blacklist_check()
    @ignore_check()
    async def _hentai(self, ctx):
        """Get hentai NSFW image"""
        image = await self._fetch_nekos_fun("hentai")
        if image:
            await self._check_nsfw_and_send(ctx, image)
        else:
            await ctx.send("Failed to fetch image.")

    @nsfw.command(name="anal")
    @commands.is_nsfw()
    @commands.bot_has_permissions(embed_links=True)
    async def anal(self, ctx):
        """Get random anal image"""
        url = "https://nekobot.xyz/api/image"
        params = {"type": "anal"}

        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    res = await r.json()
                    img = res["message"]
                    
                    em = discord.Embed(title="Anal", timestamp=datetime.datetime.utcnow(), color=self.color)
                    em.set_footer(text=f"{ctx.author.name}")
                    em.set_image(url=img)
                    await ctx.reply(embed=em)
                else:
                    await ctx.send("Failed to fetch image.")
        except:
            await ctx.send("Failed to fetch image.")

    @nsfw.command(name="gonewild")
    @commands.is_nsfw()
    @commands.bot_has_permissions(embed_links=True)
    async def gonewild(self, ctx):
        """Get random gonewild image"""
        url = "https://nekobot.xyz/api/image"
        params = {"type": "gonewild"}

        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    res = await r.json()
                    img = res["message"]
                    
                    em = discord.Embed(timestamp=datetime.datetime.utcnow(), color=self.color)
                    em.set_footer(text=f"{ctx.author.name}")
                    em.set_image(url=img)
                    await ctx.reply(embed=em)
                else:
                    await ctx.send("Failed to fetch image.")
        except:
            await ctx.send("Failed to fetch image.")

    @nsfw.command(name="hanal")
    @commands.is_nsfw()
    @commands.bot_has_permissions(embed_links=True)
    async def hanal(self, ctx):
        """Get random hentai anal image"""
        url = "https://nekobot.xyz/api/image"
        params = {"type": "hanal"}

        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    res = await r.json()
                    img = res["message"]
                    
                    em = discord.Embed(timestamp=datetime.datetime.utcnow(), color=self.color)
                    em.set_footer(text=f"{ctx.author.name}")
                    em.set_image(url=img)
                    await ctx.reply(embed=em)
                else:
                    await ctx.send("Failed to fetch image.")
        except:
            await ctx.send("Failed to fetch image.")

    @nsfw.command(name="holo")
    @commands.is_nsfw()
    @commands.bot_has_permissions(embed_links=True)
    async def holo(self, ctx):
        """Get random holo image"""
        url = "https://nekobot.xyz/api/image"
        params = {"type": "holo"}

        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    res = await r.json()
                    img = res["message"]
                    
                    em = discord.Embed(timestamp=datetime.datetime.utcnow(), color=self.color)
                    em.set_footer(text=f"{ctx.author.name}")
                    em.set_image(url=img)
                    await ctx.reply(embed=em)
                else:
                    await ctx.send("Failed to fetch image.")
        except:
            await ctx.send("Failed to fetch image.")

    @nsfw.command(name="neko")
    @commands.is_nsfw()
    @commands.bot_has_permissions(embed_links=True)
    async def neko(self, ctx):
        """Get random neko image"""
        url = "https://nekobot.xyz/api/image"
        params = {"type": "neko"}

        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status == 200:
                    res = await r.json()
                    img = res["message"]
                    
                    em = discord.Embed(timestamp=datetime.datetime.utcnow(), color=self.color)
                    em.set_footer(text=f"{ctx.author.name}")
                    em.set_image(url=img)
                    await ctx.reply(embed=em)
                else:
                    await ctx.send("Failed to fetch image.")
        except:
            await ctx.send("Failed to fetch image.")


async def setup(bot):
    await bot.add_cog(Nsfw(bot))
