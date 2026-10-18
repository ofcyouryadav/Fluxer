import discord
from discord.ext import commands
from discord import ui
from discord.ui import LayoutView
import datetime
from Database.repositories import PrefixRepository
from Database.utils import cache_manager
from Functions.session_manager import session_manager
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://insane:op5@cluster0.5qyw6.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["ArgoBotV2"]
logger = logging.getLogger(__name__)

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embeds = []
        self._cd_cache = {}  # Cache for cooldowns
        self.cd_mapping = commands.CooldownMapping.from_cooldown(2, 3, commands.BucketType.member)
        self.prefix_repo = PrefixRepository()
        self._session = None
        logger.info("\x1b[38;5;197m[Cog]\x1b[0m OnMention cog initialized")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        bldata = await db.blacklist.find_one({"blacklist": self.bot.user.id})

        if bldata is None:
            blisted = []
        else:
            blisted = bldata["user_id"]
        

        # Handle bot mention only
        if self.bot.user.mentioned_in(message) and len(message.content.split()) == 1:
            try:
                # Get prefix using prefix repository
                if message.author.id in blisted:
                    return
                guild_id = message.guild.id if message.guild else None
                prefix = await self.prefix_repo.get_prefix(guild_id) if guild_id else "+"

                # Create Component V2 response
                view = LayoutView()
                container = ui.Container()
                
                # Add content with user info
                content = f"Hey {message.author.name}, you can use `{prefix}help` or `/help` to see all my commands!"
                thumb = ui.Thumbnail(message.author.display_avatar.url)
                section = ui.Section(
                    ui.TextDisplay(content),
                    accessory=thumb
                )
                container.add_item(section)
                
                container.add_item(ui.Separator())
                
                # Add buttons
                buttons = ui.ActionRow()
                buttons.add_item(ui.Button(
                    label="Invite Me",
                    url=f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot%20applications.commands",
                    style=discord.ButtonStyle.link
                ))
                buttons.add_item(ui.Button(
                    label="Support Server",
                    url="https://discord.gg/jw6n7g5zbZ",
                    style=discord.ButtonStyle.link
                ))
                container.add_item(buttons)
                
                container.add_item(ui.Separator())
                container.add_item(ui.TextDisplay(f"-# {message.author.name} • <t:{int(datetime.datetime.now(datetime.UTC).timestamp())}:R>"))
                
                view.add_item(container)

                await message.reply(view=view, mention_author=False)

            except Exception as e:
                logger.error(f"Error handling mention: {e}")
                # Fallback to simple message
                await message.channel.send("Sorry, I encountered an error. Please try again later.")

async def setup(bot):
    await bot.add_cog(Events(bot))