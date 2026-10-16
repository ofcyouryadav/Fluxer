import os
from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
from discord.ui import LayoutView, Container, TextDisplay
import aiohttp, json

# Load environment variables from .env file
load_dotenv()
import wavelink
from discord.gateway import DiscordWebSocket
import asyncio
from discord.http import HTTPClient
from cachetools import TTLCache
import logging
import datetime
import gc
import psutil
import time
import contextlib
import sys
from typing import Set, Optional, Dict, Any
import importlib
from Config.logging_config import setup_logging
from Database.connection import DatabaseConnection
from Database.repositories import (
    PrefixRepository,
    PlaylistRepository,
   # SettingsRepository,
   # IgnoreRepository,
   # SpotifyRepository,
 #   ChannelRepository
)
from Database.utils import initialize_database, check_database_health, db_metrics, cache_manager
from Functions.session_manager import session_manager
from Functions.webhook_logger import webhook_logger
from Config.Config import join_log, leave_log, command_log, exceptt
from discord import app_commands
from motor.motor_asyncio import AsyncIOMotorClient
# Initialize logging with color support
setup_logging()
logger = logging.getLogger('bot')

# In-memory cache with TTL and size limit
command_stats = TTLCache(maxsize=1000, ttl=3600)  # Track command usage for 1 hour

# Default Configuration
DEFAULT_PREFIX = "+"
OWNERS: Set[int] = {1052620216443601076}

# Optimize websocket rate limit
DiscordWebSocket.rate_limit = 110

# Initialize repositories as module-level variables
prefix_repo = PrefixRepository()
playlist_repo = PlaylistRepository()
#settings_repo = SettingsRepository()
#ignore_repo = IgnoreRepository()
#spotify_repo = SpotifyRepository()
#channel_repo = ChannelRepository()
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    logger.error("MONGO_URI environment variable is required. Please set it in your secrets.")
    sys.exit(1)
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["ArgoBotV2"]

Shard_Count = 6

async def get_prefix(bot, message: discord.Message):
    """Get guild-specific prefix with enhanced error handling and caching"""
    if not message.guild:
        return commands.when_mentioned_or(DEFAULT_PREFIX)(bot, message)

    try:
        # Check if user has no-prefix access
        cache_key_noprefix = f"noprefix:{message.author.id}"
        noprefix_data = await cache_manager.get('noprefix', cache_key_noprefix)
        
        if noprefix_data is None:
            data = await db.noprefix.find_one({"noprefix": bot.user.id})
            if data and message.author.id in data.get("user_id", []):
                noprefix_data = True
                await cache_manager.set('noprefix', cache_key_noprefix, True, ttl=3600)
            else:
                noprefix_data = False
                await cache_manager.set('noprefix', cache_key_noprefix, False, ttl=300)
        
        # Get guild prefix from cache or database
        cache_key = f"prefix:{message.guild.id}"
        prefix = await cache_manager.get('prefix', cache_key)

        if prefix is None:
            prefix = await prefix_repo.get_prefix(message.guild.id)
            await cache_manager.set('prefix', cache_key, prefix)

        # Use when_mentioned_or: for no-prefix users, add empty string as second parameter
        if noprefix_data:
            # No-prefix user: mention + prefix + empty string (no prefix needed)
            return commands.when_mentioned_or(prefix, '')(bot, message)
        else:
            # Regular user: mention + prefix
            return commands.when_mentioned_or(prefix)(bot, message)

    except Exception as e:
        logger.error(f"Error in get_prefix for guild {message.guild.id}: {e}")
        return commands.when_mentioned_or(DEFAULT_PREFIX)(bot, message)

