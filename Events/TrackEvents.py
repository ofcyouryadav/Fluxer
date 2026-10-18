import discord
import wavelink
import datetime as dt
import os
import asyncio
import logging
from discord.ext import commands, tasks
from discord.ext.commands import Context, Cog
from typing import Optional, Dict
from collections import deque
from Database.repositories import PlaylistRepository
#from Database.repositories.settings_repository import SettingsRepository # Added import
from Database.utils import cache_manager
from Config import Config
from Views.PlayEmbeds import play_embed1, play_embed2, play_embed3, play_embed4, play_embed5
from Views.DetailView import DetailView
from Views.DefaultView import DefaultView
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB Configuration
MONGO_URI = "mongodb+srv://fluxer8585:fluxer8585@fluxer.3izoeeq.mongodb.net/?appName=Fluxer"
mongo_client = AsyncIOMotorClient(MONGO_URI)
dbx = mongo_client["ArgoBotV2"]
db1 = dbx["EmbedDB"]
db2 = dbx["ButtonDB"]
db3 = dbx["247DB"]
db5 = dbx["SourceDB"]
logger = logging.getLogger(__name__)

def format_duration(seconds):
    minutes, seconds = divmod(seconds / 1000, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}" if hours else f"{int(minutes)}:{int(seconds):02d}"

