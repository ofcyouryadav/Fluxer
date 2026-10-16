import os
import io
import random
import discord
import datetime
import aiohttp
from discord.ext import commands
from discord.ext.commands import errors
from discord.ui import LayoutView, Container, TextDisplay, Separator, MediaGallery, Section, Thumbnail
from PIL import Image, ImageFont, ImageDraw
from utils.Tools import *

class Ship(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.special_users = [458651863668228096,327878682314014721]

    @commands.command(pass_context=True, help="Ship two users together.")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def ship(self, ctx, user1: discord.Member = None, user2: discord.Member = None):
        if user1 is None:  
            user1 = ctx.author
            guild = ctx.guild
            members = guild.members
            user2 = random.choice(members)
        elif user2 is None:  
            user2 = user1
            user1 = ctx.author

        author_id = float(user1.id)
        user_id = float(user2.id)

        if user1.id in self.special_users and user2.id in self.special_users:
            rate = 100
        else:
            now = datetime.datetime.now()
            day_seed = (now.day + now.month + now.year) / 3
            seed = (author_id + user_id) / day_seed
            random.seed(seed)
            rate = random.randint(1, 99)

        user_avatar = await get_avatar(user2)
        author_avatar = await get_avatar(user1)

        if user_avatar and author_avatar:
            image_path = await self.make_modern_image(author_avatar, user_avatar, user1.name, user2.name, rate)
            await self.send_ship_v2(ctx, user1, user2, rate, image_path)
        else:
            await self.send_ship_v2(ctx, user1, user2, rate)

    async def make_modern_image(self, avatar1, avatar2, name1, name2, rate):
        """Create a modern ship image with gradient and modern styling"""
        os.makedirs("./data/ship", exist_ok=True)
        
        width, height = 800, 400
        
        bg_color_1 = (255, 100, 150)
        bg_color_2 = (255, 50, 100)
        
        gradient = Image.new('RGB', (width, height), bg_color_1)
        draw = ImageDraw.Draw(gradient)
        
        for y in range(height):
            ratio = y / height
            r = int(bg_color_1[0] * (1 - ratio) + bg_color_2[0] * ratio)
            g = int(bg_color_1[1] * (1 - ratio) + bg_color_2[1] * ratio)
            b = int(bg_color_1[2] * (1 - ratio) + bg_color_2[2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        avatar1_resized = avatar1.resize((180, 180), Image.Resampling.LANCZOS)
        avatar2_resized = avatar2.resize((180, 180), Image.Resampling.LANCZOS)
        
        mask = Image.new('L', (180, 180), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, 180, 180), fill=255)
        
        gradient.paste(avatar1_resized, (80, 110), mask)
        gradient.paste(avatar2_resized, (540, 110), mask)
        
        try:
            title_font = ImageFont.truetype("./data/ship/font.ttf", 60) if os.path.exists("./data/ship/font.ttf") else ImageFont.load_default()
            name_font = ImageFont.truetype("./data/ship/font.ttf", 32) if os.path.exists("./data/ship/font.ttf") else ImageFont.load_default()
            rate_font = ImageFont.truetype("./data/ship/font.ttf", 48) if os.path.exists("./data/ship/font.ttf") else ImageFont.load_default()
        except:
            title_font = ImageFont.load_default()
            name_font = ImageFont.load_default()
            rate_font = ImageFont.load_default()
        
        title_text = "Love Meter"
        draw.text((width // 2, 30), title_text, font=title_font, fill=(0, 0, 0), anchor="mt")
        
        draw.text((160, 310), name1[:15], font=name_font, fill=(0, 0, 0), anchor="mt")
        draw.text((620, 310), name2[:15], font=name_font, fill=(0, 0, 0), anchor="mt")
        
        rate_text = f"{rate}%"
        draw.text((width // 2, 170), rate_text, font=rate_font, fill=(0, 0, 0), anchor="mm")
        
        bar_width = 400
        bar_height = 30
        bar_x = (width - bar_width) // 2
        bar_y = 350
        
        draw.rectangle([(bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height)], 
                      outline=(0, 0, 0), width=3)
        
        fill_width = int((rate / 100) * (bar_width - 6))
        if fill_width > 0:
            fill_color = (0, 0, 0)
            draw.rectangle([(bar_x + 3, bar_y + 3), (bar_x + 3 + fill_width, bar_y + bar_height - 3)], 
                          fill=fill_color)
        
        output_path = "./data/ship/modern_ship.png"
        gradient.save(output_path, "PNG")
        return output_path

    async def send_ship_v2(self, ctx, user1: discord.Member, user2: discord.Member, rate: int, image_path: str = None):
        """Send ship result using Component V2"""
        view = LayoutView()
        container = Container()
        
        if rate >= 80:
            status = "💕 Perfect Match!"
            description = f"{user1.name} and {user2.name} are a perfect match made in heaven!"
        elif rate >= 60:
            status = "💖 Great Match!"
            description = f"{user1.name} and {user2.name} have great chemistry!"
        elif rate >= 40:
            status = "💛 Good Match"
            description = f"{user1.name} and {user2.name} could work out!"
        elif rate >= 20:
            status = "💙 Fair Match"
            description = f"{user1.name} and {user2.name} might need some work..."
        else:
            status = "💔 Not Compatible"
            description = f"{user1.name} and {user2.name} aren't very compatible..."
        
        container.add_item(TextDisplay(f"## {status}"))
        container.add_item(Separator())
        container.add_item(TextDisplay(description))
        container.add_item(Separator())
        
        progress_bar = self.create_progress_bar(rate)
        container.add_item(TextDisplay(f"**Love Rate:** {rate}%\n`{progress_bar}`"))
        
        file = None
        if image_path and os.path.exists(image_path):
            file = discord.File(image_path, filename="ship.png")
            gallery = MediaGallery()
            gallery.add_item(media="attachment://ship.png")
            container.add_item(gallery)
        
        view.add_item(container)
        
        if file:
            await ctx.reply(view=view, file=file)
        else:
            await ctx.reply(view=view)

    def create_progress_bar(self, rate):
        filled_length = int(20 * rate // 100)
        bar = '█' * filled_length + '░' * (20 - filled_length)
        return bar


async def get_avatar(user):
    try:
        user_url = user.display_avatar.replace(format="png").url
        async with aiohttp.ClientSession() as session:
            async with session.get(user_url + "?size=256") as response:
                avatar_data = await response.read()
                avatar = Image.open(io.BytesIO(avatar_data)).convert('RGBA')
                tmp = Image.new('RGBA', avatar.size, (255, 255, 255, 255))
                tmp = Image.alpha_composite(tmp, avatar)
                return tmp
    except Exception as e:
        print(f"Error fetching avatar: {e}")
        return None


async def setup(bot):
    await bot.add_cog(Ship(bot))
