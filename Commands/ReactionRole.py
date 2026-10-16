from __future__ import annotations
import discord
import aiosqlite
import logging
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay, Separator, ActionRow, Button, Modal, TextInput
from typing import Optional
from utils.Tools import *

logging.basicConfig(
    level=logging.INFO,
    format="\x1b[38;5;197m[\x1b[0m%(asctime)s\x1b[38;5;197m]\x1b[0m -> \x1b[38;5;197m%(message)s\x1b[0m",
    datefmt="%H:%M:%S",
)

DATABASE_PATH = 'db/reactionrole.db'

class CreateMessageModal(Modal):
    def __init__(self, cog, channel):
        super().__init__(title="Create Reaction Role Message")
        self.cog = cog
        self.channel = channel
        
        self.title_input = TextInput(
            label="Title",
            placeholder="Enter message title",
            default="Reaction Roles",
            max_length=256,
            required=False
        )
        self.add_item(self.title_input)
        
        self.description_input = TextInput(
            label="Description",
            placeholder="React to get your roles!",
            style=discord.TextStyle.paragraph,
            max_length=2000,
            required=False
        )
        self.add_item(self.description_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        title = self.title_input.value or "Reaction Roles"
        description = self.description_input.value or "React to get your roles!"
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## {title}"))
        container.add_item(Separator())
        container.add_item(TextDisplay(description))
        container.add_item(Separator())
        container.add_item(TextDisplay("-# React below to get roles"))
        
        view.add_item(container)
        msg = await self.channel.send(view=view)
        
        # Success response
        success_view = LayoutView()
        success_container = Container()
        
        success_container.add_item(TextDisplay("## ✅ Success"))
        success_container.add_item(Separator())
        success_container.add_item(TextDisplay(
            f"Created reaction role message in {self.channel.name}\n"
            f"**Message ID:** `{msg.id}`\n\n"
            f"Use the panel to add reaction roles."
        ))
        
        success_view.add_item(success_container)
        await interaction.response.send_message(view=success_view, ephemeral=True)


class AddReactionModal(Modal):
    def __init__(self, cog, guild):
        super().__init__(title="Add Reaction Role")
        self.cog = cog
        self.guild = guild
        
        self.message_id_input = TextInput(
            label="Message ID",
            placeholder="Enter the message ID",
            max_length=20,
            required=True
        )
        self.add_item(self.message_id_input)
        
        self.emoji_input = TextInput(
            label="Emoji",
            placeholder="Enter emoji (e.g., 🎮 or :custom_emoji:)",
            max_length=100,
            required=True
        )
        self.add_item(self.emoji_input)
        
        self.role_id_input = TextInput(
            label="Role ID or Name",
            placeholder="Enter role ID or name",
            max_length=100,
            required=True
        )
        self.add_item(self.role_id_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            message_id = int(self.message_id_input.value)
        except ValueError:
            await interaction.response.send_message("❌ Invalid message ID!", ephemeral=True)
            return
        
        emoji = self.emoji_input.value.strip()
        
        # Try to find role
        role = None
        try:
            role_id = int(self.role_id_input.value)
            role = self.guild.get_role(role_id)
        except ValueError:
            # Try by name
            role = discord.utils.get(self.guild.roles, name=self.role_id_input.value)
        
        if not role:
            await interaction.response.send_message("❌ Role not found!", ephemeral=True)
            return
        
        # Check role hierarchy
        if role >= self.guild.me.top_role:
            await interaction.response.send_message(
                f"❌ {role.name} is higher than or equal to my top role!",
                ephemeral=True
            )
            return
        
        # Find message
        message = None
        for channel in self.guild.text_channels:
            try:
                message = await channel.fetch_message(message_id)
                break
            except:
                continue
        
        if not message:
            await interaction.response.send_message("❌ Message not found!", ephemeral=True)
            return
        
        # Add reaction
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            await interaction.response.send_message("❌ Invalid emoji!", ephemeral=True)
            return
        
        # Save to database
        await self.cog.add_reaction_role(
            self.guild.id,
            message.channel.id,
            message_id,
            str(emoji),
            role.id
        )
        
        # Success response
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## ✅ Success"))
        container.add_item(Separator())
        container.add_item(TextDisplay(
            f"Added {emoji} → {role.name}\n"
            f"To message: `{message_id}`"
        ))
        
        view.add_item(container)
        await interaction.response.send_message(view=view, ephemeral=True)


class RemoveReactionModal(Modal):
    def __init__(self, cog, guild):
        super().__init__(title="Remove Reaction Role")
        self.cog = cog
        self.guild = guild
        
        self.message_id_input = TextInput(
            label="Message ID",
            placeholder="Enter the message ID",
            max_length=20,
            required=True
        )
        self.add_item(self.message_id_input)
        
        self.emoji_input = TextInput(
            label="Emoji",
            placeholder="Enter emoji to remove",
            max_length=100,
            required=True
        )
        self.add_item(self.emoji_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            message_id = int(self.message_id_input.value)
        except ValueError:
            await interaction.response.send_message("❌ Invalid message ID!", ephemeral=True)
            return
        
        emoji = self.emoji_input.value.strip()
        
        # Check if exists
        reaction_roles = await self.cog.get_reaction_roles(message_id)
        if str(emoji) not in reaction_roles:
            await interaction.response.send_message(
                f"❌ No reaction role found for {emoji}",
                ephemeral=True
            )
            return
        
        # Remove from database
        await self.cog.remove_reaction_role(message_id, str(emoji))
        
        # Remove reaction from message
        for channel in self.guild.text_channels:
            try:
                message = await channel.fetch_message(message_id)
                await message.clear_reaction(emoji)
                break
            except:
                continue
        
        # Success response
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## ✅ Success"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"Removed {emoji} from message `{message_id}`"))
        
        view.add_item(container)
        await interaction.response.send_message(view=view, ephemeral=True)


class ReactionRolePanel(LayoutView):
    def __init__(self, ctx, cog, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.cog = cog
        self.update_panel()
    
    def update_panel(self):
        self.clear_items()
        
        container = Container()
        
        container.add_item(TextDisplay("## 🎭 Reaction Role Panel"))
        container.add_item(Separator())
        container.add_item(TextDisplay(
            "**Manage reaction roles easily with this panel!**\n\n"
            "**Available Actions:**\n"
            "📝 Create a new reaction role message\n"
            "➕ Add a reaction role to a message\n"
            "➖ Remove a reaction role from a message\n"
            "📋 List all reaction role messages\n"
            "🗑️ Delete all roles from a message"
        ))
        container.add_item(Separator())
        
        # Action buttons
        button_row = ActionRow()
        
        create_btn = Button(style=discord.ButtonStyle.green, label="Create Message", emoji="📝")
        async def create_callback(interaction: discord.Interaction):
            if interaction.user.id != self.ctx.author.id:
                await interaction.response.send_message("❌ This panel is not for you!", ephemeral=True)
                return
            
            # Ask for channel
            view = LayoutView()
            channel_container = Container()
            channel_container.add_item(TextDisplay("Which channel should I send the message to?"))
            channel_container.add_item(TextDisplay(f"-# Reply with the channel mention or ID"))
            view.add_item(channel_container)
            
            await interaction.response.send_message(view=view, ephemeral=True)
            
            def check(m):
                return m.author.id == self.ctx.author.id and m.channel.id == self.ctx.channel.id
            
            try:
                msg = await self.cog.bot.wait_for('message', check=check, timeout=60.0)
                
                # Parse channel
                channel = None
                if msg.channel_mentions:
                    channel = msg.channel_mentions[0]
                else:
                    try:
                        channel_id = int(msg.content.strip('<>#'))
                        channel = self.ctx.guild.get_channel(channel_id)
                    except:
                        pass
                
                if not channel:
                    await self.ctx.send("❌ Invalid channel!", delete_after=5)
                    return
                
                # Show modal
                modal = CreateMessageModal(self.cog, channel)
                await interaction.followup.send("Opening modal...", ephemeral=True)
                await self.ctx.author.send("Please fill out the form:", view=discord.ui.View().add_item(
                    discord.ui.Button(label="Fill Form", custom_id="open_modal")
                ))
                # Note: Discord.py doesn't support sending modals outside of interactions
                # So we'll create the message directly
                await self.create_message_directly(channel, interaction)
                
            except Exception as e:
                await self.ctx.send(f"❌ Timed out or error: {e}", delete_after=5)
        
        create_btn.callback = create_callback
        button_row.add_item(create_btn)
        
        add_btn = Button(style=discord.ButtonStyle.primary, label="Add Role", emoji="➕")
        async def add_callback(interaction: discord.Interaction):
            if interaction.user.id != self.ctx.author.id:
                await interaction.response.send_message("❌ This panel is not for you!", ephemeral=True)
                return
            modal = AddReactionModal(self.cog, self.ctx.guild)
            await interaction.response.send_modal(modal)
        add_btn.callback = add_callback
        button_row.add_item(add_btn)
        
        remove_btn = Button(style=discord.ButtonStyle.danger, label="Remove Role", emoji="➖")
        async def remove_callback(interaction: discord.Interaction):
            if interaction.user.id != self.ctx.author.id:
                await interaction.response.send_message("❌ This panel is not for you!", ephemeral=True)
                return
            modal = RemoveReactionModal(self.cog, self.ctx.guild)
            await interaction.response.send_modal(modal)
        remove_btn.callback = remove_callback
        button_row.add_item(remove_btn)
        
        container.add_item(button_row)
        
        # Second row
        button_row2 = ActionRow()
        
        list_btn = Button(style=discord.ButtonStyle.secondary, label="List Messages", emoji="📋")
        async def list_callback(interaction: discord.Interaction):
            if interaction.user.id != self.ctx.author.id:
                await interaction.response.send_message("❌ This panel is not for you!", ephemeral=True)
                return
            await self.show_list(interaction)
        list_btn.callback = list_callback
        button_row2.add_item(list_btn)
        
        close_btn = Button(style=discord.ButtonStyle.red, label="Close", emoji="❌")
        async def close_callback(interaction: discord.Interaction):
            if interaction.user.id != self.ctx.author.id:
                await interaction.response.send_message("❌ This panel is not for you!", ephemeral=True)
                return
            await interaction.message.delete()
        close_btn.callback = close_callback
        button_row2.add_item(close_btn)
        
        container.add_item(button_row2)
        
        self.add_item(container)
    
    async def create_message_directly(self, channel, interaction):
        """Helper to create message without modal"""
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## Reaction Roles"))
        container.add_item(Separator())
        container.add_item(TextDisplay("React to get your roles!"))
        container.add_item(Separator())
        container.add_item(TextDisplay("-# React below to get roles"))
        
        view.add_item(container)
        msg = await channel.send(view=view)
        
        # Success response
        success_view = LayoutView()
        success_container = Container()
        
        success_container.add_item(TextDisplay("## ✅ Success"))
        success_container.add_item(Separator())
        success_container.add_item(TextDisplay(
            f"Created reaction role message in {channel.name}\n"
            f"**Message ID:** `{msg.id}`"
        ))
        
        success_view.add_item(success_container)
        await interaction.followup.send(view=success_view, ephemeral=True)
    
    async def show_list(self, interaction):
        messages = list(await self.cog.get_all_guild_reaction_roles(self.ctx.guild.id))
        
        view = LayoutView()
        container = Container()
        
        if not messages:
            container.add_item(TextDisplay("## ❌ No Reaction Roles"))
            container.add_item(Separator())
            container.add_item(TextDisplay("No reaction role messages found."))
        else:
            container.add_item(TextDisplay("## 📋 Reaction Role Messages"))
            container.add_item(Separator())
            
            for msg_id, ch_id in messages[:5]:
                channel = self.ctx.guild.get_channel(ch_id)
                reaction_roles = await self.cog.get_reaction_roles(msg_id)
                
                roles_text = "\n".join([
                    f"{emoji} → <@&{role_id}>" 
                    for emoji, role_id in list(reaction_roles.items())[:3]
                ])
                
                if len(reaction_roles) > 3:
                    roles_text += f"\n... and {len(reaction_roles) - 3} more"
                
                container.add_item(TextDisplay(
                    f"**Message ID:** `{msg_id}`\n"
                    f"**Channel:** {channel.name if channel else 'Unknown'}\n"
                    f"{roles_text}"
                ))
                container.add_item(Separator())
            
            if len(messages) > 5:
                container.add_item(TextDisplay(f"-# Showing 5 of {len(messages)} messages"))
        
        view.add_item(container)
        await interaction.response.send_message(view=view, ephemeral=True)


class ReactionRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.create_table())
        self.color = 0x2f3136

    async def create_table(self):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS reactionroles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                emoji TEXT NOT NULL,
                role_id INTEGER NOT NULL,
                UNIQUE(message_id, emoji)
            )
            """)
            await db.commit()

    async def get_reaction_roles(self, message_id: int):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute(
                "SELECT emoji, role_id FROM reactionroles WHERE message_id = ?", 
                (message_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return {row[0]: row[1] for row in rows}

    async def add_reaction_role(self, guild_id: int, channel_id: int, message_id: int, emoji: str, role_id: int):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO reactionroles (guild_id, channel_id, message_id, emoji, role_id) VALUES (?, ?, ?, ?, ?)",
                (guild_id, channel_id, message_id, emoji, role_id)
            )
            await db.commit()

    async def remove_reaction_role(self, message_id: int, emoji: str):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "DELETE FROM reactionroles WHERE message_id = ? AND emoji = ?",
                (message_id, emoji)
            )
            await db.commit()

    async def delete_message_reaction_roles(self, message_id: int):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "DELETE FROM reactionroles WHERE message_id = ?",
                (message_id,)
            )
            await db.commit()

    async def get_all_guild_reaction_roles(self, guild_id: int):
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute(
                "SELECT DISTINCT message_id, channel_id FROM reactionroles WHERE guild_id = ?",
                (guild_id,)
            ) as cursor:
                return await cursor.fetchall()

    @commands.hybrid_command(name="reactionrole", aliases=['rr', 'rrpanel'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(manage_roles=True)
    async def _reactionrole(self, ctx):
        """Open the reaction role management panel"""
        panel = ReactionRolePanel(ctx, self)
        await ctx.reply(view=panel)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        
        reaction_roles = await self.get_reaction_roles(payload.message_id)
        emoji_str = str(payload.emoji)
        
        if emoji_str in reaction_roles:
            guild = self.bot.get_guild(payload.guild_id)
            if guild:
                role = guild.get_role(reaction_roles[emoji_str])
                member = guild.get_member(payload.user_id)
                
                if role and member:
                    try:
                        await member.add_roles(role, reason="Reaction role")
                    except discord.Forbidden:
                        pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        
        reaction_roles = await self.get_reaction_roles(payload.message_id)
        emoji_str = str(payload.emoji)
        
        if emoji_str in reaction_roles:
            guild = self.bot.get_guild(payload.guild_id)
            if guild:
                role = guild.get_role(reaction_roles[emoji_str])
                member = guild.get_member(payload.user_id)
                
                if role and member:
                    try:
                        await member.remove_roles(role, reason="Reaction role removed")
                    except discord.Forbidden:
                        pass


async def setup(bot):
    await bot.add_cog(ReactionRole(bot))