class TrackEvents(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._status_cooldown = 120
        self._last_status_update: Dict[int, dt.datetime] = {}
        self._update_queues: Dict[int, deque] = {}
        self._update_tasks: Dict[int, asyncio.Task] = {}
        self._history_limit = 100
        self._rate_limit_hits = {}
        self._max_queue_size = 5
        self.playlist_repo = PlaylistRepository()
      #  self.settings_repo = SettingsRepository() # Added initialization
        
        logger.info("TrackEvents Cog initialized with enhanced rate limiting")
        
        # Start cleanup task
        self.cleanup_stale_players.start()

    @Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        """Handle track start event with enhanced error handling and style system"""
        try:
            player = payload.player
            if not hasattr(player, 'ctx') or player.ctx is None:
                logger.warning("Context is None in track_start")
                return

            # Initialize queue history if not present
            if not hasattr(player.queue, 'history'):
                setattr(player.queue, 'history', [])

            track = payload.track
            queue_length = len(player.queue)
            artwork = track.artwork if track.artwork else Config.bot_icon

            # Get embed settings (style and buttons) with caching
            guild_id = player.ctx.guild.id
            cache_key = f"embed_settings:{guild_id}"
            settings = None
            
            try:
                # Try cache first
                settings = await cache_manager.get('embed_settings', cache_key)
                
                if settings is None:
                    # Fetch from DB if not in cache
                    async with asyncio.timeout(2.0):
                        settings_doc = await db1.embed.find_one({'guild_id': guild_id})
                        if settings_doc:
                            settings = {
                                'style': settings_doc.get('style', 'default'),
                                'buttons': settings_doc.get('status', True)
                            }
                        else:
                            settings = {'style': 'default', 'buttons': True}
                        
                        # Cache the result
                        await cache_manager.set('embed_settings', cache_key, settings, ttl=300) # 5 min cache
                
                style = settings.get('style', 'default')
                show_buttons = settings.get('buttons', True)
                
            except Exception as e:
                logger.error(f"Error fetching embed settings: {e}")
                style = "default"
                show_buttons = True

            # Map styles to embed functions
            embed_funcs = {
                "default": play_embed1,
                "basic": play_embed2,
                "detailed": play_embed3,
                "dynamic": play_embed4,
                "aesthetic": play_embed5
            }

            try:
                # Get the appropriate layout function or fallback to default
                layout_func = embed_funcs.get(style, play_embed1)
                logger.debug(f"Using layout style: {style} for guild {guild_id}")

                # Generate the layout (returns LayoutView now, not embed)
                layout_view = await layout_func(
                    title=track.title,
                    author=track.author,
                    duration=format_duration(track.length),
                    requester=player.ctx.author.name if hasattr(player.ctx, 'author') else "Unknown",
                    volume=player.volume,
                    queue_length=queue_length,
                    artwork=artwork
                )

            except Exception as e:
                logger.error(f"Error creating layout: {e}")
                # Fallback to simple layout
                from discord.ui import LayoutView, Container, TextDisplay
                layout_view = LayoutView()
                container = Container()
                container.add_item(TextDisplay(f"Now Playing: {track.title}"))
                layout_view.add_item(container)

            # Integrate DefaultView controls into the layout
            view = DefaultView(player.ctx, player)
            view.set_layout(layout_view)

            try:
                # Check for redirect channel
                db_redirect = dbx["PlayingRedirectDB"]
                redirect_data = await db_redirect.find_one({"guild_id": guild_id})
                
                if redirect_data and redirect_data.get("channel_id"):
                    # Send to redirect channel
                    redirect_channel = player.ctx.guild.get_channel(redirect_data["channel_id"])
                    if redirect_channel:
                        msg = await redirect_channel.send(view=view)
                    else:
                        # Fallback to default channel if redirect channel not found
                        msg = await player.ctx.send(view=view)
                else:
                    # Send to default channel (where song was requested)
                    msg = await player.ctx.send(view=view)
                
                player.message = msg

                # Update channel status with timeout
                short_title = track.title[:20] + "..." if len(track.title) > 20 else track.title
                await asyncio.wait_for(
                    self.update_channel_status(player, f"<a:Arziyaan_Music:1442615980365709624> | {short_title}"),
                    timeout=5.0  # 5 second timeout
                )

            except asyncio.TimeoutError:
                logger.warning(f"Channel status update timed out for guild {guild_id}")
            except Exception as e:
                logger.error(f"Error sending message or updating status: {e}")

        except Exception as e:
            logger.error(f"Track start error: {e}", exc_info=True)

    async def update_channel_status(self, player: wavelink.Player, status: str):
        """Queue a channel status update with enhanced rate limiting and timeouts"""
        try:
            if not player or not player.channel:
                return

            guild_id = player.guild.id
            if guild_id not in self._update_queues:
                self._update_queues[guild_id] = deque(maxlen=self._max_queue_size)

            if not self._update_queues[guild_id] or self._update_queues[guild_id][-1][1] != status:
                logger.debug(f"Queueing status update for guild {guild_id}: {status}")
                self._update_queues[guild_id].append((player, status))

                if guild_id not in self._update_tasks or self._update_tasks[guild_id].done():
                    self._update_tasks[guild_id] = asyncio.create_task(
                        self._process_status_queue(guild_id)
                    )

        except Exception as e:
            logger.error(f"Error queueing status update: {e}")

    async def _process_status_queue(self, guild_id: int):
        """Process queued status updates with enhanced error handling"""
        while True:
            try:
                if not self._update_queues[guild_id]:
                    del self._update_queues[guild_id]
                    if guild_id in self._update_tasks:
                        del self._update_tasks[guild_id]
                    if guild_id in self._rate_limit_hits:
                        del self._rate_limit_hits[guild_id]
                    return

                player, status = self._update_queues[guild_id][0]
                now = dt.datetime.now()

                if guild_id in self._last_status_update:
                    elapsed = (now - self._last_status_update[guild_id]).total_seconds()
                    if elapsed < self._status_cooldown:
                        wait_time = min(self._status_cooldown - elapsed, 60)  # Max 60s wait
                        await asyncio.sleep(wait_time)

                try:
                    async with asyncio.timeout(5.0):  # 5 second timeout
                        if player and player.channel:
                            await player.channel.edit(status=status[:32])
                            self._last_status_update[guild_id] = now
                except asyncio.TimeoutError:
                    logger.warning(f"Channel edit timed out for guild {guild_id}")
                    continue
                except discord.HTTPException as e:
                    if e.code == 429:  # Rate limit hit
                        self._rate_limit_hits[guild_id] = self._rate_limit_hits.get(guild_id, 0) + 1
                        retry_after = e.retry_after if hasattr(e, 'retry_after') else 60
                        await asyncio.sleep(min(retry_after, 300))  # Max 5 min wait
                        continue

                self._update_queues[guild_id].popleft()
                await asyncio.sleep(self._status_cooldown)

            except Exception as e:
                logger.error(f"Error in status queue processor: {e}")
                await asyncio.sleep(self._status_cooldown)
    
    @tasks.loop(hours=12)  # Run every 12 hours
    async def cleanup_stale_players(self):
        """Clean up stale player data to prevent memory leaks"""
        try:
            # Clear old update queues
            now = dt.datetime.now()
            to_remove = []
            for guild_id, last_update in self._last_status_update.items():
                if (now - last_update).total_seconds() > 43200:  # 12 hours
                    to_remove.append(guild_id)
            
            for guild_id in to_remove:
                if guild_id in self._update_queues:
                    del self._update_queues[guild_id]
                if guild_id in self._update_tasks:
                    del self._update_tasks[guild_id]
                if guild_id in self._last_status_update:
                    del self._last_status_update[guild_id]
                if guild_id in self._rate_limit_hits:
                    del self._rate_limit_hits[guild_id]
            
            if to_remove:
                logger.info(f"Cleaned up stale data for {len(to_remove)} guilds")
                
        except Exception as e:
            logger.error(f"Error in cleanup_stale_players: {e}")
    
    @cleanup_stale_players.before_loop
    async def before_cleanup_stale_players(self):
        """Wait for bot to be ready before starting cleanup"""
        await self.bot.wait_until_ready()

    @Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        try:
            player = payload.player
            if not player:
                return

            # Clean up previous message (delete now playing message)
            try:
                if hasattr(player, 'message') and player.message:
                    await player.message.delete()
                    player.message = None
            except Exception as e:
                logger.debug(f"Failed to delete message: {e}")

            # Handle track loop
            player: wavelink.Player | None = payload.player
            ctx = payload.player.ctx


            if ctx is None:
                      return 
         #   loop = payload.player.loop
            if not player:
                return
           # if hasattr(player, "loop"):
               # if loop:
                  #  prev_track = player.queue.history[-1]
                #    return await player.play(prev_track) 

            if len(player.queue) == 0:
                # Check if 247 mode is enabled before disconnecting
                guild_id = ctx.guild.id
                data = await db3.find_one({"guild_id": guild_id})
                is_247_enabled = data.get("247", False) if data else False
                
                if not is_247_enabled:
                    from discord.ui import LayoutView, Container, TextDisplay
                    view = LayoutView()
                    container = Container()
                    container.add_item(TextDisplay("The queue has ended. I'll be disconnecting from the voice channel."))
                    view.add_item(container)
                    return await ctx.send(view=view)
                # If 247 is enabled, just return without disconnecting
                return 
            if player is not None:
                if player.queue:
                    await player.play(player.queue.get())
                    return
            try:
                await self.update_channel_status(player, "<a:Arziyaan_Music:1442615980365709624> | Nothing playing")
            except Exception:
                return

        except Exception as e:
            logger.error(f"Track end error: {e}", exc_info=True)

    
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TrackEvents(bot))