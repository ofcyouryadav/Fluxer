import discord
from discord.ext import commands
import json
from utils.Tools import *
from typing import Optional

color = 0x2f3136


class GuildBlacklist(commands.Cog):
    """Guild blacklist management"""

    def __init__(self, bot):
        self.bot = bot
        self.blacklisted_guilds = []
        self.color = color
        self.load_blacklist()

    def load_blacklist(self):
        try:
            with open('guildbl.json', 'r') as file:
                self.blacklisted_guilds = json.load(file)
                if not isinstance(self.blacklisted_guilds, list):
                    self.blacklisted_guilds = []
        except FileNotFoundError:
            self.blacklisted_guilds = []

    def save_blacklist(self):
        with open('guildbl.json', 'w') as file:
            json.dump(self.blacklisted_guilds, file, indent=4)

    @commands.group(
        name="guildbl",
        help="Add guild in blacklist",
        invoke_without_command=True,
        usage="guildbl <subcommand>"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    async def _guildbl(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @_guildbl.command(name="add", help="Add a guild to the blacklist")
    @commands.is_owner()
    async def add(self, ctx, guild_id: int):
        # Validate guild ID
        if guild_id <= 0:
            await ctx.send("<:Nexus_cross:1144687282176147629> | Invalid guild ID.")
            return
        
        # Reload blacklist to ensure we have the latest state
        self.load_blacklist()
        
        if guild_id in self.blacklisted_guilds:
            await ctx.send("<:Nexus_cross:1144687282176147629> | This guild is already blacklisted.")
            return
        
        self.blacklisted_guilds.append(guild_id)
        self.save_blacklist()
        
        guild = self.bot.get_guild(guild_id)
        guild_name = guild.name if guild else "Unknown"
        await ctx.send(f"<:Nexus_tick:1144687280540369018> | Successfully blacklisted Guild {guild_name} - {guild_id}.")
        
        # Try to leave the guild if we're in it
        if guild:
            try:
                await guild.leave()
            except:
                pass

    @_guildbl.command(name="remove", help="Remove a guild from the blacklist")
    @commands.is_owner()
    async def remove(self, ctx, guild_id: int):
        if guild_id in self.blacklisted_guilds:
            self.blacklisted_guilds.remove(guild_id)
            self.save_blacklist()
            await ctx.send("<:Nexus_tick:1144687280540369018> | Successfully Guild has been removed from the blacklist.")
        else:
            await ctx.send("<:Nexus_cross:1144687282176147629> | This guild is not blacklisted.")

    @_guildbl.command(name="show", help="Show all blacklisted guilds")
    @commands.is_owner()
    async def show(self, ctx):
        self.load_blacklist()
        if self.blacklisted_guilds:
            entries = [
                f"`[{i}]` | `[{guild_id}]`"
                for i, guild_id in enumerate(self.blacklisted_guilds, start=1)
            ]
            paginator = Paginator(
                source=DescriptionEmbedPaginator(
                    entries=entries,
                    description="",
                    title=f"Server Blacklist - {len(self.blacklisted_guilds)}",
                    color=self.color,
                    per_page=10
                ),
                ctx=ctx
            )
            await paginator.paginate()
        else:
            await ctx.send("There are no blacklisted guilds.")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # Reload blacklist to get the latest state
        self.load_blacklist()
        
        if guild.id in self.blacklisted_guilds:
            try:
                await guild.leave()
            except Exception as e:
                print(f"Failed to leave blacklisted guild {guild.id}: {e}")


async def setup(bot):
    await bot.add_cog(GuildBlacklist(bot))
