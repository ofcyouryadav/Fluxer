import discord
from discord.ext import commands
import os
import logging
from typing import Optional, List
from discord.ui import LayoutView, Container, TextDisplay, Separator, ActionRow, Select

logger = logging.getLogger(__name__)

class CogsDropdown(Select):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

        super().__init__(
            placeholder="Select a cog to reload...",
            options=[discord.SelectOption(label="All", description="All the cogs")] +
            [
                discord.SelectOption(label=name, description=cog.description[:50] if cog.description else "No description")
                for name, cog in bot.cogs.items()
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        selected = self.values[0]
        try:
            if selected == "All":
                for file in os.listdir("Commands"):
                    if file.endswith(".py"):
                        await self.bot.reload_extension(f"Commands.{file[:-3]}")
                for file in os.listdir("Events"):
                    if file.endswith(".py"):
                        await self.bot.reload_extension(f"Events.{file[:-3]}")

                await self.bot.reload_extension("jishaku")

            else:
                for file in os.listdir("Commands"):
                    if file.startswith(f"{selected}"):
                        await self.bot.reload_extension(f"Commands.{file[:-3]}")   
                for file in os.listdir("Events"):
                    if file.startswith(f"{selected}"):
                        await self.bot.reload_extension(f"Events.{file[:-3]}")
                if selected == "jishaku":
                    await self.bot.reload_extension("jishaku")

        except Exception as e:
            logger.error(f"Failed to reload cog {selected}: {e}")
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ Unable to reload `{selected}`! Reason: {e}"))
            view.add_item(container)
            return await interaction.response.send_message(view=view, ephemeral=True)

        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay("## Reload Commands"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"✅ Cogs reloaded: **{selected}**"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"Actioned by {interaction.user}"))
        view.add_item(container)
        
        await interaction.response.send_message(view=view, ephemeral=False)

class CogsView(LayoutView):
    def __init__(self, bot, *, timeout: float | None = 180):
        super().__init__(timeout=timeout)
        
        container = Container()
        container.add_item(TextDisplay("## Reload Commands"))
        container.add_item(Separator())
        container.add_item(TextDisplay("**Select the cogs you want to reload.**"))
        
        row = ActionRow()
        row.add_item(CogsDropdown(bot))
        container.add_item(row)
        
        self.add_item(container)