class CustomBot(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.voice_states = True
      #  intents.presences = True
        # Make sure guild intents are enabled

        # Initialize repositories and caches before super().__init__
        self._loaded_extensions = set()
        self.prefix_repo = prefix_repo
        self.cache_manager = cache_manager

        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            owner_ids=OWNERS,
            case_insensitive=True,
            strip_after_prefix=True,
            help_command=None,
            shard_count=Shard_Count,
            
            status=discord.Status.idle,
            max_messages=10000,
            chunk_guilds_at_startup=False, 
            sync_commands_debug=True,
            sync_commands=True,
            sync_on_cog_reload=True,
            heartbeat_timeout=60.0,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, replied_user=False
            )
            
        )

        self.session: Optional[aiohttp.ClientSession] = None
        self.start_time = datetime.datetime.now(datetime.UTC)
        self.launch_time = datetime.datetime.now(datetime.UTC)
        self.command_stats = command_stats
        self.wavelink: Optional[wavelink.Node] = None
        self._db_initialized = False
        self.db = db  # MongoDB database instance

        # Add proper command error handling
        self.tree.on_error = self.on_app_command_error

        # Optimize command processing
        self._command_lock = asyncio.Lock()

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle application command errors"""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"This command is on cooldown. Try again in {error.retry_after:.2f}s",
                ephemeral=True
            )
        elif isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                "You don't have permission to use this command.",
                ephemeral=True
            )
        else:
            logger.error(f"App command error: {error}")
            await interaction.response.send_message(
                "An error occurred while executing this command.",
                ephemeral=True
            )

    async def load_extension_safe(self, extension_name: str) -> bool:
        """Safely load an extension with duplicate checking and error handling"""
        try:
            if extension_name in self._loaded_extensions:
                logger.warning(f"Extension {extension_name} is already loaded, skipping.")
                return False

            # Force reload the module to ensure fresh state
            if extension_name in sys.modules:
                importlib.reload(sys.modules[extension_name])

            await self.load_extension(extension_name)
            self._loaded_extensions.add(extension_name)
            logger.info(f"Successfully loaded extension: {extension_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to load extension {extension_name}: {e}")
            return False

    async def setup_hook(self) -> None:
        """Initialize bot with enhanced error handling and cleanup"""
        try:
            # Initialize session using session manager
            self.session = await session_manager.get_session("bot_main")
            
            # Initialize webhook logger
            await webhook_logger.set_session(self.session)

            # Initialize database only once
            if not self._db_initialized:
                db = await DatabaseConnection.get_instance()
                await initialize_database()
                self._db_initialized = True
                logger.info("Database initialized successfully")

            # Load extensions with improved error handling
            successful_loads = []
            failed_loads = []

            # Load jishaku first
            await self.load_extension_safe("jishaku")

            for folder in ["Commands", "Events"]:
                for filename in os.listdir(f"./{folder}"):
                    if filename.endswith(".py"):
                        extension_name = f"{folder}.{filename[:-3]}"
                        if await self.load_extension_safe(extension_name):
                            successful_loads.append(extension_name)
                        else:
                            failed_loads.append(extension_name)

            # Log results
            if successful_loads:
                logger.info(f"Successfully loaded extensions: {', '.join(successful_loads)}")
            if failed_loads:
                logger.warning(f"Failed to load extensions: {', '.join(failed_loads)}")

            # Initialize wavelink node with better error handling and retry logic
            nodes = [wavelink.Node(
                uri="http://lava-v4.ajieblogs.eu.org:80",
                password="https://dsc.gg/ajidevserver",
                inactive_player_timeout=10,
                identifier="Fluxer"
            )]

            retry_count = 0
            max_retries = 3
            while retry_count < max_retries:
                try:
                    await wavelink.Pool.connect(client=self, nodes=nodes)
                    logger.info("Successfully connected to Lavalink node")
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        logger.error(f"Failed to connect to Lavalink after {max_retries} attempts: {e}")
                        break
                    logger.warning(f"Lavalink connection attempt {retry_count} failed: {e}")
                    await asyncio.sleep(5)  # Wait before retry
            
            # Start wavelink health monitoring task
            self.wavelink_health_check.start()

        except Exception as e:
            logger.error(f"Critical error in setup_hook: {e}")
            await self.cleanup()
            raise

    # on shard connect handle with ratelimits
    async def on_shard_connect(self, shard_id: int):
        logger.info(f"Shard {self.shard_id} connected")
        await asyncio.sleep(5)  # Wait for 5 seconds before sending the initial heartbeat
    # on shard disconnect handle with ratelimits
    async def on_shard_disconnect(self, shard_id: int):
        logger.warning(f"Shard {self.shard_id} disconnected")
        await asyncio.sleep(5)  # Wait for 5 seconds before reconnecting
    async def on_shard_ready(self, shard_id: int):
        logger.info(f"Shard {shard_id} is ready")
    async def on_shard_resumed(self, shard_id: int):
        logger.info(f"Shard {shard_id} resumed")
    
        
        
    

    async def cleanup(self) -> None:
        """Cleanup resources with proper error handling"""
        try:
            # Close all sessions using session manager
            await session_manager.cleanup()

            # Close wavelink nodes if they exist
            if hasattr(self, 'wavelink'):
               await wavelink.Pool.close()

            # Clear command stats cache
            self.command_stats.clear()

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    @tasks.loop(hours=6)  # Check every 6 hours
    async def wavelink_health_check(self):
        """Monitor wavelink connection health and reconnect if needed"""
        try:
            nodes = list(wavelink.Pool.nodes.values())
            if not nodes:
                logger.warning("No wavelink nodes found, attempting reconnection...")
                await self.reconnect_wavelink()
                return
            
            for node in nodes:
                # Check if node is connected by checking its status
                if node.status != wavelink.NodeStatus.CONNECTED:
                    logger.warning(f"Wavelink node {node.identifier} is disconnected (status: {node.status}), reconnecting...")
                    await self.reconnect_wavelink()
                    break
        except Exception as e:
            logger.error(f"Error in wavelink health check: {e}")
    
    @wavelink_health_check.before_loop
    async def before_wavelink_health_check(self):
        """Wait for bot to be ready before starting health checks"""
        await self.wait_until_ready()
    
    async def reconnect_wavelink(self):
        """Reconnect to wavelink node with error handling"""
        try:
            # Close existing connections
            await wavelink.Pool.close()
            await asyncio.sleep(2)
            
            # Reconnect with retry logic
            nodes = [wavelink.Node(
                uri="http://lava-v4.ajieblogs.eu.org:80",
                password="https://dsc.gg/ajidevserver",
                inactive_player_timeout=10,
                identifier="Fluxer"
            )]
            
            retry_count = 0
            max_retries = 3
            while retry_count < max_retries:
                try:
                    await wavelink.Pool.connect(client=self, nodes=nodes)
                    logger.info("Successfully reconnected to Lavalink node")
                    return
                except Exception as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        logger.error(f"Failed to reconnect to Lavalink after {max_retries} attempts: {e}")
                        return
                    logger.warning(f"Lavalink reconnection attempt {retry_count} failed: {e}")
                    await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Error in reconnect_wavelink: {e}")

    async def close(self) -> None:
        """Override close to ensure proper cleanup"""
        try:
            await self.cleanup()
            await super().close()
        except Exception as e:
            logger.error(f"Error during bot shutdown: {e}")
            raise

    async def get_bot_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        try:
            return {
                'uptime': (datetime.datetime.now(datetime.UTC) - self.start_time).total_seconds(),
                'guilds': len(self.guilds),
                'users': sum(g.member_count for g in self.guilds),
                'commands_used': len(self.command_stats),
                'latency': round(self.latency * 1000, 2),
                'active_sessions': session_manager.get_active_sessions(),
                'memory_usage': psutil.Process().memory_info().rss / 1024 / 1024  # MB
            }
        except Exception as e:
            logger.error(f"Error getting bot stats: {e}")
            return {}

bot = CustomBot()

@bot.event
async def on_ready() -> None:
    """Handle bot startup with enhanced error handling"""
    try:
        # Skip database initialization if already done
        if not bot._db_initialized:
            if not await initialize_database():
                logger.error("Failed to initialize database")
                return

            # Check database health
            health_status = await check_database_health()
            if not health_status['connection']:
                logger.error("Database health check failed")
                return

        # ASCII Banner
        banner = f"""
