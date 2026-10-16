import discord
from discord.ext import commands
from discord import ui
from discord.ui import LayoutView, Container, Section, TextDisplay, Separator, MediaGallery, ActionRow, Button, Thumbnail
from typing import Optional
import random

COLOR = 0x2f3136
SUCCESS_COLOR = 0x00ff88

class Media(commands.Cog):
    """Media and fun image commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.color = COLOR
    
    @commands.command(name="meme")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def meme(self, ctx):
        """Get a random meme"""
        # Using a meme API URL
        meme_api = "https://meme-api.com/gimme"
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## 😂 Random Meme"))
        container.add_item(Separator())
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(meme_api) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        desc = f"**{data.get('title', 'Meme')}**\n"
                        desc += f"From r/{data.get('subreddit', 'memes')}\n"
                        desc += f"👍 {data.get('ups', 0)} upvotes"
                        
                        container.add_item(TextDisplay(desc))
                        
                        # Add meme image
                        gallery = MediaGallery()
                        gallery.add_item(media=data.get('url'))
                        container.add_item(gallery)
                        
                        container.add_item(Separator())
                        container.add_item(TextDisplay(f"-# Requested by {ctx.author.name}"))
                    else:
                        container.add_item(TextDisplay("Failed to fetch meme! Try again."))
        except Exception as e:
            container.add_item(TextDisplay("Failed to fetch meme! Try again."))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="cat")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cat(self, ctx):
        """Get a random cat image"""
        cat_api = "https://api.thecatapi.com/v1/images/search"
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## 🐱 Random Cat"))
        container.add_item(Separator())
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(cat_api) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        if data and len(data) > 0:
                            # Add cat image
                            gallery = MediaGallery()
                            gallery.add_item(media=data[0].get('url'))
                            container.add_item(gallery)
                            
                            container.add_item(Separator())
                            container.add_item(TextDisplay(f"-# Meow! 🐾"))
                        else:
                            container.add_item(TextDisplay("Failed to fetch cat! Try again."))
                    else:
                        container.add_item(TextDisplay("Failed to fetch cat! Try again."))
        except Exception:
            container.add_item(TextDisplay("Failed to fetch cat! Try again."))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="dog")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def dog(self, ctx):
        """Get a random dog image"""
        dog_api = "https://dog.ceo/api/breeds/image/random"
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## 🐶 Random Dog"))
        container.add_item(Separator())
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(dog_api) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        if data.get('status') == 'success':
                            # Add dog image
                            gallery = MediaGallery()
                            gallery.add_item(media=data.get('message'))
                            container.add_item(gallery)
                            
                            container.add_item(Separator())
                            container.add_item(TextDisplay(f"-# Woof! 🐾"))
                        else:
                            container.add_item(TextDisplay("Failed to fetch dog! Try again."))
                    else:
                        container.add_item(TextDisplay("Failed to fetch dog! Try again."))
        except Exception:
            container.add_item(TextDisplay("Failed to fetch dog! Try again."))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="mock", aliases=["spongebob"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def mock(self, ctx, *, text: str):
        """Create mocking spongebob text"""
        if len(text) > 200:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ **Text Too Long**\n\nText must be under 200 characters!"))
            view.add_item(container)
            await ctx.reply(view=view)
            return
        
        mocked = ''.join(char.upper() if i % 2 else char.lower() for i, char in enumerate(text))
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## 🧽 Mocking SpongeBob"))
        container.add_item(Separator())
        
        desc = f"**Original:**\n{text}\n\n**Mocked:**\n{mocked}"
        
        thumb = Thumbnail(ctx.author.display_avatar.url)
        section = Section(TextDisplay(desc), accessory=thumb)
        container.add_item(section)
        
        container.add_item(Separator())
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="reverse")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def reverse(self, ctx, *, text: str):
        """Reverse text"""
        if len(text) > 200:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ **Text Too Long**\n\nText must be under 200 characters!"))
            view.add_item(container)
            await ctx.reply(view=view)
            return
        
        reversed_text = text[::-1]
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## 🔄 Reversed Text"))
        container.add_item(Separator())
        
        desc = f"**Original:**\n{text}\n\n**Reversed:**\n{reversed_text}"
        
        container.add_item(TextDisplay(desc))
        container.add_item(Separator())
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="emojify")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def emojify(self, ctx, *, text: str):
        """Convert text to emoji letters"""
        if len(text) > 100:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ **Text Too Long**\n\nText must be under 100 characters!"))
            view.add_item(container)
            await ctx.reply(view=view)
            return
        
        emoji_map = {
            'a': '🇦', 'b': '🇧', 'c': '🇨', 'd': '🇩', 'e': '🇪',
            'f': '🇫', 'g': '🇬', 'h': '🇭', 'i': '🇮', 'j': '🇯',
            'k': '🇰', 'l': '🇱', 'm': '🇲', 'n': '🇳', 'o': '🇴',
            'p': '🇵', 'q': '🇶', 'r': '🇷', 's': '🇸', 't': '🇹',
            'u': '🇺', 'v': '🇻', 'w': '🇼', 'x': '🇽', 'y': '🇾',
            'z': '🇿', ' ': '  '
        }
        
        emojified = ''.join(emoji_map.get(char.lower(), char) for char in text)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## 🔤 Emojified Text"))
        container.add_item(Separator())
        
        desc = f"**Original:**\n{text}\n\n**Emojified:**\n{emojified}"
        
        container.add_item(TextDisplay(desc))
        container.add_item(Separator())
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.command(name="randompfp", aliases=["randavatar", "genpfp"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def randompfp(self, ctx):
        """Get a random AI-generated profile picture"""
        # Using random avatar generation APIs
        avatar_apis = [
            f"https://api.dicebear.com/7.x/adventurer/png?seed={random.randint(1, 100000)}",
            f"https://api.dicebear.com/7.x/avataaars/png?seed={random.randint(1, 100000)}",
            f"https://api.dicebear.com/7.x/bottts/png?seed={random.randint(1, 100000)}",
            f"https://api.dicebear.com/7.x/personas/png?seed={random.randint(1, 100000)}",
            f"https://api.dicebear.com/7.x/pixel-art/png?seed={random.randint(1, 100000)}"
        ]
        
        selected_avatar = random.choice(avatar_apis)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## 🎨 Random Profile Picture"))
        container.add_item(Separator())
        
        desc = f"**Generated Avatar:**\nHere's a randomly generated profile picture!\n\n**Download:** [Click Here]({selected_avatar})"
        
        container.add_item(TextDisplay(desc))
        
        # Add avatar image
        gallery = MediaGallery()
        gallery.add_item(media=selected_avatar)
        container.add_item(gallery)
        
        container.add_item(Separator())
        container.add_item(TextDisplay("-# Use this as your new Discord profile picture!"))
        
        view.add_item(container)
        await ctx.reply(view=view)


async def setup(bot):
    await bot.add_cog(Media(bot))
