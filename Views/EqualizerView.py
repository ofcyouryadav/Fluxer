import discord
from discord.ui import LayoutView, Container, ActionRow, Button, Separator, TextDisplay
from Config import Config as cf
import wavelink

def create_eq_response(mode_name):
    """Helper function to create equalizer mode response"""
    view = LayoutView()
    container = Container()
    container.add_item(TextDisplay(f"## Equalizer Mode: {mode_name}"))
    view.add_item(container)
    return view

class EqualizerView(LayoutView):
    def __init__(self, ctx, player):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.player = player
        self.build_view()

    def build_view(self):
        self.clear_items()
        container = Container()
        
        container.add_item(TextDisplay("## Equalizer Settings"))
        container.add_item(Separator())
        container.add_item(TextDisplay("Select a frequency band to adjust:"))
        container.add_item(Separator())
        
        # Row 1: hz25, hz50, hz100, hz160
        row1 = ActionRow()
        
        hz25_btn = Button(label="hz25", style=discord.ButtonStyle.grey)
        async def hz25_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("You cannot interact in this message", ephemeral=True)
            eq: wavelink.Filters = self.player.filters
            eq.equalizer.set(bands=[{"band": 0, "gain": 0.25}])
            await interaction.response.edit_message(view=create_eq_response("HZ25"))
            await self.player.set_filters(eq)
        hz25_btn.callback = hz25_callback
        row1.add_item(hz25_btn)
        
        hz50_btn = Button(label="hz50", style=discord.ButtonStyle.grey)
        async def hz50_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("You cannot interact in this message", ephemeral=True)
            eq: wavelink.Filters = self.player.filters
            eq.equalizer.set(bands=[{"band": 1, "gain": 0.25}])
            await interaction.response.edit_message(view=create_eq_response("HZ50"))
            await self.player.set_filters(eq)
        hz50_btn.callback = hz50_callback
        row1.add_item(hz50_btn)
        
        hz100_btn = Button(label="hz100", style=discord.ButtonStyle.grey)
        async def hz100_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("You cannot interact in this message", ephemeral=True)
            eq: wavelink.Filters = self.player.filters
            eq.equalizer.set(bands=[{"band": 2, "gain": 0.25}])
            await interaction.response.edit_message(view=create_eq_response("HZ100"))
            await self.player.set_filters(eq)
        hz100_btn.callback = hz100_callback
        row1.add_item(hz100_btn)
        
        hz160_btn = Button(label="hz160", style=discord.ButtonStyle.grey)
        async def hz160_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("You cannot interact in this message", ephemeral=True)
            eq: wavelink.Filters = self.player.filters
            eq.equalizer.set(bands=[{"band": 3, "gain": 0.25}])
            await interaction.response.edit_message(view=create_eq_response("HZ160"))
            await self.player.set_filters(eq)
        hz160_btn.callback = hz160_callback
        row1.add_item(hz160_btn)
        
        container.add_item(row1)
        
        # Row 2: hz250, hz400, hz630, hz1k
        row2 = ActionRow()
        
        hz250_btn = Button(label="hz250", style=discord.ButtonStyle.grey)
        async def hz250_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("You cannot interact in this message", ephemeral=True)
            eq: wavelink.Filters = self.player.filters
            eq.equalizer.set(bands=[{"band": 4, "gain": 0.25}])
            await interaction.response.edit_message(view=create_eq_response("HZ250"))
            await self.player.set_filters(eq)
        hz250_btn.callback = hz250_callback
        row2.add_item(hz250_btn)
        
        hz400_btn = Button(label="hz400", style=discord.ButtonStyle.grey)
        async def hz400_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("You cannot interact in this message", ephemeral=True)
            eq: wavelink.Filters = self.player.filters
            eq.equalizer.set(bands=[{"band": 5, "gain": 0.25}])
            await interaction.response.edit_message(view=create_eq_response("HZ400"))
            await self.player.set_filters(eq)
        hz400_btn.callback = hz400_callback
        row2.add_item(hz400_btn)
        
        hz630_btn = Button(label="hz630", style=discord.ButtonStyle.grey)
        async def hz630_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("You cannot interact in this message", ephemeral=True)
            eq: wavelink.Filters = self.player.filters
            eq.equalizer.set(bands=[{"band": 6, "gain": 0.25}])
            await interaction.response.edit_message(view=create_eq_response("HZ630"))
            await self.player.set_filters(eq)
        hz630_btn.callback = hz630_callback
        row2.add_item(hz630_btn)
        
        hz1k_btn = Button(label="hz1k", style=discord.ButtonStyle.grey)
        async def hz1k_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("You cannot interact in this message", ephemeral=True)
            eq: wavelink.Filters = self.player.filters
            eq.equalizer.set(bands=[{"band": 7, "gain": 0.25}])
            await interaction.response.send_message(view=create_eq_response("HZ1K"))
            await self.player.set_filters(eq)
        hz1k_btn.callback = hz1k_callback
        row2.add_item(hz1k_btn)
        
        container.add_item(row2)
        
        # Row 3: hz1_6k, hz2_1k, hz3_2k, hz4_4k
        row3 = ActionRow()
        
        hz1_6k_btn = Button(label="hz1_6k", style=discord.ButtonStyle.grey)
        async def hz1_6k_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("You cannot interact in this message", ephemeral=True)
            eq: wavelink.Filters = self.player.filters
            eq.equalizer.set(bands=[{"band": 8, "gain": 0.25}])
            await interaction.response.edit_message(view=create_eq_response("HZ1_6K"))
            await self.player.set_filters(eq)
        hz1_6k_btn.callback = hz1_6k_callback
        row3.add_item(hz1_6k_btn)
        
        hz2_1k_btn = Button(label="hz2_1k", style=discord.ButtonStyle.grey)
        async def hz2_1k_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("You cannot interact in this message", ephemeral=True)
            eq: wavelink.Filters = self.player.filters
            eq.equalizer.set(bands=[{"band": 9, "gain": 0.25}])
            await interaction.response.edit_message(view=create_eq_response("HZ2_1K"))
            await self.player.set_filters(eq)
        hz2_1k_btn.callback = hz2_1k_callback
        row3.add_item(hz2_1k_btn)
        
        hz3_2k_btn = Button(label="hz3_2k", style=discord.ButtonStyle.grey)
        async def hz3_2k_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("You cannot interact in this message", ephemeral=True)
            eq: wavelink.Filters = self.player.filters
            eq.equalizer.set(bands=[{"band": 10, "gain": 0.25}])
            await interaction.response.edit_message(view=create_eq_response("HZ3_2K"))
            await self.player.set_filters(eq)
        hz3_2k_btn.callback = hz3_2k_callback
        row3.add_item(hz3_2k_btn)
        
        hz4_4k_btn = Button(label="hz4_4k", style=discord.ButtonStyle.grey)
        async def hz4_4k_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("You cannot interact in this message", ephemeral=True)
            eq: wavelink.Filters = self.player.filters
            eq.equalizer.set(bands=[{"band": 11, "gain": 0.25}])
            await interaction.response.edit_message(view=create_eq_response("HZ4_4K"))
            await self.player.set_filters(eq)
        hz4_4k_btn.callback = hz4_4k_callback
        row3.add_item(hz4_4k_btn)
        
        container.add_item(row3)
        
        # Row 4: hz6_6k, hz8_8k, hz10_10k, delete
        row4 = ActionRow()
        
        hz6_6k_btn = Button(label="hz6_6k", style=discord.ButtonStyle.grey)
        async def hz6_6k_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("You cannot interact in this message", ephemeral=True)
            eq: wavelink.Filters = self.player.filters
            eq.equalizer.set(bands=[{"band": 12, "gain": 0.25}])
            await interaction.response.edit_message(view=create_eq_response("HZ6_6K"))
            await self.player.set_filters(eq)
        hz6_6k_btn.callback = hz6_6k_callback
        row4.add_item(hz6_6k_btn)
        
        hz8_8k_btn = Button(label="hz8_8k", style=discord.ButtonStyle.grey)
        async def hz8_8k_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("You cannot interact in this message", ephemeral=True)
            eq: wavelink.Filters = self.player.filters
            eq.equalizer.set(bands=[{"band": 13, "gain": 0.50}])
            await interaction.response.edit_message(view=create_eq_response("HZ8_8K"))
            await self.player.set_filters(eq)
        hz8_8k_btn.callback = hz8_8k_callback
        row4.add_item(hz8_8k_btn)
        
        hz10_10k_btn = Button(label="hz10_10k", style=discord.ButtonStyle.grey)
        async def hz10_10k_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("You cannot interact in this message", ephemeral=True)
            eq: wavelink.Filters = self.player.filters
            eq.equalizer.set(bands=[{"band": 14, "gain": 0.50}])
            await interaction.response.edit_message(view=create_eq_response("HZ10_10K"))
            await self.player.set_filters(eq)
        hz10_10k_btn.callback = hz10_10k_callback
        row4.add_item(hz10_10k_btn)
        
        delete_btn = Button(emoji="<:melodic_delete:1307016346956988447>", style=discord.ButtonStyle.danger)
        async def delete_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("You cannot interact in this message", ephemeral=True)
            eq: wavelink.Filters = self.player.filters
            eq.equalizer.reset()
            await self.player.set_filters(eq)
            await interaction.message.delete()
        delete_btn.callback = delete_callback
        row4.add_item(delete_btn)
        
        container.add_item(row4)
        
        self.add_item(container)
