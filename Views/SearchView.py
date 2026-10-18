from __future__ import annotations

import discord, wavelink
from discord.ui import LayoutView, Container, ActionRow, Select, Separator, TextDisplay

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from wavelink import Playable as Track

class SearchView(LayoutView):
    def __init__(self, ctx, tracks: list[Track]) -> None:
        super().__init__(timeout=60)
        self.ctx = ctx
        self.tracks = tracks
        self.response: discord.Message = None
        self.values: list[str] = None
        
        # Build the view using Component V2
        self.build_view()

    def build_view(self):
        self.clear_items()
        container = Container()
        
        container.add_item(TextDisplay("## Search Results"))
        container.add_item(Separator())
        container.add_item(TextDisplay("Select the songs you want to add to the queue:"))
        container.add_item(Separator())
        
        # Add dropdown inside ActionRow
        select_row = ActionRow()
        options = [
            discord.SelectOption(
                label=f"{i}. {track.title[:50]}", 
                description=f"{track.author[:50]} · {track.length}"
            )
            for i, track in enumerate(self.tracks, start=1)
        ]
        
        select = Select(
            placeholder="Select songs...",
            min_values=1,
            max_values=len(self.tracks),
            options=options
        )
        
        async def select_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("You cannot interact in this message", ephemeral=True)
            select.disabled = True
            select.placeholder = "Songs selected!"
            self.values = select.values
            await interaction.response.edit_message(view=self)
            self.stop()
        
        select.callback = select_callback
        select_row.add_item(select)
        container.add_item(select_row)
        
        self.add_item(container)

    async def on_error(self, error, item, interaction):
        return

    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, Container):
                for item in child.children:
                    if isinstance(item, ActionRow):
                        for component in item.children:
                            if hasattr(component, 'disabled'):
                                component.disabled = True
        try:
            await self.response.edit(view=self)
        except:
            pass
