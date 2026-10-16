import discord
from discord.ext import commands
from discord import PermissionOverwrite
from discord.ui import LayoutView, Container, TextDisplay, Separator, ActionRow, Button, MediaGallery
import aiosqlite
from core import Context
from core.Cog import Cog
from core.Cryptora import Cryptora

DATABASE_PATH = 'db/j2c.db'

# Colors
SUCCESS_COLOR = 0x00ff88
ERROR_COLOR = 0xff0033
INFO_COLOR = 0x2f3136

class J2CControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(custom_id="vc_lock", emoji="🔒", style=discord.ButtonStyle.secondary, row=0)
    async def lock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
        
        channel = interaction.user.voice.channel
        await channel.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message(f"🔒 Locked {channel.name}", ephemeral=True)

    @discord.ui.button(custom_id="vc_unlock", emoji="🔓", style=discord.ButtonStyle.secondary, row=0)
    async def unlock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
        
        channel = interaction.user.voice.channel
        await channel.set_permissions(interaction.guild.default_role, connect=None)
        await interaction.response.send_message(f"🔓 Unlocked {channel.name}", ephemeral=True)

    @discord.ui.button(custom_id="vc_hide", emoji="👁️", style=discord.ButtonStyle.secondary, row=0)
    async def hide_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
        
        channel = interaction.user.voice.channel
        await channel.set_permissions(interaction.guild.default_role, view_channel=False)
        await interaction.response.send_message(f"👁️ Hidden {channel.name}", ephemeral=True)

    @discord.ui.button(custom_id="vc_unhide", emoji="👁", style=discord.ButtonStyle.secondary, row=0)
    async def unhide_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
        
        channel = interaction.user.voice.channel
        await channel.set_permissions(interaction.guild.default_role, view_channel=None)
        await interaction.response.send_message(f"👁 Unhidden {channel.name}", ephemeral=True)

    @discord.ui.button(custom_id="vc_limit", emoji="👥", style=discord.ButtonStyle.secondary, row=0)
    async def limit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
        
        modal = LimitModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(custom_id="vc_rename", emoji="✏️", style=discord.ButtonStyle.secondary, row=1)
    async def rename_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
        
        modal = RenameModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(custom_id="vc_bitrate", emoji="<a:Arziyaan_Music:1442615980365709624>", style=discord.ButtonStyle.secondary, row=1)
    async def bitrate_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
        
        modal = BitrateModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(custom_id="vc_region", emoji="🌍", style=discord.ButtonStyle.secondary, row=1)
    async def region_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
        
        await interaction.response.send_message("Region changing is handled automatically by Discord.", ephemeral=True)

    @discord.ui.button(custom_id="vc_claim", emoji="👑", style=discord.ButtonStyle.secondary, row=1)
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
        
        await interaction.response.send_message(f"👑 You claimed {interaction.user.voice.channel.name}", ephemeral=True)

    @discord.ui.button(custom_id="vc_transfer", emoji="↔️", style=discord.ButtonStyle.secondary, row=1)
    async def transfer_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
        
        await interaction.response.send_message("Mention a user to transfer ownership.", ephemeral=True)

    @discord.ui.button(custom_id="vc_kick", emoji="👢", style=discord.ButtonStyle.secondary, row=2)
    async def kick_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
        
        await interaction.response.send_message("Mention a user to kick from voice.", ephemeral=True)

    @discord.ui.button(custom_id="vc_ban", emoji="🚫", style=discord.ButtonStyle.secondary, row=2)
    async def ban_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
        
        await interaction.response.send_message("Mention a user to ban from voice.", ephemeral=True)

    @discord.ui.button(custom_id="vc_unban", emoji="✅", style=discord.ButtonStyle.secondary, row=2)
    async def unban_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
        
        await interaction.response.send_message("Mention a user to unban from voice.", ephemeral=True)


class LimitModal(discord.ui.Modal, title="Set User Limit"):
    limit = discord.ui.TextInput(label="User Limit", placeholder="Enter number (0 for unlimited)", max_length=2)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            limit_value = int(self.limit.value)
            if interaction.user.voice and interaction.user.voice.channel:
                await interaction.user.voice.channel.edit(user_limit=limit_value)
                await interaction.response.send_message(f"Set user limit to {limit_value}", ephemeral=True)
        except:
            await interaction.response.send_message("Invalid limit value", ephemeral=True)


