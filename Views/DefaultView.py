import discord , os, wavelink, json
from discord.ext import commands
from Events.TrackEvents import *
from Views.MultiQueueView import MultiQueueSelect
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

import random

tick = "<a:melodic_check:1307006796497551370>"

cross = "<a:melodic_cross:1307006642633572482>"

# MongoDB Configuration for Favorites
MONGO_URI = "mongodb+srv://insane:op5@cluster0.5qyw6.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
mongo_client = AsyncIOMotorClient(MONGO_URI)
dbx = mongo_client["ArgoBotV2"]
playlist_db = dbx["PlaylistDB"]












from discord.ui import LayoutView, Container, TextDisplay, ActionRow, Separator, Select, Button
from discord import ButtonStyle

def create_message_view(text, color=0x2f3136):
    """Helper function to create a simple message view"""
    view = LayoutView()
    container = Container()
    container.add_item(TextDisplay(f"## {text}"))
    view.add_item(container)
    return view

class DefaultView(LayoutView):
  def __init__(self, ctx, player):
      super().__init__(timeout=None)
      self.ctx = ctx
      self.player = player
      self.queue = []
      self.current = None
      self.message = None
      self.color = 0x2f3136 
      self.queue_select = None
      if len(player.queue) >= 1:
        self.queue_select = MultiQueueSelect(ctx, player)

  def set_layout(self, layout_view: LayoutView):
      """Integrate layout containers from another LayoutView"""
      self.clear_items()
      
      # Get the main container from the layout view
      if layout_view.children:
          main_container = layout_view.children[0]
      else:
          main_container = Container()
      
      # Add separator before controls
      main_container.add_item(Separator())
      
      # Create control buttons
      button_row = ActionRow()
      
      # Previous button
      prev_btn = Button(emoji="<:melodic_rewind:1191621745413734491>", style=ButtonStyle.grey, custom_id="prev_btn")
      async def prev_callback(interaction: discord.Interaction):
          if not await self.interaction_check(interaction):
              return
          vc = self.ctx.voice_client
          if not vc:
              return await interaction.response.send_message(view=create_message_view("I am not connected to a voice channel."), ephemeral=True)
          if not vc.playing:
              return await interaction.response.send_message(view=create_message_view("There is nothing playing right now."), ephemeral=True)
          if vc.queue.history:
              await vc.play(vc.queue.history[0])
              await interaction.response.send_message(view=create_message_view(f"{tick} Played The Previous Song"), ephemeral=True)
              vc.ctx = self.ctx
              self.stop()
      prev_btn.callback = prev_callback
      button_row.add_item(prev_btn)
      
      # Stop button
      stop_btn = Button(emoji="<:melodic_stop:1191621781329555588>", style=ButtonStyle.danger, custom_id="stop_btn")
      async def stop_callback(interaction: discord.Interaction):
          if not await self.interaction_check(interaction):
              return
          vc = self.ctx.voice_client
          if not vc:
              return await interaction.response.send_message(view=create_message_view("I am not connected to a voice channel."), ephemeral=True)
          if not vc.playing:
              return await interaction.response.send_message(view=create_message_view("There is nothing playing right now."), ephemeral=True)
          await vc.stop()
          await interaction.response.send_message(view=create_message_view(f"{tick} Stopped The Player"), ephemeral=True)
          vc.ctx = self.ctx
          self.stop()
      stop_btn.callback = stop_callback
      button_row.add_item(stop_btn)
      
      # Pause/Resume button
      pause_btn = Button(emoji="<:Melodic_Pause:1191621639260086343>", style=ButtonStyle.grey, custom_id="pause_btn")
      async def pause_callback(interaction: discord.Interaction):
          if not await self.interaction_check(interaction):
              return
          vc = self.ctx.voice_client
          if not vc:
              return await interaction.response.send_message(view=create_message_view("I am not connected to a voice channel."), ephemeral=True)
          if not vc.playing:
              return await interaction.response.send_message(view=create_message_view("There is nothing playing right now."), ephemeral=True)
          if vc.paused:
              await vc.pause(False)
              await interaction.response.send_message(view=create_message_view(f"{tick} Resumed The Player"), ephemeral=True)
          else:
              await vc.pause(True)
              await interaction.response.send_message(view=create_message_view(f"{tick} Paused The Player"), ephemeral=True)
          vc.ctx = self.ctx
      pause_btn.callback = pause_callback
      button_row.add_item(pause_btn)
      
      # Skip button
      skip_btn = Button(emoji="<:melodic_skip:1191626987912044605>", style=ButtonStyle.grey, custom_id="skip_btn")
      async def skip_callback(interaction: discord.Interaction):
          if not await self.interaction_check(interaction):
              return
          vc = self.ctx.voice_client
          if not vc:
              return await interaction.response.send_message(view=create_message_view("I am not connected to a voice channel."), ephemeral=True)
          if not vc.playing:
              return await interaction.response.send_message(view=create_message_view("There is nothing playing right now."), ephemeral=True)
          await vc.skip(force=True)
          await interaction.response.send_message(view=create_message_view(f"{tick} Played The Next Song"), ephemeral=True)
          vc.ctx = self.ctx
          self.stop()
      skip_btn.callback = skip_callback
      button_row.add_item(skip_btn)
      
      # Like button
      like_btn = Button(emoji="<:white_heart:1443366161873113108>", style=ButtonStyle.red, custom_id="like_btn")
      async def like_callback(interaction: discord.Interaction):
          if not await self.interaction_check(interaction):
              return
          vc = self.ctx.voice_client
          if not vc:
              return await interaction.response.send_message(view=create_message_view("I am not connected to a voice channel."), ephemeral=True)
          if not vc.current:
              return await interaction.response.send_message(view=create_message_view("There is nothing playing right now."), ephemeral=True)
          
          try:
              track = vc.current
              favorites_name = "Favorites"
              
              # Check if Favorites playlist exists
              existing = await playlist_db.find_one({
                  "user_id": interaction.user.id,
                  "name": favorites_name
              })
              
              # Create Favorites playlist if it doesn't exist
              if not existing:
                  await playlist_db.insert_one({
                      "user_id": interaction.user.id,
                      "name": favorites_name,
                      "tracks": [],
                      "created_at": datetime.utcnow()
                  })
              
              # Check if track is already in favorites
              existing_playlist = await playlist_db.find_one({
                  "user_id": interaction.user.id,
                  "name": favorites_name,
                  "tracks.uri": track.uri
              })
              
              if existing_playlist:
                  # Track already liked, remove it (unlike)
                  await playlist_db.update_one(
                      {"user_id": interaction.user.id, "name": favorites_name},
                      {
                          "$pull": {"tracks": {"uri": track.uri}},
                          "$set": {"updated_at": datetime.utcnow()}
                      }
                  )
                  await interaction.response.send_message(
                      view=create_message_view(f" Removed '{track.title}' from Favorites"), 
                      ephemeral=True
                  )
              else:
                  # Add track to favorites
                  track_data = {
                      "title": track.title,
                      "uri": track.uri,
                      "author": track.author,
                      "length": track.length
                  }
                  await playlist_db.update_one(
                      {"user_id": interaction.user.id, "name": favorites_name},
                      {
                          "$push": {"tracks": track_data},
                          "$set": {"updated_at": datetime.utcnow()}
                      }
                  )
                  await interaction.response.send_message(
                      view=create_message_view(f" Added '{track.title}' to Favorites"), 
                      ephemeral=True
                  )
          except Exception as e:
              await interaction.response.send_message(
                  view=create_message_view(f"{cross} Error saving to favorites: {str(e)}"), 
                  ephemeral=True
              )
      like_btn.callback = like_callback
      button_row.add_item(like_btn)
      
      # Add the button row to container
      main_container.add_item(button_row)
      
      # Second row for autoplay if needed
      button_row2 = ActionRow()
      
      # Autoplay button
      autoplay_btn = Button(emoji="<:melodic_autoplay:1191786277645856820>", style=ButtonStyle.green, custom_id="autoplay_btn")
      async def autoplay_callback(interaction: discord.Interaction):
          if not await self.interaction_check(interaction):
              return
          vc = self.ctx.voice_client
          if not vc:
              return await interaction.response.send_message(view=create_message_view("I am not connected to a voice channel."), ephemeral=True)
          if not vc.playing:
              return await interaction.response.send_message(view=create_message_view("There is nothing playing right now."), ephemeral=True)
          if vc.autoplay == wavelink.AutoPlayMode.enabled:
              vc.autoplay = wavelink.AutoPlayMode.disabled
              await interaction.response.send_message(view=create_message_view(f"{tick} Disabled Autoplay"), ephemeral=True)
          else:
              vc.autoplay = wavelink.AutoPlayMode.enabled
              await interaction.response.send_message(view=create_message_view(f"{tick} Enabled Autoplay"), ephemeral=True)
          vc.ctx = self.ctx
      autoplay_btn.callback = autoplay_callback
      button_row2.add_item(autoplay_btn)
      
      main_container.add_item(button_row2)
      
      # Add queue select if exists
      if self.queue_select:
          select_row = ActionRow()
          select_row.add_item(self.queue_select)
          main_container.add_item(select_row)
      
      # Add the main container to this view
      self.add_item(main_container)
      
      # Add any other containers that were in the layout
      if layout_view.children:
          for item in layout_view.children[1:]:
              self.add_item(item)
  




  async def interaction_check(self, interaction: discord.Interaction) -> bool:
      c = False
      for i in self.ctx.guild.me.voice.channel.members:
          if i.id == interaction.user.id:
              c = True
              break
      if c:
          return True
      else:
          await interaction.response.send_message(f"Um, Looks like you are not in the voice channel .", ephemeral=True)
          return False
      vc: wavelink.Player = self.ctx.voice_client
      if not vc:
        return await interaction.response.send_message(view=create_message_view("I am not connected to a voice channel."), ephemeral=True)
