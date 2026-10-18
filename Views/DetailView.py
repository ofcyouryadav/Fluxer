import discord, os, wavelink, json
from discord.ext import commands
from discord.ui import LayoutView, Container, ActionRow, Button, Select, Separator, TextDisplay
from Events.TrackEvents import *
from Views.MultiQueueView import MultiQueueSelect
from Commands.MusicPresets import PresetManager
import random

tick = "<a:melodic_check:1307006796497551370>"
cross = "<a:melodic_cross:1307006642633572482>"

class DetailView(LayoutView):
    def __init__(self, ctx, player):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.player = player
        self.queue = []
        self.current = None
        self.message = None
        self.color = 0x2f3136
        self.filters = wavelink.Filters()
        self.preset_manager = PresetManager()
        self.build_view()
    
    def create_ephemeral_view(self, message):
        """
        Create a standalone LayoutView for ephemeral button responses.
        Returns a fresh LayoutView instance (not attached to self) to avoid nesting.
        """
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(message))
        view.add_item(container)
        return view

    def build_view(self):
        self.clear_items()
        container = Container()
        
        container.add_item(TextDisplay("## Music Player Controls"))
        container.add_item(Separator())
        
        # Queue select dropdown if queue has songs
        if len(self.player.queue) >= 1:
            select_row1 = ActionRow()
            queue_select = MultiQueueSelect(self.ctx, self.player)
            select_row1.add_item(queue_select)
            container.add_item(select_row1)
        
        # Preset select dropdown
        select_row2 = ActionRow()
        preset_options = [
            discord.SelectOption(
                label=preset.name,
                description=preset.description,
                value=name
            ) for name, preset in self.preset_manager.presets.items()
        ]
        
        preset_select = Select(
            placeholder="Choose a music preset...",
            min_values=1,
            max_values=1,
            options=preset_options,
            custom_id="preset_select"
        )
        
        async def preset_callback(interaction: discord.Interaction):
            vc: wavelink.Player = interaction.guild.voice_client
            if not vc or not vc.playing:
                return await interaction.response.send_message(
                    view=self.create_ephemeral_view("Nothing is playing right now."),
                    ephemeral=True
                )
            preset_name = preset_select.values[0]
            preset = self.preset_manager.get_preset(preset_name)
            if preset:
                await preset.apply(vc)
                await interaction.response.send_message(
                    view=self.create_ephemeral_view(f"{tick} Applied the {preset.name} preset"),
                    ephemeral=True
                )
        
        preset_select.callback = preset_callback
        select_row2.add_item(preset_select)
        container.add_item(select_row2)
        
        container.add_item(Separator())
        
        # Row 1: Previous, Stop, Pause, Skip, Autoplay
        row1 = ActionRow()
        
        prev_btn = Button(emoji="<:melodic_rewind:1191621745413734491>", style=discord.ButtonStyle.grey)
        async def prev_callback(interaction: discord.Interaction):
            if not await self.check_voice_channel(interaction):
                return
            vc: wavelink.Player = self.ctx.voice_client
            if not vc:
                return await interaction.response.send_message(view=self.create_ephemeral_view("I am not connected to a voice channel."), ephemeral=True)
            if not vc.playing:
                return await interaction.response.send_message(view=self.create_ephemeral_view("There is nothing playing right now."), ephemeral=True)
            if vc.queue.history:
                await vc.play(vc.queue.history[0])
                await interaction.response.send_message(view=self.create_ephemeral_view(f"{tick} Played the previous song"), ephemeral=True)
                vc.ctx = self.ctx
                self.stop()
        prev_btn.callback = prev_callback
        row1.add_item(prev_btn)
        
        stop_btn = Button(emoji="<:melodic_stop:1191621781329555588>", style=discord.ButtonStyle.danger)
        async def stop_callback(interaction: discord.Interaction):
            if not await self.check_voice_channel(interaction):
                return
            vc: wavelink.Player = self.ctx.voice_client
            if not vc:
                return await interaction.response.send_message(view=self.create_ephemeral_view("I am not connected to a voice channel."), ephemeral=True)
            if not vc.playing:
                return await interaction.response.send_message(view=self.create_ephemeral_view("There is nothing playing right now."), ephemeral=True)
            await vc.stop()
            await interaction.response.send_message(view=self.create_ephemeral_view(f"{tick} Stopped the player"), ephemeral=True)
            vc.ctx = self.ctx
            self.stop()
        stop_btn.callback = stop_callback
        row1.add_item(stop_btn)
        
        pause_btn = Button(style=discord.ButtonStyle.grey, emoji="<:Melodic_Pause:1191621639260086343>")
        async def pause_callback(interaction: discord.Interaction):
            if not await self.check_voice_channel(interaction):
                return
            vc: wavelink.Player = self.ctx.voice_client
            if not vc:
                return await interaction.response.send_message(view=self.create_ephemeral_view("I am not connected to a voice channel."), ephemeral=True)
            if not vc.playing:
                return await interaction.response.send_message(view=self.create_ephemeral_view("There is nothing playing right now."), ephemeral=True)
            if vc.paused:
                await vc.pause(False)
                await interaction.response.send_message(view=self.create_ephemeral_view(f"{tick} Resumed the player"), ephemeral=True)
            else:
                await vc.pause(True)
                await interaction.response.send_message(view=self.create_ephemeral_view(f"{tick} Paused the player"), ephemeral=True)
            vc.ctx = self.ctx
        pause_btn.callback = pause_callback
        row1.add_item(pause_btn)
        
        skip_btn = Button(emoji="<:melodic_skip:1191626987912044605>", style=discord.ButtonStyle.grey)
        async def skip_callback(interaction: discord.Interaction):
            if not await self.check_voice_channel(interaction):
                return
            vc: wavelink.Player = self.ctx.voice_client
            if not vc:
                return await interaction.response.send_message(view=self.create_ephemeral_view("I am not connected to a voice channel."), ephemeral=True)
            if not vc.playing:
                return await interaction.response.send_message(view=self.create_ephemeral_view("There is nothing playing right now."), ephemeral=True)
            await vc.skip(force=True)
            await interaction.response.send_message(view=self.create_ephemeral_view(f"{tick} Skipped to next song"), ephemeral=True)
            vc.ctx = self.ctx
            self.stop()
        skip_btn.callback = skip_callback
        row1.add_item(skip_btn)
        
        autoplay_btn = Button(style=discord.ButtonStyle.green, emoji="<:melodic_autoplay:1191786277645856820>")
        async def autoplay_callback(interaction: discord.Interaction):
            if not await self.check_voice_channel(interaction):
                return
            vc: wavelink.Player = self.ctx.voice_client
            if not vc:
                return await interaction.response.send_message(view=self.create_ephemeral_view("I am not connected to a voice channel."), ephemeral=True)
            if not vc.playing:
                return await interaction.response.send_message(view=self.create_ephemeral_view("There is nothing playing right now."), ephemeral=True)
            if vc.autoplay == wavelink.AutoPlayMode.enabled:
                vc.autoplay = wavelink.AutoPlayMode.disabled
                await interaction.response.send_message(view=self.create_ephemeral_view(f"{tick} Disabled autoplay"), ephemeral=True)
            else:
                vc.autoplay = wavelink.AutoPlayMode.enabled
                await interaction.response.send_message(view=self.create_ephemeral_view(f"{tick} Enabled autoplay"), ephemeral=True)
            vc.ctx = self.ctx
        autoplay_btn.callback = autoplay_callback
        row1.add_item(autoplay_btn)
        
        container.add_item(row1)
        
        # Row 2: Shuffle, Loop, Bass, Volume Down, Volume Up
        row2 = ActionRow()
        
        shuffle_btn = Button(style=discord.ButtonStyle.grey, emoji="<:melofic_shuffle:1191628252108824596>")
        async def shuffle_callback(interaction: discord.Interaction):
            if not await self.check_voice_channel(interaction):
                return
            vc: wavelink.Player = self.ctx.voice_client
            if not vc:
                return await interaction.response.send_message(view=self.create_ephemeral_view("I am not connected to a voice channel."), ephemeral=True)
            if not vc.playing:
                return await interaction.response.send_message(view=self.create_ephemeral_view("There is nothing playing right now."), ephemeral=True)
            if not vc.queue:
                return await interaction.response.send_message(view=self.create_ephemeral_view("There is nothing in the queue."), ephemeral=True)
            random.shuffle(vc.queue._queue)
            await interaction.response.send_message(view=self.create_ephemeral_view(f"{tick} Shuffled the queue"), ephemeral=True)
            vc.ctx = self.ctx
        shuffle_btn.callback = shuffle_callback
        row2.add_item(shuffle_btn)
        
        loop_btn = Button(style=discord.ButtonStyle.grey, emoji="<:melodic_loop:1191785460037603359>")
        async def loop_callback(interaction: discord.Interaction):
            if not await self.check_voice_channel(interaction):
                return
            vc: wavelink.Player = self.ctx.voice_client
            if not vc:
                return await interaction.response.send_message(view=self.create_ephemeral_view("I am not connected to a voice channel."), ephemeral=True)
            if not vc.playing:
                return await interaction.response.send_message(view=self.create_ephemeral_view("There is nothing playing right now."), ephemeral=True)
            if vc.loop:
                setattr(vc, "loop", False)
                await interaction.response.send_message(view=self.create_ephemeral_view(f"{tick} Disabled loop"), ephemeral=True)
            else:
                setattr(vc, "loop", True)
                await interaction.response.send_message(view=self.create_ephemeral_view(f"{tick} Enabled loop"), ephemeral=True)
            vc.ctx = self.ctx
        loop_btn.callback = loop_callback
        row2.add_item(loop_btn)
        
        bass_btn = Button(style=discord.ButtonStyle.grey, emoji="<:melodic_bass:1315392694559166464>")
        async def bass_callback(interaction: discord.Interaction):
            if not await self.check_voice_channel(interaction):
                return
            vc: wavelink.Player = self.ctx.voice_client
            if not vc:
                return await interaction.response.send_message(view=self.create_ephemeral_view("I am not connected to a voice channel."), ephemeral=True)
            if not vc.playing:
                return await interaction.response.send_message(view=self.create_ephemeral_view("There is nothing playing right now."), ephemeral=True)
            if not hasattr(vc, "bass_boost"):
                setattr(vc, "bass_boost", False)
            if vc.bass_boost:
                self.filters.equalizer.reset()
                await vc.set_filters(self.filters)
                setattr(vc, "bass_boost", False)
                await interaction.response.send_message(view=self.create_ephemeral_view(f"{tick} Disabled bass boost"), ephemeral=True)
            else:
                self.filters.equalizer.set(0, 0.3)
                self.filters.equalizer.set(1, 0.3)
                await vc.set_filters(self.filters)
                setattr(vc, "bass_boost", True)
                await interaction.response.send_message(view=self.create_ephemeral_view(f"{tick} Enabled bass boost"), ephemeral=True)
            vc.ctx = self.ctx
        bass_btn.callback = bass_callback
        row2.add_item(bass_btn)
        
        vol_down_btn = Button(style=discord.ButtonStyle.grey, emoji="<:melodic_volumedown:1191627758607016098>")
        async def vol_down_callback(interaction: discord.Interaction):
            if not await self.check_voice_channel(interaction):
                return
            vc: wavelink.Player = self.ctx.voice_client
            if not vc:
                return await interaction.response.send_message(view=self.create_ephemeral_view("I am not connected to a voice channel."), ephemeral=True)
            if not vc.playing:
                return await interaction.response.send_message(view=self.create_ephemeral_view("There is nothing playing right now."), ephemeral=True)
            if vc.volume == 0:
                return await interaction.response.send_message(view=self.create_ephemeral_view(f"{cross} Volume is already at 0%"), ephemeral=True)
            new_volume = max(0, vc.volume - 10)
            await vc.set_volume(new_volume)
            await interaction.response.send_message(view=self.create_ephemeral_view(f"{tick} Volume set to {new_volume}%"), ephemeral=True)
            vc.ctx = self.ctx
        vol_down_btn.callback = vol_down_callback
        row2.add_item(vol_down_btn)
        
        vol_up_btn = Button(style=discord.ButtonStyle.grey, emoji="<:melodic_volumeup:1191627699240837240>")
        async def vol_up_callback(interaction: discord.Interaction):
            if not await self.check_voice_channel(interaction):
                return
            vc: wavelink.Player = self.ctx.voice_client
            if not vc:
                return await interaction.response.send_message(view=self.create_ephemeral_view("I am not connected to a voice channel."), ephemeral=True)
            if not vc.playing:
                return await interaction.response.send_message(view=self.create_ephemeral_view("There is nothing playing right now."), ephemeral=True)
            if vc.volume >= 150:
                return await interaction.response.send_message(view=self.create_ephemeral_view(f"{cross} Volume is already at maximum (150%)"), ephemeral=True)
            new_volume = min(150, vc.volume + 10)
            await vc.set_volume(new_volume)
            await interaction.response.send_message(view=self.create_ephemeral_view(f"{tick} Volume set to {new_volume}%"), ephemeral=True)
            vc.ctx = self.ctx
        vol_up_btn.callback = vol_up_callback
        row2.add_item(vol_up_btn)
        
        container.add_item(row2)
        
        # Row 3: Speed, Reset Filters, Delete
        row3 = ActionRow()
        
        speed_btn = Button(style=discord.ButtonStyle.grey, emoji="<:melodic_speed:1315392692277739520>")
        async def speed_callback(interaction: discord.Interaction):
            if not await self.check_voice_channel(interaction):
                return
            vc: wavelink.Player = self.ctx.voice_client
            if not vc:
                return await interaction.response.send_message(view=self.create_ephemeral_view("I am not connected to a voice channel."), ephemeral=True)
            if not vc.playing:
                return await interaction.response.send_message(view=self.create_ephemeral_view("There is nothing playing right now."), ephemeral=True)
            if not hasattr(vc, "speed_multiplier"):
                setattr(vc, "speed_multiplier", 1.0)
            speeds = [0.5, 1.0, 1.5, 2.0]
            current_index = speeds.index(vc.speed_multiplier)
            next_index = (current_index + 1) % len(speeds)
            new_speed = speeds[next_index]
            self.filters.timescale.set(speed=new_speed)
            await vc.set_filters(self.filters)
            setattr(vc, "speed_multiplier", new_speed)
            await interaction.response.send_message(view=self.create_ephemeral_view(f"{tick} Playback speed set to {new_speed}x"), ephemeral=True)
            vc.ctx = self.ctx
        speed_btn.callback = speed_callback
        row3.add_item(speed_btn)
        
        reset_btn = Button(style=discord.ButtonStyle.grey, emoji="<a:Arziyaan_Music:1442615980365709624>")
        async def reset_callback(interaction: discord.Interaction):
            if not await self.check_voice_channel(interaction):
                return
            vc: wavelink.Player = self.ctx.voice_client
            if not vc:
                return await interaction.response.send_message(view=self.create_ephemeral_view("I am not connected to a voice channel."), ephemeral=True)
            if not vc.playing:
                return await interaction.response.send_message(view=self.create_ephemeral_view("There is nothing playing right now."), ephemeral=True)
            self.filters = wavelink.Filters()
            await vc.set_filters(self.filters)
            setattr(vc, "current_preset", None)
            setattr(vc, "bass_boost", False)
            setattr(vc, "speed_multiplier", 1.0)
            await interaction.response.send_message(view=self.create_ephemeral_view(f"{tick} Reset all audio filters to default"), ephemeral=True)
            vc.ctx = self.ctx
        reset_btn.callback = reset_callback
        row3.add_item(reset_btn)
        
        delete_btn = Button(style=discord.ButtonStyle.danger, emoji="<:melodic_delete:1307016346956988447>")
        async def delete_callback(interaction: discord.Interaction):
            await interaction.message.delete()
        delete_btn.callback = delete_callback
        row3.add_item(delete_btn)
        
        container.add_item(row3)
        
        self.add_item(container)

    async def check_voice_channel(self, interaction: discord.Interaction) -> bool:
        if any(i.id == interaction.user.id for i in self.ctx.guild.me.voice.channel.members):
            return True
        await interaction.response.send_message("You must be in the voice channel to use these controls.", ephemeral=True)
        return False
