
import discord
from discord.ext import commands
import aiosqlite
from utils.Tools import *

class ShowRules(discord.ui.View):
    def __init__(self, author, selected_events):
        super().__init__(timeout=60)
        self.author = author
        self.selected_events = selected_events

    @discord.ui.button(label="Show Rules", style=discord.ButtonStyle.secondary)
    async def show_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("You are not allowed to interact with this button.", ephemeral=True)
            return

        rules = {
            "Anti NSFW link": "__**Anti NSFW Link**__:\n• Takes action if the message contains a NSFW link.\n• Default punishment: Block message (unchangeable)",
            "Anti caps": "__**Anti Caps**__:\n• Takes action if the message contains >70% caps.\n• Messages under 45 characters are bypassed\n• Default punishment: Mute (1 minutes)",
            "Anti link": "__**Anti Link**__:\n• Takes action if the message contains a link.\n• Server invites, Spotify Music and GIF links are bypassed\n• Default punishment: Mute (7 minutes)",
            "Anti invites": "__**Anti Invites**__:\n• Takes action if the message contains a Discord server invite.\n• Invites from the current server are bypassed\n• Default punishment: Mute (12 minutes)",
            "Anti emoji spam": "__**Anti Emoji Spam**__:\n• Takes action if a message contains more than 5 emojis.\n• Default punishment: Mute (1 minute)",
            "Anti mass mention": "__**Anti Mass Mention**__:\n• Takes action if a message contains more than 4 mentions.\n• Default punishment: Mute (3 minutes)",
            "Anti spam": "__**Anti Spam**__:\n• Takes action if more than 5 messages are sent rapidly in a short time.\n• Default punishment: Mute (12 minutes)",
        }

        enabled_rules = "\n\n".join([rules[event] for event in self.selected_events])

        embed = discord.Embed(title="Enabled Automod Rules", description=enabled_rules, color=0x000000)
        embed.set_footer(text="Punishment type of each event is changeable except for Anti NSFW.")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ConfirmDisable(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=30)
        self.author = author
        self.value = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("You are not allowed to interact with this button.", ephemeral=True)
            return
        self.value = True
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("You are not allowed to interact with this button.", ephemeral=True)
            return
        self.value = False
        self.stop()


class Automod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def automod(self, ctx):
        """Automod configuration commands"""
        prefix = ctx.prefix
        embed = discord.Embed(
            title="Automod Commands",
            description=(
                f"**Available Commands:**\n"
                f"`{prefix}automod enable` - Enable automod\n"
                f"`{prefix}automod disable` - Disable automod\n"
                f"`{prefix}automod punishment` - Configure punishments\n"
                f"`{prefix}automod config` - View configuration\n"
                f"`{prefix}automod logging` - Configure logging\n"
                f"`{prefix}automod ignore` - Ignore channels/roles\n"
                f"`{prefix}automod unignore` - Unignore channels/roles"
            ),
            color=0x000000
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Automod(bot))
