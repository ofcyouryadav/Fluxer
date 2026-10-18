import discord
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay
import datetime
from logging import basicConfig, INFO, info 
from typing import Optional
import logging
import time

logger = logging.getLogger(__name__)

tick = "<a:melodic_check:1307006796497551370>"
cross = "<a:melodic_cross:1307006642633572482>"

def create_error_view(message):
    """Helper function to create error message view"""
    view = LayoutView()
    container = Container()
    container.add_item(TextDisplay(message))
    view.add_item(container)
    return view

class ErrorHandlers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  
        self.color = 0x2f3136
        self._error_cache = {}  # Cache for frequent errors
        self._ratelimit_cache = {}  # Cache for rate limits
        self._error_timeout = 300 # Error cache timeout in seconds
        logger.info("\x1b[38;5;197m[Cog]\x1b[0m ErrorHandlers cog initialized with enhanced error caching")

    def _clear_old_cache_entries(self):
        """Clear expired cache entries"""
        current_time = time.time()
        self._error_cache = {
            k: v for k, v in self._error_cache.items() 
            if v.get('timestamp', 0) + self._error_timeout > current_time
        }

    def get_ratelimit(self, message: discord.Message) -> Optional[int]:
        """Returns the ratelimit left using an optimized cache"""
        current_time = datetime.datetime.utcnow().timestamp()

        if message.author.id in self._ratelimit_cache:
            last_time, count = self._ratelimit_cache[message.author.id]

            if current_time - last_time < 60:  # Within 1 minute
                if count > 5:  # More than 5 messages in a minute
                    return int(60 - (current_time - last_time))
                self._ratelimit_cache[message.author.id] = (last_time, count + 1)
                return None

        self._ratelimit_cache[message.author.id] = (current_time, 1)
        return None

    @commands.Cog.listener()
    async def on_interaction_error(self, error):
        if isinstance(error, (commands.CommandNotFound, discord.errors.NotFound)):
            return
        logger.error(f"\x1b[38;5;197m[Interaction Error]\x1b[0m {str(error)}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        try:
            # Clear expired cache entries
            self._clear_old_cache_entries()

            # Fast return for common errors
            if isinstance(error, commands.CommandNotFound):
                return

            # Generate cache key
            error_key = f"{ctx.guild.id}:{type(error).__name__}"

            # Check cache first - store message text, not view
            cached_error = self._error_cache.get(error_key)
            if cached_error and time.time() - cached_error['timestamp'] < self._error_timeout:
                view = create_error_view(cached_error['message'])
                await ctx.reply(view=view)
                return

            # Handle different error types
            if isinstance(error, commands.MissingRequiredArgument):
                error_msg = error.param.name
                message = (
                    f"{cross} You are missing `{error_msg}` argument\n"
                    f"Do it like: `{ctx.command.name} {ctx.command.signature}`"
                )
                self._error_cache[error_key] = {
                    'message': message,
                    'timestamp': time.time()
                }
                view = create_error_view(message)
                await ctx.reply(view=view)
                logger.error(f"\x1b[38;5;197m[Command Error]\x1b[0m Missing required argument: {error_msg}")
                return

            elif isinstance(error, commands.MissingPermissions):
                missing = [perm.replace('_', ' ').replace('guild', 'server').title() 
                          for perm in error.missing_permissions]
                fmt = '{}, and {}'.format(", ".join(missing[:-1]), missing[-1]) if len(missing) > 2 \
                      else ', '.join(missing)
                message = f"{cross} You are missing `{fmt}` permission(s) to run this command"
                self._error_cache[error_key] = {
                    'message': message,
                    'timestamp': time.time()
                }
                view = create_error_view(message)
                await ctx.reply(view=view)
                logger.error(f"\x1b[38;5;197m[Command Error]\x1b[0m Missing permissions: {fmt}")
                return
                

            elif isinstance(error, commands.CommandOnCooldown):
                await ctx.reply(
                    f"{cross} You are on cooldown. Try again in {error.retry_after:.2f}s",
                    delete_after=error.retry_after
                )
                logger.warning(f"\x1b[38;5;197m[Command Error]\x1b[0m Command on cooldown for {ctx.author.id}")
                return

            elif isinstance(error, commands.NotOwner):
                await ctx.reply(f"{cross} Only My Owner Can Use This Command")
                logger.warning(f"\x1b[38;5;197m[Command Error]\x1b[0m Non-owner tried to use owner command: {ctx.author.id}")
                return

            elif isinstance(error, (commands.MemberNotFound, commands.RoleNotFound, 
                                 commands.ChannelNotFound, commands.ChannelNotReadable,
                                 commands.EmojiNotFound)):
                error_type = type(error).__name__[:-8]
                await ctx.reply(f"{cross} {error_type} Not Found")
                logger.error(f"\x1b[38;5;197m[Command Error]\x1b[0m {error_type} not found: {str(error)}")

            elif isinstance(error, commands.BadArgument):
                view = create_error_view(f"{cross} Bad Argument: {str(error)}")
                await ctx.reply(view=view)
                logger.error(f"\x1b[38;5;197m[Command Error]\x1b[0m Bad argument: {str(error)}")

            elif isinstance(error, commands.BadBoolArgument):
                await ctx.reply(f"{cross} Bad Bool Argument: Expected True/False")
                logger.error(f"\x1b[38;5;197m[Command Error]\x1b[0m Bad bool argument from {ctx.author.id}")

            elif isinstance(error, discord.NotFound) or (isinstance(error, commands.CommandInvokeError) and isinstance(error.original, discord.NotFound)):
                # Ignore "Unknown Message" errors (message deleted before bot could act)
                return

            else:
                logger.error(f"\x1b[38;5;197m[Command Error]\x1b[0m Unhandled error: {str(error)}")
                
                return
             #   try:
                 #   await ctx.reply(f"{cross} An unexpected error occurred. Please try again later.")
            #    except:
                #    pass
#
        
        except Exception as e:
            logger.error(f"\x1b[38;5;197m[Error Handler Exception]\x1b[0m {str(e)}")
            return
        return

async def setup(bot):
    await bot.add_cog(ErrorHandlers(bot))