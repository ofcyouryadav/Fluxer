import discord
from discord.ext import commands
from discord import app_commands
from discord.ext.commands import Cog
from discord.ui import LayoutView, Container, TextDisplay, Separator
import wavelink
import logging
from typing import Optional, Tuple, cast, Literal
from Database.utils import cache_manager
from Functions.CheckFunctions import *
from Functions.canvas import NowPlayingCard
from Config import Config as cf
from Views.paginator import Paginator
from Views.paginators import DescriptionEmbedPaginator
from Views.SearchView import SearchView
from Views.PlayEmbeds import *
from io import BytesIO
import asyncio
import sqlite3
logger = logging.getLogger(__name__)
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
tick = "✅"

MONGO_URI = "mongodb+srv://fluxer8585:fluxer8585@fluxer.3izoeeq.mongodb.net/?appName=Fluxer"
mongo_client = AsyncIOMotorClient(MONGO_URI)
dbx = mongo_client["ArgoBotV2"]
db3 = dbx["247DB"]
db5 = dbx["SourceDB"]
from Database.sqlite_db import save_ctx, Rex

# Local SQLite setup removed - using shared module

class LoopView(LayoutView):
    def __init__(self, bot, player: wavelink.Player):
        super().__init__(timeout=30)
        self.bot = bot
        self.player: wavelink.Player = player
        self.msg: discord.Message = None
        self.disable.disabled = True
        self.loop_mode : wavelink.QueueMode
        
        # Initial container
        self.update_container("Select a loop mode")

        if player.queue.mode == wavelink.QueueMode.loop:
            self.track.disabled = True
            self.queue.disabled = False
        elif player.queue.mode == wavelink.QueueMode.loop_all:
            self.queue.disabled = True
            self.track.disabled = False
            
    def update_container(self, text):
        # Remove existing containers
        for item in self.children:
            if isinstance(item, Container):
                self.remove_item(item)
        
        container = Container()
        container.add_item(TextDisplay(f"## {text}"))
        self.add_item(container)

    async def on_timeout(self):
        if self.msg:
            try:
                await self.msg.delete()
            except:
                pass

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user not in self.player.channel.members:
            return await interaction.response.send_message(
                "You are not in the voice channel", ephemeral=True
            )
        return True

    @discord.ui.button(label="Queue")
    async def queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self.player
        player.queue.mode = wavelink.QueueMode.loop_all
        self.disable.disabled = False
        self.queue.disabled = True
        self.track.disabled = False
        
        self.update_container("Looped the queue")
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Track")
    async def track(self, interaction: discord.Interaction, button: discord.ui.Button):
        player = self.player
        player.queue.mode = wavelink.QueueMode.loop
        self.queue.disabled = False
        self.track.disabled = True
        self.disable.disabled = True
        
        self.update_container("Looped the current track")
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Disable")
    async def disable(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        player = self.player
        player.queue.mode = wavelink.QueueMode.normal
        self.track.disabled = False
        self.queue.disabled = False
        self.disable.disabled = True

        self.update_container("Disabled loop")
        await interaction.response.edit_message(view=self) 

def truncate_string(value, max_length=128, suffix="..."):
    string_value = str(value)
    string_truncated = string_value[
        : min(len(string_value), (max_length - len(suffix)))
    ]
    suffix = suffix if len(string_value) > max_length else ""
    return string_truncated + suffix

class Music(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x2f3136
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 3.0, commands.BucketType.user)
        self._history_limit = 100  # Store up to 100 tracks in history
    #    self.channel_repo = ChannelRepository()
     #   self.settings_repo = SettingsRepository()
        logger.info("Music cog initialized with async database support")

   # async def save_ctx(self, guild_id: int, voice_channel_id: Optional[int], text_channel_id: Optional[int]) -> None:
    #    """Save the last ctx (voice and text channels) in the database"""
      #  try:
       #     await self.channel_repo.save_channel_data(guild_id, voice_channel_id, text_channel_id)
      #  except Exception as e:
        #    logger.error(f"Error saving context for guild {guild_id}: {e}")
         #   raise

    #async def get_channel_data(self, guild_id: int) -> Tuple[Optional[int], Optional[int]]:
      #  """Get the last voice and text channels from the database"""
      # # try:
       #     return await self.channel_repo.get_channel_data(guild_id)
      #  except Exception as e:
       #     logger.error(f"Error getting channel data for guild {guild_id}: {e}")
         #   return None, None 
    async def query_autocomplete(
        self, interaction: discord.Interaction, query: str
    ) -> List[app_commands.Choice[str]]:
        try:
            tracks = await wavelink.Playable.search(query, source="spsearch")
        except:
            return [
                app_commands.Choice(
                    name=f"Search Something or use url or query", value=""
                )
            ]
        songs = [
            app_commands.Choice(
                name=f"{truncate_string(value=f'{track.title} - {track.author}', max_length=100, suffix='')}",
                value=track.uri,
            )
            for track in tracks
        ]
        return songs
    async def embedx(self, text):
        """Deprecated: Use layoutx instead. Create a standard layout with text"""
        return self.layoutx(text)
    
    def layoutx(self, text, emoji=""):
        """Create a standard Component V2 layout with text"""
        from discord.ui import LayoutView, Container, TextDisplay
        view = LayoutView()
        container = Container()
        content = f"{emoji} {text}" if emoji else text
        container.add_item(TextDisplay(content))
        view.add_item(container)
        return view

    def format_duration(self, seconds):
        """Format duration in seconds to HH:MM:SS"""
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    async def ensure_voice(self, ctx):
        """Ensure bot is in voice channel and properly configured"""
        if not ctx.voice_client:
            if ctx.author.voice:
                vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player, self_deaf=True)
                vc.ctx = ctx
                # Initialize necessary attributes
              #  if not hasattr(vc, "loop"):
                   # setattr(vc, "loop", False)
                if not hasattr(vc.queue, "history"):
                    setattr(vc.queue, "history", [])
                # Set up initial volume
                await vc.set_volume(100)
                # Save channel data for 24/7 reconnection
                save_ctx(ctx.guild.id, ctx.author.voice.channel.id, ctx.channel.id)
                return vc
            raise commands.CheckFailure("You need to be in a voice channel first.")
        return ctx.voice_client

    @commands.hybrid_command(name="connect", with_app_command=True, description="Connects to your voice channel.", aliases=["join"])
    @commands.guild_only()
    async def connect(self, ctx):
        try:
            print(f"Connect command called by {ctx.author} in guild {ctx.guild.id}")
            if not ctx.author.voice:
                print("User not in voice channel")
                return await ctx.send(view=self.layoutx("You are not connected to a voice channel."))
            if ctx.voice_client:
                print("Bot already connected")
                return await ctx.send(view=self.layoutx("I am already connected to a voice channel."))

            print(f"Connecting to {ctx.author.voice.channel.name}")
            vc = await self.ensure_voice(ctx)
            print(f"Connected successfully, saving context")
            save_ctx(ctx.guild.id, ctx.author.voice.channel.id, ctx.channel.id)
         #   await ctx.send(embed=await self.embedx(f"Connected to {ctx.author.voice.channel.name}"))
            await ctx.message.add_reaction(tick)
            print("Connect command completed")

        except Exception as e:
            logger.error(f"Error in connect command: {e}")
            print(f"Error in connect command: {e}")

    @commands.hybrid_command(name="disconnect", description="Disconnects from your voice channel.", aliases=["leave"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def disconnect(self, ctx):
        try:
            # Check if 247 mode is enabled
            data = await db3.find_one({"guild_id": ctx.guild.id})
            is_247_enabled = data.get("247", False) if data else False
            
            if is_247_enabled:
                view = self.layoutx("❌ Cannot disconnect! 24/7 mode is enabled. Use `+247` to disable it first.")
                return await ctx.send(view=view)
            
            await ctx.voice_client.disconnect()
          #  await ctx.send(embed=await self.embedx(f"Disconnected from {ctx.author.voice.channel.name}"))
          #  save_ctx(ctx.guild.id, None, None)
            await ctx.message.add_reaction(tick)
        except Exception as e:
            logger.error(f"Error in disconnect command: {e}")

    @commands.hybrid_command(name="play", description="Play a song or playlist from various sources")
    @app_commands.autocomplete(query=query_autocomplete)
    @app_commands.describe(query="The song or playlist you want to play")
    @commands.guild_only()
    @check_voice()
    async def play(self, ctx, *, query: str):
        """Enhanced play command with better source handling and playlist support"""
        await ctx.defer()
        try:
            vc = await self.ensure_voice(ctx)
            try:
                # Enhanced search with multiple source support
                # Optimized source retrieval with caching
                cache_key = f"source:{ctx.guild.id}"
                source = await cache_manager.get('source', cache_key)
                if source is None:
                    datax = await db5.find_one({"guild_id": ctx.guild.id})
                    source = datax.get("source", "ytmsearch") if datax else "ytmsearch"
                    await cache_manager.set('source', cache_key, source, ttl=600)  # Cache for 10 minutes
                tracks: wavelink.Search = await wavelink.Playable.search(query, source=source)
                if not tracks:
                    logger.warning(f"No tracks found for query: {query}")
                    return await ctx.send(view=self.layoutx("No tracks were found with the given query."))
                if vc.paused:
                    return await ctx.send(view=self.layoutx("Resume The Player First"))
                if isinstance(tracks, wavelink.Playlist):
                    tracks.track_extras(ctx=ctx)
                    added = await vc.queue.put_wait(tracks)
                    await ctx.send(view=self.layoutx(f"Added playlist **{tracks.name}** with {added} tracks to queue"))
                else:
                    track = tracks[0]
                    await vc.queue.put_wait(track)
                    await ctx.send(view=self.layoutx(f"Added [{track.title}]({track.uri}) to queue"))

                if not vc.playing:
                    await vc.play(vc.queue.get())
                    vc.ctx = ctx

            except wavelink.LavalinkException as e:
                logger.error(f"Lavalink error during track search: {e}")
                await ctx.send(view=self.layoutx("The music server is having trouble processing your request. Please try again."))
            except TimeoutError:
                logger.error("Track search timed out")
                await ctx.send(view=self.layoutx("The search request timed out. Please try again."))

        except Exception as e:
            logger.error(f"Error in play command: {e}")
            await ctx.send(view=self.layoutx("An error occurred while processing your request."))

    @commands.hybrid_command(name="pause", with_app_command=True, description="Pauses the current song.")  
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def pause(self, ctx):
        await ctx.defer()
        try:
            vc: wavelink.Player = ctx.voice_client
            if not vc.current:
              await ctx.send(view=self.layoutx(f"There is no song playing."))
              return
            if vc.pause(False):          
              await vc.pause(True)
              await ctx.send(view=self.layoutx("Paused the current song."))
              await ctx.message.add_reaction(tick)
            else:
              await ctx.send(view=self.layoutx("Player is already paused."))
        except Exception as e:
            logger.error(f"Error in pause command: {e}")

    @commands.hybrid_command(name="resume", with_app_command=True, description="Resumes the current song.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def resume(self, ctx):
      await ctx.defer()
      try:
        vc: wavelink.Player = ctx.voice_client        
        if vc.pause(True):
          await vc.pause(False)
          await ctx.send(view=self.layoutx("Resumed the current song."))
          await ctx.message.add_reaction(tick)
        else:
          await ctx.send(view=self.layoutx("Player is already resumed."))
      except Exception as e:
        logger.error(f"Error in resume command: {e}")

    @commands.hybrid_command(name="skip", description="Skips the current song")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @same_voice()
    async def skip(self, ctx):
        """Skip current track with proper error handling"""
        await ctx.defer()
        try:
            vc: wavelink.Player = ctx.voice_client
            if not vc:
                return await ctx.send(view=self.layoutx("I am not connected to a voice channel."))

            if not vc.playing:
                return await ctx.send(view=self.layoutx("Nothing is currently playing."))

            # Save current track to history before skipping            
            await vc.skip(force = True)
            await ctx.send(view=self.layoutx("Skipped the current song."))
            await ctx.message.add_reaction(tick)

        except Exception as e:
            logger.error(f"Error in skip command: {e}")
            await ctx.send(view=self.layoutx("An error occurred while skipping."))

    @commands.hybrid_command(name="seek", with_app_command=True, description="Seeks to a specific time in the current song.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def seek(self, ctx, *, position: str):
      await ctx.defer()
      try:
        vc: wavelink.Player = ctx.voice_client
        if not vc.playing:
          await ctx.send(view=self.layoutx("I am not playing anything."))
          return
        num = FormatTime(position)
        if num is None:
          await ctx.send(view=self.layoutx("Input position. Exmaple: 1:30."))
          return
        if num > vc.current.length:
            return await ctx.send(view=self.layoutx("Input position is greater than the song length."))
        await vc.seek(num)
        await ctx.send(view=self.layoutx(f"Seeked to {position}")) 
        await ctx.message.add_reaction(tick)
      except Exception as e:
        logger.error(f"Error in seek command: {e}")

    @commands.hybrid_command(name="rewind", with_app_command=True, description="Input a amount that you to rewind to. Exmaple: 1:30")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def rewind(self, ctx, *, position: str = "10"):
       await ctx.defer()
       try:
         vc: wavelink.Player = ctx.voice_client
         if not vc.playing:
           await ctx.send(view=self.layoutx("I am not playing anything."))
           return
         num = FormatTime(position)
         if num is None:
           await ctx.send(view=self.layoutx("Input position. Exmaple: 1:30."))
           return
         if num > vc.current.length:
            return await ctx.send(view=self.layoutx("Input position is greater than the song length."))
         await vc.seek(vc.position - num)
         await ctx.send(view=self.layoutx(f"Rewinded to {position}"))
         await ctx.message.add_reaction(tick)

       except Exception as e:
        logger.error(f"Error in rewind command: {e}")

    @commands.hybrid_command(name="volume", description="Changes the volume of the player.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def volume(self, ctx, volume: int):
        await ctx.defer()
        try:
            vc: wavelink.Player = ctx.voice_client
            if not vc.playing:
                await ctx.send(view=self.layoutx("I am not playing anything."))
                return
            if volume > 150:
                await ctx.send(view=self.layoutx("Volume cannot be greater than 150."))
                return
            if volume < 0:
                await ctx.send(view=self.layoutx("Volume cannot be less than 0."))
                return
            await vc.set_volume(volume)
            await ctx.send(view=self.layoutx(f"Set the volume to {volume}%."))
            await ctx.message.add_reaction(tick)
        except Exception as e:
            logger.error(f"Error in volume command: {e}")

    @commands.hybrid_command(name="nowplaying", description="Shows detailed information about the current track")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @same_voice()
    async def nowplaying(self, ctx):
        """Display beautiful visualization of the currently playing track"""
        await ctx.defer()
        try:
            vc: wavelink.Player = ctx.voice_client
            if not vc or not vc.current:
                return await ctx.send(view=self.layoutx("Nothing is currently playing."))

            # Get track info
            track = vc.current
            position = vc.position

            try:
                # Generate visualization
                card = NowPlayingCard()
                image = await card.generate(
                    title=track.title,
                    artist=track.author,
                    thumbnail_url=track.artwork if track.artwork else cf.bot_icon,
                    position=position,
                    duration=track.length
                )

                if image:
                    # Save image temporarily
                    buffer = BytesIO()
                    image.save(buffer, 'PNG')
                    buffer.seek(0)

                    # Send as Discord file with Container
                    file = discord.File(buffer, 'nowplaying.png')
                    layout = LayoutView()
                    container = Container()
                    container.add_item(TextDisplay("## Now Playing"))
                    container.add_item(Separator())
                    layout.add_item(container)
                    await ctx.send(file=file, view=layout)
                else:
                    raise Exception("Failed to generate visualization")

            except Exception as vis_error:
                logger.error(f"Visualization error: {vis_error}")
                # Fallback to simple layout if visualization fails
                from discord.ui import Thumbnail, Section
                layout = LayoutView()
                container = Container()
                container.add_item(TextDisplay("## Now Playing"))
                container.add_item(Separator())
                thumb = Thumbnail(track.artwork if track.artwork else cf.bot_icon)
                section = Section(TextDisplay(f"**[{track.title}]({track.uri})**\nby {track.author}"), accessory=thumb)
                container.add_item(section)
                layout.add_item(container)
                await ctx.send(view=layout)

        except Exception as e:
            logger.error(f"Error in nowplaying command: {e}")
            await ctx.send(view=self.layoutx("An error occurred while fetching track information."))

    @commands.hybrid_command(name="recover", description="Attempts to recover the player from errors")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def recover(self, ctx):
        """Advanced error recovery for the music player"""
        await ctx.defer()
        try:
            if ctx.voice_client:
                # Store current state
                current_channel = ctx.voice_client.channel
                current_volume = getattr(ctx.voice_client, 'volume', 100)
                was_playing = ctx.voice_client.playing
                current_track = getattr(ctx.voice_client, 'current', None)

                # Disconnect and cleanup
                await ctx.voice_client.disconnect()
                await asyncio.sleep(1)  # Brief delay for cleanup

                # Reconnect with fresh player
                vc: wavelink.Player = await current_channel.connect(cls=wavelink.Player, self_deaf=True)

                # Restore state
                await vc.set_volume(current_volume)
                if was_playing and current_track:
                    await vc.play(current_track)

                vc.ctx = ctx
                save_ctx(ctx.guild.id, current_channel.id, ctx.channel.id)

                await ctx.send(view=self.layoutx("Successfully recovered the music player."))
            else:
                await ctx.send(view=self.layoutx("No active player to recover."))

        except Exception as e:
            logger.error(f"Error in recover command: {e}")
            await ctx.send(view=self.layoutx("Failed to recover the player. Please try again or rejoin manually."))

    @commands.hybrid_command(name="replay", with_app_command=True, description="Replays the current song.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def replay(self, ctx):
      await ctx.defer()
      try:
        vc: wavelink.Player = ctx.voice_client
        if not vc.playing:
          await ctx.send(view=self.layoutx("I am not playing anything."))
          return
        if vc.playing:
          await vc.seek(0)
          await ctx.send(view=self.layoutx("Replayed the current song."))
          await ctx.message.add_reaction(tick)
        else:
          await ctx.send(view=self.layoutx("Player is already replayed."))
      except Exception as e:
        logger.error(f"Error in replay command: {e}")

    @commands.hybrid_command(name="loop", with_app_command=True, description="Loops the current song.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def loop(self, ctx):
      await ctx.defer()
      try:
        vc = await self.ensure_voice(ctx)
        # Note: LoopView handles its own defer if needed, but we defer here for the command itself
        # if ctx.interaction: await ctx.defer() # Already added above

        view = LoopView(self.bot, vc)
        msg = await ctx.send(view=view)
        view.msg = msg
          
        

      except Exception as e:
        logger.error(f"Error in loop command: {e}")

    @commands.hybrid_command(name="queue",aliases=['q'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @same_voice()
    async def queue(self, ctx):
        await ctx.defer()
        try:
            vc: wavelink.Player = ctx.voice_client
            if not vc:
                return await ctx.send(view=self.layoutx("I am not playing anything."))

            if not vc.current:
                return await ctx.send(view=self.layoutx("Nothing is currently playing."))

            # Queue entries
            if vc.queue:
                entries = []
                total_duration = 0
                for i, track in enumerate(vc.queue, start=1):
                    duration = self.format_duration(track.length)
                    total_duration += track.length
                    entries.append(
                        f"`{i}.` [{track.title}]({track.uri}) - `{duration}`"
                    )

                paginator = Paginator(
                    ctx=ctx,
                    source=DescriptionEmbedPaginator(
                        entries=entries,
                        title=f"Queue - {len(vc.queue)} tracks",
                        description=f"Total Duration: `{self.format_duration(total_duration)}`",
                        per_page=10
                    )
                )
                await paginator.paginate()
            else:
                await ctx.send(view=self.layoutx("No tracks in queue."))

        except Exception as e:
            logger.error(f"Error in queue command: {e}")
            await ctx.send(view=self.layoutx("An error occurred while fetching the queue."))

    @commands.hybrid_command(name="queueclear", description="Clears the queue.", aliases=["qclear", "clearqueue"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def queueclear(self, ctx):
        await ctx.defer()
        try:
            vc: wavelink.Player = ctx.voice_client
            if not vc.playing:
                await ctx.send(view=self.layoutx("I am not playing anything."))
                return
            if vc.queue:
                vc.queue.clear()
                await ctx.send(view=self.layoutx("Cleared the queue."))
                await ctx.message.add_reaction(tick)
            else:
                await ctx.send(view=self.layoutx("The queue is already empty."))
        except Exception as e:
            logger.error(f"Error in queueclear command: {e}")

    @commands.hybrid_command(name="forward", with_app_command=True, description="Input a amount that you to forward to. Exmaple: 1:30")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def forward(self, ctx, *, position: str = "10"):
       await ctx.defer()
       try:
         vc: wavelink.Player = ctx.voice_client
         if not vc.playing:
           await ctx.send(view=self.layoutx("I am not playing anything."))
           return
         num = FormatTime(position)
         if num is None:
           await ctx.send(view=self.layoutx("Input position. Exmaple: 1:30."))
           return
         if num > vc.current.length:
            return await ctx.send(view=self.layoutx("Input position is greater than the song length.")) 
         await vc.seek(vc.position + num)
         await ctx.send(view=self.layoutx(f"Forwarded to {position}"))
         await ctx.message.add_reaction(tick)
       except Exception as e:
        logger.error(f"Error in forward command: {e}")

    @commands.hybrid_command(name="autoplay", with_app_command=True, description="Toggles autoplay on/off.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def autoplay(self, ctx):
        await ctx.defer()
        try:
            vc: wavelink.Player = ctx.voice_client
            enabled: wavelink.Player = wavelink.AutoPlayMode.enabled
            disabled: wavelink.Player = wavelink.AutoPlayMode.disabled
            if not vc.playing:
                await ctx.send(view=self.layoutx("I am not playing anything."))
                return
            if vc.autoplay == enabled:
                vc.autoplay = disabled
                await ctx.send(view=self.layoutx("Autoplay is now disabled."))
                await ctx.message.add_reaction(tick)
            else:
                vc.autoplay = enabled
                await ctx.send(view=self.layoutx("Autoplay is now enabled."))
                await ctx.message.add_reaction(tick)
        except Exception as e:
            logger.error(f"Error in autoplay command: {e}")

    @commands.hybrid_command(name="shuffle", with_app_command=True, description="Shuffles the queue.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def shuffle(self, ctx):
        await ctx.defer()
        try:
            vc: wavelink.Player = ctx.voice_client
            if not vc.playing:
                await ctx.send(view=self.layoutx("I am not playing anything."))
                return
            if vc.queue:
                vc.queue.shuffle()
                await ctx.send(view=self.layoutx("Shuffled the queue."))
                await ctx.message.add_reaction(tick)
            else:
                await ctx.send(view=self.layoutx("The queue is already empty."))
        except Exception as e:
            logger.error(f"Error in shuffle command: {e}")

    @commands.hybrid_command(name="search")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @same_voice()
    async def search(self, ctx, *, query: str):
        await ctx.defer()
        try:
            vc: wavelink.Player= ctx.voice_client
            if not vc:
                vc = await self.ensure_voice(ctx)

            
            tracks = await wavelink.Playable.search(query)

            if not tracks:
                return await ctx.send(view=self.layoutx("No results found for your search."))

            # Create search results view
            search_results = [
                f"{i+1}. [{track.title}]({track.uri}) - `{self.format_duration(track.length)}`"
                for i, track in enumerate(tracks[:10])
            ]

            search_view = SearchView(ctx, tracks=tracks[:10])
            layout = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"## Search Results for: {query}"))
            container.add_item(Separator())
            from discord.ui import Thumbnail, Section
            thumb = Thumbnail(cf.bot_icon)
            section = Section(TextDisplay("\n".join(search_results)), accessory=thumb)
            container.add_item(section)
            
            search_view_container = Container()
            search_view_row = ActionRow()
            for item in search_view.children:
                search_view_row.add_item(item)
            search_view_container.add_item(search_view_row)
            layout.add_item(container)
            layout.add_item(search_view_container)
            
            await ctx.send(view=layout)
            search_view.message = await ctx.original_response()
            await search_view.wait()

            if search_view.values:
                added_tracks = []
                for value in search_view.values:
                    track = tracks[int(value.split(". ")[0]) - 1]
                    await vc.queue.put_wait(track)
                    added_tracks.append(f"[{track.title}]({track.uri})")

                from discord.ui import Thumbnail, Section
                layout = LayoutView()
                container = Container()
                container.add_item(TextDisplay("## Added to Queue"))
                container.add_item(Separator())
                thumb = Thumbnail(cf.bot_icon)
                section = Section(TextDisplay("\n".join(added_tracks)), accessory=thumb)
                container.add_item(section)
                layout.add_item(container)
                await ctx.send(view=layout)

                if not vc.current:
                    await vc.play(vc.queue.get())
                    vc.ctx = ctx

        except Exception as e:
            logger.error(f"Error in search command: {e}")
            await ctx.send(view=self.layoutx("An error occurred while searching."))

    @commands.hybrid_command(name="skipto", aliases=["st"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def skipto(self, ctx, index: int):
        try:
            vc = await self.ensure_voice(ctx)
            if index > len(ctx.voice_client.queue):
                return await ctx.send(view=self.layoutx("Invalid index"))
            position_number = int(index - 1)
            for _ in range(position_number):
                vc.queue.get()

         #   await vc.stop()
          #  await vc.skip(force=True)
            await asyncio.gather(
               # vc.stop(),
                vc.skip(force=True), 
                ctx.message.add_reaction(tick)
            
            )

            

        except Exception as e:
            logger.error(f"Error in skipto command: {e}")
    


    @commands.hybrid_command(name="moveto", with_app_command=True, description="Moves the bot to a different voice channel.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def moveto(self, ctx, *, channel: discord.VoiceChannel):
        try:
            vc: wavelink.Player = ctx.voice_client
            await vc.move_to(channel)
            await ctx.send(view=self.layoutx(f"Moved to {channel.name}"))
            await ctx.message.add_reaction(tick)
        except Exception as e:
            logger.error(f"Error in moveto command: {e}")

    @commands.hybrid_command(name="history", with_app_command=True, description="Shows the history of the current song.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def history(self, ctx):
        try:
            vc: wavelink.Player = ctx.voice_client
            if vc.queue.history:
                queue = vc.queue.history
                entries = [(
                    f"`{i+1}.` [{track.title}]({track.uri}) - [{track.author}](https://discord.gg/argomusic)")for i, track in enumerate(queue)]
                paginator = Paginator(ctx=ctx,source=DescriptionEmbedPaginator(
                    entries=entries,
                    title=None,
                    description="",
                    thumbnail=None,
                    author = "Recent Played Songs History", 
                    author_icon=cf.bot_icon,
                     per_page=10)
                                  )
                await paginator.paginate()
            else:
                await ctx.send(view=self.layoutx("The history is empty."))

        except Exception as e:
            logger.error(f"Error in history command: {e}")

    @commands.hybrid_command(name="forcefix", with_app_command=True, description="Forcefully fixes the bot's voice issues. ")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def forcefix(self, ctx):
        try:
            vc: wavelink.Player = ctx.voice_client
            if not vc:
                vc = await self.ensure_voice(ctx)
            await vc.disconnect()
            await ctx.send(view=self.layoutx("Forcefully disconnected from the voice channel."))
            await ctx.message.add_reaction(tick)

        except Exception as e:
            logger.error(f"Error in forcefix command: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Handle voice state updates for better user experience"""
        player = member
        data = await db3.find_one({"guild_id": player.guild.id})
        if not data:
           return

        # If 24/7 mode is enabled, don't disconnect the bot
        if data.get("247", False):
           return
        if member == self.bot.user and not after.channel:
            # Bot was disconnected
            if before.channel:
                save_ctx(before.channel.guild.id, None, None)

        elif member != self.bot.user:
            if before.channel and self.bot.user in before.channel.members:
                # Check if bot is alone in voice channel
                if len([m for m in before.channel.members if not m.bot]) == 0:
                    # No human users left in the voice channel
                    vc = before.channel.guild.voice_client
                    if vc:
                        await vc.disconnect()
                       # await self.save_ctx(before.channel.guild.id, None, None)

    def __del__(self):
        """Cleanup database connection on cog unload"""
        if hasattr(self, 'db'):
          self.db.close()

async def setup(bot):
    await bot.add_cog(Music(bot))