class RenameModal(discord.ui.Modal, title="Rename Channel"):
    name = discord.ui.TextInput(label="Channel Name", placeholder="Enter new name", max_length=100)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.voice and interaction.user.voice.channel:
            await interaction.user.voice.channel.edit(name=self.name.value)
            await interaction.response.send_message(f"Renamed to {self.name.value}", ephemeral=True)


class BitrateModal(discord.ui.Modal, title="Set Bitrate"):
    bitrate = discord.ui.TextInput(label="Bitrate (kbps)", placeholder="8-96 for normal, up to 384 for boosted", max_length=3)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            bitrate_value = int(self.bitrate.value) * 1000
            if interaction.user.voice and interaction.user.voice.channel:
                await interaction.user.voice.channel.edit(bitrate=bitrate_value)
                await interaction.response.send_message(f"Set bitrate to {self.bitrate.value} kbps", ephemeral=True)
        except:
            await interaction.response.send_message("Invalid bitrate value", ephemeral=True)


class JoinToCreate(Cog):
    def __init__(self, bot: Cryptora):
        self.bot = bot
        self.bot.loop.create_task(self.initialize_db())
    
    async def initialize_db(self):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS j2c_config (
                    guild_id INTEGER PRIMARY KEY,
                    enabled INTEGER DEFAULT 0,
                    category_id INTEGER,
                    channel_id INTEGER,
                    control_channel_id INTEGER,
                    panel_message_id INTEGER
                )
            ''')
            await db.commit()
        
        self.bot.add_view(J2CControlView())
        
        # Dictionary to track temporary channels and their owners
        self.temp_channels = {}  # {channel_id: owner_id}
    
    @Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Handle users joining/leaving J2C channels"""
        try:
            # Don't process bot's own state changes
            if member.bot:
                return
            
            guild = member.guild
            j2c_data = await self.get_j2c_config(guild.id)
            
            if not j2c_data.get('enabled'):
                return
            
            j2c_channel_id = j2c_data.get('channel')
            category_id = j2c_data.get('category')
            
            # User joined the J2C channel
            if after.channel and after.channel.id == j2c_channel_id:
                category = guild.get_channel(category_id)
                if not category:
                    return
                
                # Create temporary voice channel for the user
                temp_channel = await guild.create_voice_channel(
                    name=f"{member.display_name}'s Channel",
                    category=category,
                    user_limit=0
                )
                
                # Give the user special permissions
                await temp_channel.set_permissions(
                    member,
                    manage_channels=True,
                    move_members=True,
                    manage_permissions=True
                )
                
                # Track this temp channel
                self.temp_channels[temp_channel.id] = member.id
                
                # Move the user to their new channel
                await member.move_to(temp_channel)
            
            # User left a temporary channel - check if we should delete it
            if before.channel and before.channel.id in self.temp_channels:
                # Check if channel is now empty (no human members)
                human_members = [m for m in before.channel.members if not m.bot]
                
                if len(human_members) == 0:
                    # Channel is empty, delete it
                    try:
                        await before.channel.delete()
                        del self.temp_channels[before.channel.id]
                    except Exception as e:
                        print(f"Error deleting temp channel: {e}")
        
        except Exception as e:
            print(f"Error in J2C voice state update: {e}")
    
    async def get_j2c_config(self, guild_id: int):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute(
                "SELECT enabled, category_id, channel_id, control_channel_id, panel_message_id FROM j2c_config WHERE guild_id = ?",
                (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'enabled': row[0],
                        'category': row[1],
                        'channel': row[2],
                        'controlChannel': row[3],
                        'panelId': row[4]
                    }
                return {}
    
    async def save_j2c_config(self, guild_id: int, data: dict):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                '''INSERT INTO j2c_config (guild_id, enabled, category_id, channel_id, control_channel_id, panel_message_id) 
                   VALUES (?, ?, ?, ?, ?, ?) 
                   ON CONFLICT(guild_id) DO UPDATE SET 
                   enabled=?, category_id=?, channel_id=?, control_channel_id=?, panel_message_id=?''',
                (guild_id, data.get('enabled', 0), data.get('category'), data.get('channel'), 
                 data.get('controlChannel'), data.get('panelId'),
                 data.get('enabled', 0), data.get('category'), data.get('channel'), 
                 data.get('controlChannel'), data.get('panelId'))
            )
            await db.commit()
    
    async def delete_j2c_config(self, guild_id: int):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("DELETE FROM j2c_config WHERE guild_id = ?", (guild_id,))
            await db.commit()

    def create_response(self, title: str, description: str = "", color: int = INFO_COLOR):
        """Helper to create Component V2 responses"""
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## {title}"))
        if description:
            container.add_item(Separator())
            container.add_item(TextDisplay(description))
        view.add_item(container)
        return view

    @commands.group(name="j2c", aliases=["jtc", "jointocreate"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def j2c(self, ctx: Context):
        view = self.create_response(
            "🔗 Join To Create System",
            "`j2c setup` - Setup the system\n"
            "`j2c reset` - Reset the system\n"
            "`j2c config` - Show configuration",
            INFO_COLOR
        )
        await ctx.send(view=view)

    @j2c.command(name="setup")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def setup(self, ctx: Context):
        j2c_data = await self.get_j2c_config(ctx.guild.id)
        
        if j2c_data.get('enabled'):
            view = self.create_response(
                "⚠️ Already Setup",
                "Join To Create System is already setup.",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        loading_view = self.create_response(
            "⏳ Setting Up",
            "Setting up Join To Create System...",
            INFO_COLOR
        )
        loading_msg = await ctx.send(view=loading_view)
        
        try:
            category = await ctx.guild.create_category(name="Voice Channels")
            
            channel = await ctx.guild.create_voice_channel(
                name="Join To Create",
                category=category,
                user_limit=1
            )
            
            control_channel = await ctx.guild.create_text_channel(
                name="j2c-control",
                category=category
            )
            
            await control_channel.set_permissions(
                ctx.guild.default_role,
                send_messages=False
            )
            
            # Create J2C Panel View with buttons inside container
            class J2CPanelView(LayoutView):
                def __init__(self):
                    super().__init__(timeout=None)
                    
                    # Create container
                    container = Container()
                    container.add_item(TextDisplay("## 🔗 Join To Create Panel"))
                    container.add_item(Separator())
                    container.add_item(TextDisplay(
                        "Use the buttons below to control your voice channel."
                    ))
                    container.add_item(Separator())
                    
                    # Add media gallery
                    media_gallery = MediaGallery()
                    media_gallery.add_item(media="https://media.discordapp.net/attachments/1430601251371880481/1431307745574785024/1761320740459.jpg?ex=69252676&is=6923d4f6&hm=3ad4bea25b653a08e93255a767edb13b455b82d57e17af856eae9de54a9566cd&=&format=webp&width=1361&height=778")
                    container.add_item(media_gallery)
                    container.add_item(Separator())
                    
                    # Add button rows inside container (like Help.py pattern)
                    button_row1 = ActionRow()
                    
                    lock_btn = Button(style=discord.ButtonStyle.secondary, emoji="🔒", custom_id="vc_lock")
                    async def lock_callback(interaction: discord.Interaction):
                        if not interaction.user.voice or not interaction.user.voice.channel:
                            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
                        channel = interaction.user.voice.channel
                        await channel.set_permissions(interaction.guild.default_role, connect=False)
                        await interaction.response.send_message(f"🔒 Locked {channel.name}", ephemeral=True)
                    lock_btn.callback = lock_callback
                    button_row1.add_item(lock_btn)
                    
                    unlock_btn = Button(style=discord.ButtonStyle.secondary, emoji="🔓", custom_id="vc_unlock")
                    async def unlock_callback(interaction: discord.Interaction):
                        if not interaction.user.voice or not interaction.user.voice.channel:
                            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
                        channel = interaction.user.voice.channel
                        await channel.set_permissions(interaction.guild.default_role, connect=None)
                        await interaction.response.send_message(f"🔓 Unlocked {channel.name}", ephemeral=True)
                    unlock_btn.callback = unlock_callback
                    button_row1.add_item(unlock_btn)
                    
                    hide_btn = Button(style=discord.ButtonStyle.secondary, emoji="👁️", custom_id="vc_hide")
                    async def hide_callback(interaction: discord.Interaction):
                        if not interaction.user.voice or not interaction.user.voice.channel:
                            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
                        channel = interaction.user.voice.channel
                        await channel.set_permissions(interaction.guild.default_role, view_channel=False)
                        await interaction.response.send_message(f"👁️ Hidden {channel.name}", ephemeral=True)
                    hide_btn.callback = hide_callback
                    button_row1.add_item(hide_btn)
                    
                    unhide_btn = Button(style=discord.ButtonStyle.secondary, emoji="👁", custom_id="vc_unhide")
                    async def unhide_callback(interaction: discord.Interaction):
                        if not interaction.user.voice or not interaction.user.voice.channel:
                            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
                        channel = interaction.user.voice.channel
                        await channel.set_permissions(interaction.guild.default_role, view_channel=None)
                        await interaction.response.send_message(f"👁 Unhidden {channel.name}", ephemeral=True)
                    unhide_btn.callback = unhide_callback
                    button_row1.add_item(unhide_btn)
                    
                    limit_btn = Button(style=discord.ButtonStyle.secondary, emoji="👥", custom_id="vc_limit")
                    async def limit_callback(interaction: discord.Interaction):
                        if not interaction.user.voice or not interaction.user.voice.channel:
                            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
                        modal = LimitModal()
                        await interaction.response.send_modal(modal)
                    limit_btn.callback = limit_callback
                    button_row1.add_item(limit_btn)
                    
                    container.add_item(button_row1)
                    
                    # Second button row
                    button_row2 = ActionRow()
                    
                    rename_btn = Button(style=discord.ButtonStyle.secondary, emoji="✏️", custom_id="vc_rename")
                    async def rename_callback(interaction: discord.Interaction):
                        if not interaction.user.voice or not interaction.user.voice.channel:
                            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
                        modal = RenameModal()
                        await interaction.response.send_modal(modal)
                    rename_btn.callback = rename_callback
                    button_row2.add_item(rename_btn)
                    
                    bitrate_btn = Button(style=discord.ButtonStyle.secondary, emoji="<a:Arziyaan_Music:1442615980365709624>", custom_id="vc_bitrate")
                    async def bitrate_callback(interaction: discord.Interaction):
                        if not interaction.user.voice or not interaction.user.voice.channel:
                            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
                        modal = BitrateModal()
                        await interaction.response.send_modal(modal)
                    bitrate_btn.callback = bitrate_callback
                    button_row2.add_item(bitrate_btn)
                    
                    region_btn = Button(style=discord.ButtonStyle.secondary, emoji="🌍", custom_id="vc_region")
                    async def region_callback(interaction: discord.Interaction):
                        if not interaction.user.voice or not interaction.user.voice.channel:
                            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
                        await interaction.response.send_message("Region changing is handled automatically by Discord.", ephemeral=True)
                    region_btn.callback = region_callback
                    button_row2.add_item(region_btn)
                    
                    claim_btn = Button(style=discord.ButtonStyle.secondary, emoji="👑", custom_id="vc_claim")
                    async def claim_callback(interaction: discord.Interaction):
                        if not interaction.user.voice or not interaction.user.voice.channel:
                            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
                        await interaction.response.send_message(f"👑 You claimed {interaction.user.voice.channel.name}", ephemeral=True)
                    claim_btn.callback = claim_callback
                    button_row2.add_item(claim_btn)
                    
                    transfer_btn = Button(style=discord.ButtonStyle.secondary, emoji="↔️", custom_id="vc_transfer")
                    async def transfer_callback(interaction: discord.Interaction):
                        if not interaction.user.voice or not interaction.user.voice.channel:
                            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
                        await interaction.response.send_message("Mention a user to transfer ownership.", ephemeral=True)
                    transfer_btn.callback = transfer_callback
                    button_row2.add_item(transfer_btn)
                    
                    container.add_item(button_row2)
                    
                    # Third button row
                    button_row3 = ActionRow()
                    
                    kick_btn = Button(style=discord.ButtonStyle.secondary, emoji="👢", custom_id="vc_kick")
                    async def kick_callback(interaction: discord.Interaction):
                        if not interaction.user.voice or not interaction.user.voice.channel:
                            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
                        await interaction.response.send_message("Mention a user to kick from voice.", ephemeral=True)
                    kick_btn.callback = kick_callback
                    button_row3.add_item(kick_btn)
                    
                    ban_btn = Button(style=discord.ButtonStyle.secondary, emoji="🚫", custom_id="vc_ban")
                    async def ban_callback(interaction: discord.Interaction):
                        if not interaction.user.voice or not interaction.user.voice.channel:
                            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
                        await interaction.response.send_message("Mention a user to ban from voice.", ephemeral=True)
                    ban_btn.callback = ban_callback
                    button_row3.add_item(ban_btn)
                    
                    unban_btn = Button(style=discord.ButtonStyle.secondary, emoji="✅", custom_id="vc_unban")
                    async def unban_callback(interaction: discord.Interaction):
                        if not interaction.user.voice or not interaction.user.voice.channel:
                            return await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
                        await interaction.response.send_message("Mention a user to unban from voice.", ephemeral=True)
                    unban_btn.callback = unban_callback
                    button_row3.add_item(unban_btn)
                    
                    container.add_item(button_row3)
                    
                    self.add_item(container)
            
            panel_view_instance = J2CPanelView()
            msg = await control_channel.send(view=panel_view_instance)
            
            await self.save_j2c_config(ctx.guild.id, {
                'enabled': 1,
                'category': category.id,
                'channel': channel.id,
                'controlChannel': control_channel.id,
                'panelId': msg.id
            })
            
            success_view = self.create_response(
                "✅ Setup Complete",
                "Join To Create System has been setup successfully!",
                SUCCESS_COLOR
            )
            await loading_msg.edit(view=success_view)
            
        except Exception as err:
            error_view = self.create_response(
                "❌ Setup Failed",
                f"An error occurred during setup.",
                ERROR_COLOR
            )
            await loading_msg.edit(view=error_view)
            print(f"J2C Setup Error: {err}")

    @j2c.command(name="reset")
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(administrator=True)
    async def reset(self, ctx: Context):
        j2c_data = await self.get_j2c_config(ctx.guild.id)
        
        if not j2c_data.get('enabled'):
            view = self.create_response(
                "⚠️ Not Setup",
                "Join To Create System is not setup.",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        loading_view = self.create_response(
            "⏳ Resetting",
            "Resetting Join To Create System...",
            INFO_COLOR
        )
        loading_msg = await ctx.send(view=loading_view)
        
        category = ctx.guild.get_channel(j2c_data.get('category'))
        channel = ctx.guild.get_channel(j2c_data.get('channel'))
        control_channel = ctx.guild.get_channel(j2c_data.get('controlChannel'))
        
        if category:
            try:
                await category.delete()
            except:
                pass
        
        if channel:
            try:
                await channel.delete()
            except:
                pass
        
        if control_channel:
            try:
                await control_channel.delete()
            except:
                pass
        
        await self.delete_j2c_config(ctx.guild.id)
        
        success_view = self.create_response(
            "✅ Reset Complete",
            "Join To Create System has been reset successfully.",
            SUCCESS_COLOR
        )
        await loading_msg.edit(view=success_view)

    @j2c.command(name="config")
    @commands.has_permissions(administrator=True)
    async def config(self, ctx: Context):
        j2c_data = await self.get_j2c_config(ctx.guild.id)
        
        if not j2c_data.get('enabled'):
            view = self.create_response(
                "⚠️ Not Setup",
                "Join To Create System is not setup.",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        category = ctx.guild.get_channel(j2c_data.get('category'))
        channel = ctx.guild.get_channel(j2c_data.get('channel'))
        control_channel = ctx.guild.get_channel(j2c_data.get('controlChannel'))
        
        category_name = category.name if category else "N/A"
        channel_mention = f"<#{channel.id}>" if channel else "N/A"
        control_mention = f"<#{control_channel.id}>" if control_channel else "N/A"
        
        view = self.create_response(
            "🔗 Join To Create Configuration",
            f"**Category:** {category_name}\n"
            f"**Channel:** {channel_mention}\n"
            f"**Control Channel:** {control_mention}",
            INFO_COLOR
        )
        await ctx.send(view=view)

async def setup(bot: Cryptora):
    await bot.add_cog(JoinToCreate(bot))
