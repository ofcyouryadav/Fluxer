from __future__ import annotations
from typing import TYPE_CHECKING
import discord, os, wavelink, json
from discord.ext import commands
from discord.ui import LayoutView, Container, ActionRow, Select, TextDisplay, Separator
from Events.TrackEvents import *
import random

tick = "<a:melodic_yes:1191623575359201391>"
cross = "<a:melodic_cross:1307006642633572482>"
temp_icon = "https://media.discordapp.net/attachments/1317376605647142945/1317505937837396039/2841a42e18acbd5a5c17900195a0b531.webp?ex=675eee85&is=675d9d05&hm=3f8962053419e22fe88d5f27bfab7172914499e81b756649c6f7739b720c0a0b&"

class MultiQueueSelect(Select):
    def __init__(self, ctx, player):
        self.player = player
        self.ctx = ctx
        
        options = []
        # Safely handle queues of any size
        queue_list = list(player.queue)
        for index, track in enumerate(queue_list, start=1):
            if index > 10:
                break
            options.append(discord.SelectOption(label=f"{index}. {track.title[:40]}"))

        # If no options, add a placeholder (Select requires at least 1 option)
        if not options:
            options.append(discord.SelectOption(label="No songs in queue", value="empty", description="The queue is empty"))

        super().__init__(
            placeholder="Select a song." if options[0].value != "empty" else "Queue is empty",
            options=options,
            custom_id="queue_select",
            disabled=len(queue_list) == 0  # Disable if queue is empty
        )

    async def callback(self, interaction: discord.Interaction):
        # Don't do anything if the queue is empty
        if self.values[0] == "empty":
            return await interaction.response.send_message("The queue is empty.", ephemeral=True)
        
        # Check if user is in voice channel
        c = False
        if self.ctx.guild.me.voice and self.ctx.guild.me.voice.channel:
            for i in self.ctx.guild.me.voice.channel.members:
                if i.id == interaction.user.id:
                    c = True
                    break
        if not c:
            return await interaction.response.send_message("Um, Looks like you are not in the voice channel.", ephemeral=True)
        
        position_number = int(self.values[0].split(".")[0]) - 1
        position = position_number
        
        try:
            # Skip to the specified position in the queue
            # Safely skip tracks without going out of bounds
            queue_length = len(list(self.player.queue))
            if position >= queue_length:
                return await interaction.response.send_message(f"Position {position_number + 1} is out of range (queue has {queue_length} songs).", ephemeral=True)
            
            # Remove tracks before the specified position
            for _ in range(position):
                if self.player.queue:
                    self.player.queue.get()
                else:
                    break
            
            # Play the selected track
            await self.player.stop()
            await self.player.skip(True)
        except Exception as e:
            return await interaction.response.send_message(f"Error skipping to song: {str(e)}", ephemeral=True)
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## Skipped To {position_number + 1}th Song"))
        view.add_item(container)
        await interaction.response.send_message(view=view)


class MultiQueueView(LayoutView):
    def __init__(self, ctx, player):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.player = player
        
        container = Container()
        
        container.add_item(TextDisplay("## Queue Selection"))
        container.add_item(Separator())
        
        # Check if queue has songs
        queue_length = len(list(player.queue))
        if queue_length > 0:
            container.add_item(TextDisplay(f"Select a song from the queue to skip to ({queue_length} songs available):"))
        else:
            container.add_item(TextDisplay("The queue is currently empty."))
        
        container.add_item(Separator())
        
        # Add select in ActionRow
        row = ActionRow()
        row.add_item(MultiQueueSelect(ctx, player))
        container.add_item(row)
        
        self.add_item(container)
