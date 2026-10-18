import discord
from discord.ext.commands import Cog
from discord.ext import tasks
from discord.ui import LayoutView, Container, TextDisplay, Separator
import wavelink
from Database.sqlite_db import Rex
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import traceback

# MongoDB Configuration
MONGO_URI = "mongodb+srv://fluxer8585:fluxer8585@fluxer.3izoeeq.mongodb.net/?appName=Fluxer"
mongo_client = AsyncIOMotorClient(MONGO_URI)
dbx = mongo_client["ArgoBotV2"]
db3 = dbx["247DB"]

pl_create = "https://discord.com/api/webhooks/1317540713126297630/qSz7vFvjsXmt2ibQFgI7iCYEiufwer3jJ1ldSESyd1dAtt8l6SDjJ50lhrQPHYqtVOxk"
pl_delete = "https://discord.com/api/webhooks/1317540959852040296/XvlW81rhK457rtam7nI_OFPA2dhZL2r2WCsNEJPUCNDAGMUypoWEnqGSGG6DNVAIhMVq"

class VoiceEvents(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_247_cache = {}  # Cache for 24/7 settings
        self.check_vc_status.start()

    # WHEN BOT Joins A VC Event
    @Cog.listener()
    async def on_ready(self):
        print("VoiceEvents cog on_ready called")
        await asyncio.sleep(5)  # Wait for bot to be fully ready
        reconnected_count = 0
        
        for guild in self.bot.guilds:
            try:
                voice_channel_id, txt_id = Rex(guild.id)
                
                if not voice_channel_id or not txt_id:
                    continue

                txt_channel = guild.get_channel(txt_id)
                channel = guild.get_channel(voice_channel_id)

                if not channel or not isinstance(channel, discord.VoiceChannel):
                    continue

                data = await db3.find_one({"guild_id": guild.id})
                if not data:
                    data = {"guild_id": guild.id, "247": False}
                    await db3.insert_one(data)

                is_247_enabled = data.get("247", False)
                self.guild_247_cache[guild.id] = is_247_enabled
                
                if not is_247_enabled:
                    continue

                if guild.voice_client:
                    continue
                else:
                    await self.connect_to_channel(channel, txt_channel)
                    reconnected_count += 1
                    
            except Exception as e:
                print(f"Error in on_ready for guild {guild.id}: {e}")
                traceback.print_exc()
        
        if reconnected_count > 0:
            print(f"✅ Reconnected to {reconnected_count} VC{'s' if reconnected_count != 1 else ''}")

    @Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot and member.id == self.bot.user.id:
            guild = member.guild
            try:
                if before.channel is None and after.channel is not None:
                    await self.handle_bot_join(member)

                elif before.channel is not None and after.channel is None:
                    await self.handle_bot_leave(guild)
            except Exception as e:
                print(f"Error in on_voice_state_update: {e}")
                traceback.print_exc()

    async def handle_bot_join(self, member):
        webhook = discord.SyncWebhook.from_url(pl_create)
        try:
            player: wavelink.Player = member.guild.voice_client
            content = (
                f"## Player Created\n\n"
                f"*Player Guild: {member.guild.name} ({member.guild.id})\n"
                f"Player Channel: {player.channel.name} ({player.channel.id})\n"
                f"Player Node: Melodic™*"
            )
            webhook.send(content=content)
        except Exception as e:
            print(f"Error in handle_bot_join: {e}")
            traceback.print_exc()

    async def handle_bot_leave(self, guild):
        webhook = discord.SyncWebhook.from_url(pl_delete)
        try:
            content = (
                f"## Player Destroyed\n\n"
                f"*Player Guild: {guild.name} ({guild.id})\n"
                f"Player Node: Melodic™*"
            )
            webhook.send(content=content)

            # Attempt reconnection if 24/7 is enabled
            voice_channel_id, txt_id = Rex(guild.id)
            if not voice_channel_id or not txt_id:
                return

            txt_channel = guild.get_channel(txt_id)
            channel = guild.get_channel(voice_channel_id)

            if not channel or not isinstance(channel, discord.VoiceChannel):
                return

            # Check 24/7 status with fresh database query to ensure accuracy
            data = await db3.find_one({"guild_id": guild.id})
            is_247_enabled = data.get("247", False) if data else False

            if is_247_enabled:
                await asyncio.sleep(2)  # Wait 2 seconds before reconnecting
                await self.connect_to_channel(channel, txt_channel)
        except Exception as e:
            print(f"Error in handle_bot_leave: {e}")
            traceback.print_exc()

    async def connect_to_channel(self, channel, txt_channel):
        try:
            print(f"Connecting to channel {channel.name} in guild {channel.guild.name}")
            if channel.guild.voice_client:
                print(f"Already connected to voice channel in guild {channel.guild.name}")
                return  # Avoid duplicate connections

            permissions = channel.permissions_for(channel.guild.me)
            if not permissions.connect or not permissions.speak:
                print(f"Missing permissions in {channel.name}")
                return

            player = await channel.connect(cls=wavelink.Player, self_deaf=True)
            print(f"Successfully connected to {channel.name}")

            if not hasattr(player, "loop"):
                setattr(player, "loop", False)
            player.ctx = txt_channel

            # Check if notifier is enabled
            db_notifier = dbx["247NotifierDB"]
            notifier_data = await db_notifier.find_one({"guild_id": channel.guild.id})
            notifier_enabled = notifier_data.get("notifier_enabled", True) if notifier_data else True

            if notifier_enabled:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("## Player Recreated"))
                container.add_item(Separator())
                container.add_item(TextDisplay("24/7 is Enabled, Bot Reconnected To Last Connected Voice Channel"))
                view.add_item(container)
                await txt_channel.send(view=view)

            print(f"Reconnected to {channel.name} in {channel.guild.name}")
        except discord.ClientException as e:
            print(f"Failed to connect to {channel.name}: {e}")
        except Exception as e:
            print(f"Error in connect_to_channel: {e}")
            traceback.print_exc()

    # Task to Check Voice Connection Every 2 Minutes
    @tasks.loop(minutes=2)
    async def check_vc_status(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            try:
                voice_channel_id, txt_id = Rex(guild.id)
                if not voice_channel_id or not txt_id:
                    continue

                txt_channel = guild.get_channel(txt_id)
                channel = guild.get_channel(voice_channel_id)

                if not channel or not isinstance(channel, discord.VoiceChannel):
                    continue

                # Check 24/7 status with fresh database query
                data = await db3.find_one({"guild_id": guild.id})
                is_247_enabled = data.get("247", False) if data else False

                if is_247_enabled and not guild.voice_client:
                    await self.connect_to_channel(channel, txt_channel)
            except Exception as e:
                print(f"Error in check_vc_status for guild {guild.id}: {e}")
                traceback.print_exc()

    @check_vc_status.before_loop
    async def before_check_vc_status(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(VoiceEvents(bot))
