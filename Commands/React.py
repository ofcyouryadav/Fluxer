import json
import discord
from discord.ext import commands
from utils.Tools import *

color = 0x2f3136


class React(commands.Cog):
    """Reaction trigger system"""

    def __init__(self, bot):
        self.bot = bot
        self.reaction_triggers = {}
        self.color = color
        self.load_reaction_triggers()

    def load_reaction_triggers(self):
        try:
            with open('reaction_triggers.json', 'r') as f:
                self.reaction_triggers = json.load(f)
        except FileNotFoundError:
            self.reaction_triggers = {}

    def save_reaction_triggers(self):
        with open('reaction_triggers.json', 'w') as f:
            json.dump(self.reaction_triggers, f, indent=4)

    def is_admin():
        def predicate(ctx):
            return ctx.author.guild_permissions.administrator
        return commands.check(predicate)

    @commands.group(invoke_without_command=True, name="react", help="Manage reaction triggers")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def react(self, ctx):
        await ctx.send("**<:Nexus_cross:1144687282176147629> | Invalid action. Available actions: `remove`, `clear`, `list`, `add`**")

    @react.command(name="add", help="Add a reaction trigger")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def add(self, ctx, trigger, *reactions):
        if len(reactions) > 3:
            await ctx.send("**<:icons_exclamation:1144986614804787310> | You can only add up to 3 emojis to any reaction.**")
            return

        # Store reactions as a list for proper handling
        self.reaction_triggers[trigger] = list(reactions)
        self.save_reaction_triggers()
        reaction_str = " ".join(reactions)
        await ctx.send(f"** <:Nexus_tick:1144687280540369018> | Added reaction trigger for {trigger} with {reaction_str} emoji reaction.**")

    @react.command(name="remove", help="Remove a reaction trigger")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx, *, trigger):
        if trigger in self.reaction_triggers:
            del self.reaction_triggers[trigger]
            self.save_reaction_triggers()
            await ctx.send(f"** <:Nexus_tick:1144687280540369018>  | Removed reaction trigger for {trigger} **")
        else:
            await ctx.send(f"**<:icons_exclamation:1144986614804787310> | No reaction trigger found for '{trigger}'**")

    @react.command(name="clear", help="Clear all reaction triggers")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def clear(self, ctx):
        self.reaction_triggers.clear()
        self.save_reaction_triggers()
        await ctx.send("** <:Nexus_tick:1144687280540369018> | Cleared all reaction triggers**")

    @react.command(name="list", help="List all reaction triggers")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def list(self, ctx, *, view=None):
        if not self.reaction_triggers:
            await ctx.send("**<:icons_exclamation:1144986614804787310> | There are no reaction triggers set**")
        else:
            if view == 'raw':
                await ctx.send(str(self.reaction_triggers))
            else:
                message = "**Current reaction triggers:**\n"
                for trigger, reactions in self.reaction_triggers.items():
                    reaction_str = " ".join(reactions) if isinstance(reactions, list) else reactions
                    message += f"{trigger}: {reaction_str}\n"
                await ctx.send(message)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        for trigger, reactions in self.reaction_triggers.items():
            if trigger.lower() in message.content.lower():
                # Handle both list and string formats for backwards compatibility
                reaction_list = reactions if isinstance(reactions, list) else [reactions]
                for reaction in reaction_list:
                    try:
                        await message.add_reaction(reaction)
                    except:
                        pass


async def setup(bot):
    await bot.add_cog(React(bot))