\x1b[38;5;199m╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ███████╗██╗     ██╗   ██╗██╗  ██╗███████╗██████╗          ║
║   ██╔════╝██║     ██║   ██║╚██╗██╔╝██╔════╝██╔══██╗         ║
║   █████╗  ██║     ██║   ██║ ╚███╔╝ █████╗  ██████╔╝         ║
║   ██╔══╝  ██║     ██║   ██║ ██╔██╗ ██╔══╝  ██╔══██╗         ║
║   ██║     ███████╗╚██████╔╝██╔╝ ██╗███████╗██║  ██║         ║
║   ╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝         ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  Bot: {bot.user.name:<23} ID: {bot.user.id:<17} ║
║  Version: Discord.py {discord.__version__:<39} ║
║  Shards: {bot.shard_count:<49} ║
║  Servers: {len(bot.guilds):<48} ║
║  Users: {sum(g.member_count for g in bot.guilds if g.member_count):<50} ║
╚══════════════════════════════════════════════════════════════╝\x1b[0m
"""
        print(banner)

        try:
            synced = await bot.tree.sync()
            logger.info(f"\x1b[38;5;46m[OK]\x1b[0m Synced {len(synced)} slash commands globally")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

        # Start monitoring tasks
     #   for task_name, task_coro in [
     #   ("Performance Monitor", log_performance_stats(bot)),
      #  ("Cache Cleanup", cleanup_caches())
     #  ]:
     #  2  try:
           #bot.loop.create_task(task_coro, name=task_name)
       #  except Exception as e:
      #    logger.error(f"Failed to start {task_name}: {e}")
        try:
           #  x = f"/help - {len(bot.guilds)/1000:.3f}k"
           #  await bot.change_presence(status=discord.Status.dnd, activity=discord.Activity(type=discord.ActivityType.custom, name=x)) 
             bot.loop.create_task(update_status(bot))
        except Exception as e:
             print(e)
            
         

    except Exception as e:
        logger.error(f"Error during bot startup: {e}")



@tasks.loop(minutes=5)
async def update_status(bot):
    """Update bot status with enhanced error handling"""
    try:
        x = f"/help - {len(bot.guilds)/1000:.3f}k servers."
        await bot.change_presence(status=discord.Status.dnd, activity=discord.CustomActivity(name=x))

    except Exception as e:
        logger.error(f"Error updating bot status: {e}")
                                  




@bot.event
async def on_command(ctx: commands.Context) -> None:
    """Track command usage statistics with memory management"""
    try:
        cmd_name = ctx.command.qualified_name
        current_time = time.time()

        # Clean up old stats before adding new ones
        if len(command_stats) >= command_stats.maxsize * 0.9:
          command_stats.clear()
          return
            # Clear cache entirely or selectively remove old entries

        if len(command_stats) >= 900:  # 90% of maxsize
            oldest_commands = sorted(command_stats.items(), key=lambda x: x[1])[:100]
            for cmd in oldest_commands:
                command_stats.pop(cmd[0], None)

        command_stats[cmd_name] = current_time
       # await bot.process_commands(ctx)
    except Exception as e:
        logger.error(f"Error tracking command usage: {e}")

#@bot.event
async def on_command_completion(ctx: commands.Context) -> None:
    """Log command completion with enhanced error handling"""
    try:
        webhook_url = os.getenv("COMMAND_WEBHOOK_URL")
        if not webhook_url:
            return

        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay("## Command Used"))
        container.add_item(TextDisplay(
            f"**Command:** {ctx.command}\n"
            f"**User:** {ctx.author} ({ctx.author.id})\n"
            f"**Guild:** {ctx.guild} ({ctx.guild.id})\n"
            f"**Channel:** {ctx.channel} ({ctx.channel.id})"
        ))
        view.add_item(container)

       # async with aiohttp.ClientSession() as session:
          #  webhook = discord.Webhook.from_url(webhook_url, session=session)
            #webhook.send(view=view)
    except Exception as e:
        logger.error(f"Command completion webhook error: {e}")

@bot.event
async def on_message(message: discord.Message):
    """Primary message handler with optimized command processing"""
    if message.author.bot:
        return

    # Process commands only if in a guild and bot has necessary permissions
    if message.guild:
        try:
            me = message.guild.me
            ctx = await bot.get_context(message)
            if all([
                me.guild_permissions.read_messages,
                me.guild_permissions.read_message_history,
                me.guild_permissions.view_channel,
                me.guild_permissions.send_messages
            ]):
                # Check ignored channels with optimized blacklist check
                cache_key = f"blacklist:{bot.user.id}"
                data = await cache_manager.get('blacklist', cache_key)
                if data is None:
                    data = await db.blacklist.find_one({"blacklist": bot.user.id})
                    await cache_manager.set('blacklist', cache_key, data or {}, ttl=300)  # Cache for 5 minutes

                # Check blacklist and notify user
                if data and message.author.id in data.get("user_id", []):
                    # User is blacklisted - send a message if they're trying to use a command
                    if message.content.startswith(tuple(await bot.get_prefix(message))):
                        view = LayoutView()
                        container = Container()
                        container.add_item(TextDisplay("## 🚫 Access Denied"))
                        container.add_item(Separator())
                        container.add_item(TextDisplay("You are currently **blacklisted** from using this bot.\n\nIf you believe this is an error, please contact the bot owner."))
                        view.add_item(container)
                        try:
                            await message.reply(view=view, delete_after=10)
                        except:
                            pass
                    return

                # Process the command with lock to prevent concurrent processing
                async with bot._command_lock:
                    await bot.process_commands(message)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
# 

    

# Environment variables for jishaku
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_FORCE_PAGINATOR"] = "True"
os.environ["JISHAKU_RETAIN"] = "True"

def main():
    """Main entry point with enhanced error handling"""
    try:
        token = os.getenv("DISCORD_BOT_TOKEN")
        if not token:
            logger.error("Bot token not found in environment variables. Please set DISCORD_BOT_TOKEN.")
            sys.exit(1)
        bot.run(token)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
    finally:
        # Ensure cleanup runs even if the bot crashes
        with contextlib.suppress(Exception):
            asyncio.run(bot.close())

async def log_performance_stats(bot: CustomBot) -> None:
    """Monitor and log performance metrics"""
    while True:
        try:
            stats = await bot.get_bot_stats()
            if stats:
                logger.info(
                    f"\x1b[38;5;197m[Performance Stats]\x1b[0m - "
                    f"Uptime: {stats['uptime']:.2f}s, "
                    f"Guilds: {stats['guilds']}, "
                    f"Users: {stats['users']}, "
                    f"Commands Used: {stats['commands_used']}, "
                    f"Latency: {stats['latency']}ms, "
                    f"Memory: {stats.get('memory_usage', 0):.2f}MB, "
                    f"Active Sessions: {stats['active_sessions']}"
                )
            await asyncio.sleep(300)  # Log every 5 minutes
        except Exception as e:
            logger.error(f"Error logging performance stats: {e}")
            await asyncio.sleep(60)

async def cleanup_caches() -> None:
    """Periodic cache cleanup with enhanced memory management"""
    while True:
        try:
            # Perform garbage collection
            gc.collect()

            # Clean expired entries from caches
            await cache_manager.cleanup()
            command_stats.expire()

            # Log memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            logger.info(
                f"\x1b[38;5;197m[Memory Stats]\x1b[0m - "
                f"RSS: {memory_info.rss / 1024 / 1024:.2f}MB, "
                f"VMS: {memory_info.vms / 1024 / 1024:.2f}MB"
            )

            logger.info("\x1b[38;5;197m[Cache]\x1b[0m Cache cleanup completed")
            await asyncio.sleep(1800)  # Run every 30 minutes
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            await asyncio.sleep(200)


if __name__ == "__main__":
    main()