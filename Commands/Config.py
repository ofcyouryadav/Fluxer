import discord
from discord.ext import commands
from discord.ext.commands import Context, hybrid_command, hybrid_group
from discord.ui import LayoutView, Container, TextDisplay, Separator, Section, Thumbnail, ActionRow, Button
import datetime
from typing import Optional
import psutil
import logging
from Database.repositories import PrefixRepository

logger = logging.getLogger('bot')

bot_icon = "https://cdn.discordapp.com/avatars/914785889329233931/acc9c19e09a7896237899937b57d9d89.png?size=1024"

class PlayerStyleSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            discord.SelectOption(label="Preset 1", value="preset_1"),
            discord.SelectOption(label="Preset 2", value="preset_2"),
        ]
        super().__init__(placeholder="Select a player style...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()

class PlayerStyleView(LayoutView):
    def __init__(self, bot):
        super().__init__()
        container = Container()
        
        container.add_item(TextDisplay("## Player Style"))
        container.add_item(Separator())
        container.add_item(TextDisplay("Select your preferred player style below."))
        
        row = ActionRow()
        row.add_item(PlayerStyleSelect(bot))
        container.add_item(row)
        self.add_item(container)

    async def on_timeout(self):
        # Clear view when timeout occurs
        if hasattr(self, 'message'):
            try:
                await self.message.edit(view=None)
            except:
                pass

class Config(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot  
        self.color = 0x2f3136
     #   self.config_repo = ConfigRepository()
        self.prefix_repo = PrefixRepository()
      #  self.ignore_repo = IgnoreRepository()
     #   self.settings_repo = SettingsRepository()
        # Initialize caches
        self._247_states = {}
        self._button_states = {}
        logger.info("Config cog initialized with enhanced caching")

    @hybrid_command(name="stats", description="Shows the bot's stats")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def stats(self, ctx):
        """Shows the bot's stats using Component V2"""
        try:
            def create_stats_view(active_tab="general"):
                layout = LayoutView()
                container = Container()
                
                if active_tab == "team":
                    container.add_item(TextDisplay("## Team Info"))
                    container.add_item(Separator())
                    thumb = Thumbnail(self.bot.user.avatar.url)
                    section = Section(TextDisplay("**__Owner__**\n1. [Kumar](https://discord.com/users/458651863668228096) [ID: 458651863668228096]"), accessory=thumb)
                    container.add_item(section)
                elif active_tab == "general":
                    channels = len(list(self.bot.get_all_channels()))
                    total_members = sum(g.member_count for g in self.bot.guilds if g.member_count)
                    container.add_item(TextDisplay("## General Info"))
                    container.add_item(Separator())
                    thumb = Thumbnail(self.bot.user.avatar.url)
                    desc = f"**__Fluxer's Information__**\nBot's Mention: <@{self.bot.user.id}>\nBot's Name: {self.bot.user.name}\nBot's Version: 1.0\nTotal Servers: {len(self.bot.guilds):,}\nTotal Users: {total_members:,}\nTotal Channels: {channels:,}\nLast Rebooted: <t:{int(self.bot.launch_time.timestamp())}:R>"
                    section = Section(TextDisplay(desc), accessory=thumb)
                    container.add_item(section)
                elif active_tab == "system":
                    uptime_seconds = int(datetime.datetime.now().timestamp() - self.bot.launch_time.timestamp())
                    uptime_str = str(datetime.timedelta(seconds=uptime_seconds))
                    container.add_item(TextDisplay("## System Info"))
                    container.add_item(Separator())
                    thumb = Thumbnail(self.bot.user.avatar.url)
                    desc = f"**__System Information__**\nCPU Usage: {psutil.cpu_percent()}%\nRAM Usage: {psutil.virtual_memory().percent}%\nDisk Usage: {psutil.disk_usage('/').percent}%\nBot's Uptime: {uptime_str}"
                    section = Section(TextDisplay(desc), accessory=thumb)
                    container.add_item(section)
                
                # Add buttons inside container
                row = ActionRow()
                btn_team = Button(label="Team Info", style=discord.ButtonStyle.red if active_tab == "team" else discord.ButtonStyle.grey, disabled=active_tab == "team", custom_id=f"stats_team_{ctx.author.id}")
                btn_general = Button(label="General Info", style=discord.ButtonStyle.red if active_tab == "general" else discord.ButtonStyle.grey, disabled=active_tab == "general", custom_id=f"stats_general_{ctx.author.id}")
                btn_system = Button(label="System Info", style=discord.ButtonStyle.red if active_tab == "system" else discord.ButtonStyle.grey, disabled=active_tab == "system", custom_id=f"stats_system_{ctx.author.id}")
                
                async def team_cb(interaction):
                    if interaction.user != ctx.author:
                        return await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
                    await interaction.response.edit_message(view=create_stats_view("team"))
                
                async def general_cb(interaction):
                    if interaction.user != ctx.author:
                        return await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
                    await interaction.response.edit_message(view=create_stats_view("general"))
                
                async def system_cb(interaction):
                    if interaction.user != ctx.author:
                        return await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
                    await interaction.response.edit_message(view=create_stats_view("system"))
                
                btn_team.callback = team_cb
                btn_general.callback = general_cb
                btn_system.callback = system_cb
                row.add_item(btn_team)
                row.add_item(btn_general)
                row.add_item(btn_system)
                container.add_item(row)
                layout.add_item(container)
                return layout
            
            await ctx.send(view=create_stats_view("general"))
        except Exception as e:
            logger.error(f"Error in stats command: {e}")
            await ctx.send("An error occurred while fetching stats.")

    @hybrid_group(name="toggle", description="Toggle various bot settings")
    @commands.has_permissions(administrator=True)
    async def toggle(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            pre = await self.prefix_repo.get_prefix(ctx.guild.id)
            from discord.ui import Thumbnail, Section
            layout = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## Toggle Commands"))
            container.add_item(Separator())
            thumb = Thumbnail(bot_icon)
            desc = (
                f"{pre}toggle preset\nToggle the preset for your nowplaying embed.\n\n"
                f"{pre}toggle buttons\nToggle the button mode for your server."
            )
            section = Section(TextDisplay(desc), accessory=thumb)
            container.add_item(section)
            layout.add_item(container)
            await ctx.send(view=layout)

    @hybrid_command(name="247", description="Toggle 24/7 mode for your server")
    @commands.has_permissions(administrator=True)
    async def toggle_247(self, ctx: Context):
        """Toggle 24/7 mode for the server - keeps the bot connected to voice channel"""
        from motor.motor_asyncio import AsyncIOMotorClient
        MONGO_URI = "mongodb+srv://fluxer8585:fluxer8585@fluxer.3izoeeq.mongodb.net/?appName=Fluxer"
        mongo_client = AsyncIOMotorClient(MONGO_URI)
        dbx = mongo_client["ArgoBotV2"]
        db_247 = dbx["247ModeDB"]
        
        guild_data = await db_247.find_one({"guild_id": ctx.guild.id})
        current_status = guild_data.get("enabled", False) if guild_data else False
        
        new_status = not current_status
        
        await db_247.update_one(
            {"guild_id": ctx.guild.id},
            {"$set": {"enabled": new_status}},
            upsert=True
        )
        
        self._247_states[ctx.guild.id] = new_status
        
        # If enabling 24/7 and bot is in a voice channel, save the context immediately
        if new_status and ctx.guild.voice_client and ctx.guild.voice_client.channel:
            from Database.sqlite_db import save_ctx
            try:
                save_ctx(ctx.guild.id, ctx.guild.voice_client.channel.id, ctx.channel.id)
                logger.info(f"Saved 24/7 context for guild {ctx.guild.name}")
            except Exception as e:
                logger.error(f"Failed to save 24/7 context: {e}")
        
        layout = LayoutView()
        container = Container()
        
        if new_status:
            container.add_item(TextDisplay("## 24/7 Mode"))
            container.add_item(Separator())
            container.add_item(TextDisplay(" **247 is enabled**\n\n-# The bot will stay connected to the voice channel even when no music is playing."))
        else:
            container.add_item(TextDisplay("## 24/7 Mode"))
            container.add_item(Separator())
            container.add_item(TextDisplay(" **247 is disabled**\n\n-# The bot will disconnect from the voice channel when idle."))
        
        layout.add_item(container)
        await ctx.send(view=layout)

    @hybrid_command(name="247notifier", description="Toggle 24/7 reconnection notifications")
    @commands.has_permissions(administrator=True)
    async def notifier_247(self, ctx: Context):
        """Toggle 24/7 reconnection notifications for the server"""
        from motor.motor_asyncio import AsyncIOMotorClient
        MONGO_URI = "mongodb+srv://fluxer8585:fluxer8585@fluxer.3izoeeq.mongodb.net/?appName=Fluxer"
        mongo_client = AsyncIOMotorClient(MONGO_URI)
        dbx = mongo_client["ArgoBotV2"]
        db_notifier = dbx["247NotifierDB"]
        
        guild_data = await db_notifier.find_one({"guild_id": ctx.guild.id})
        current_status = guild_data.get("notifier_enabled", False) if guild_data else False
        
        new_status = not current_status
        
        await db_notifier.update_one(
            {"guild_id": ctx.guild.id},
            {"$set": {"notifier_enabled": new_status}},
            upsert=True
        )
        
        layout = LayoutView()
        container = Container()
        
        if new_status:
            container.add_item(TextDisplay("## 24/7 Notifier"))
            container.add_item(Separator())
            container.add_item(TextDisplay(" **247 Notifier is enabled**\n\n-# Bot will send reconnection notifications when 24/7 mode reconnects."))
        else:
            container.add_item(TextDisplay("## 24/7 Notifier"))
            container.add_item(Separator())
            container.add_item(TextDisplay(" **247 Notifier is disabled**\n\n-# Bot will no longer send reconnection notifications."))
        
        layout.add_item(container)
        await ctx.send(view=layout)

    @hybrid_command(name="playingredirect", description="Set channel for now playing messages")
    @commands.has_permissions(administrator=True)
    async def playingredirect(self, ctx: Context, channel: Optional[discord.TextChannel] = None):
        """Redirect now playing messages to a specific channel"""
        from motor.motor_asyncio import AsyncIOMotorClient
        MONGO_URI = "mongodb+srv://fluxer8585:fluxer8585@fluxer.3izoeeq.mongodb.net/?appName=Fluxer"
        mongo_client = AsyncIOMotorClient(MONGO_URI)
        dbx = mongo_client["ArgoBotV2"]
        db_redirect = dbx["PlayingRedirectDB"]
        
        if channel is None:
            # Disable redirect
            await db_redirect.delete_one({"guild_id": ctx.guild.id})
            layout = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## Playing Redirect Disabled"))
            container.add_item(Separator())
            container.add_item(TextDisplay("Now playing messages will be sent to the channel where the song was requested."))
            layout.add_item(container)
            await ctx.send(view=layout)
        else:
            # Enable redirect to specific channel
            await db_redirect.update_one(
                {"guild_id": ctx.guild.id},
                {"$set": {"channel_id": channel.id, "channel_name": channel.name}},
                upsert=True
            )
            
            layout = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## Playing Redirect Enabled"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f" Now playing messages will be sent to {channel.name}\n\n-# The message will be automatically deleted after the song finishes."))
            layout.add_item(container)
            await ctx.send(view=layout)

async def setup(bot: commands.Bot):
    await bot.add_cog(Config(bot))
