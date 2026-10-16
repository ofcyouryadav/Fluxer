import discord
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay, Separator
import aiosqlite
import os
import time
import asyncio
from typing import Optional
from utils.Tools import *

DB_PATH = "db/afk.db"

# Colors for Component V2
SUCCESS_COLOR = 0x00ff88
ERROR_COLOR = 0xff0033
INFO_COLOR = 0x2f3136
WARNING_COLOR = 0xffaa00

class DmChoiceView(discord.ui.View):
    """Button view for asking if user wants DM notifications"""
    def __init__(self, ctx: commands.Context, timeout: Optional[int] = 180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                f"Only **{self.ctx.author}** can use this button!", 
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="DM me", emoji="", custom_id='Yes', style=discord.ButtonStyle.green)
    async def dm_yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = 'Yes'
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Don't DM", emoji="", custom_id='No', style=discord.ButtonStyle.danger)
    async def dm_no(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = 'No'
        await interaction.response.defer()
        self.stop()


class Afk(commands.Cog):
    def __init__(self, client, *args, **kwargs):
        self.client = client
        self.client.loop.create_task(self.initialize_db())

    async def initialize_db(self):
        """Initialize the AFK database"""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS afk (
                    user_id INTEGER PRIMARY KEY,
                    AFK TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    time INTEGER NOT NULL,
                    mentions INTEGER NOT NULL,
                    dm TEXT NOT NULL
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS afk_guild (
                    user_id INTEGER NOT NULL,
                    guild_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, guild_id)
                )
            """)
            await db.commit()

    async def cog_after_invoke(self, ctx):
        """Reset cooldown after command"""
        ctx.command.reset_cooldown(ctx)

    async def update_data(self, user, guild_id):
        """Update user data in database"""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR IGNORE INTO afk (user_id, AFK, reason, time, mentions, dm) VALUES (?, 'False', 'None', 0, 0, 'False')", 
                (user.id,)
            )
            await db.execute(
                "INSERT OR IGNORE INTO afk_guild (user_id, guild_id) VALUES (?, ?)", 
                (user.id, guild_id)
            )
            await db.commit()

    async def time_formatter(self, seconds: float) -> str:
        """Format seconds into readable time string"""
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        
        time_parts = []
        if days:
            time_parts.append(f"{days} day{'s' if days > 1 else ''}")
        if hours:
            time_parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
        if minutes:
            time_parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
        if seconds:
            time_parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")
        
        return ", ".join(time_parts) if time_parts else "0 seconds"

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

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle AFK status checks and mentions"""
        try:
            if message.author.bot:
                return

            async with aiosqlite.connect(DB_PATH) as db:
                # Check if author was AFK
                cursor = await db.execute(
                    "SELECT AFK, time, mentions, reason FROM afk WHERE user_id = ?", 
                    (message.author.id,)
                )
                afk_data = await cursor.fetchone()
                await cursor.close()

                if afk_data and afk_data[0] == 'True':
                    cursor = await db.execute(
                        "SELECT guild_id FROM afk_guild WHERE user_id = ?", 
                        (message.author.id,)
                    )
                    guild_ids = [row[0] for row in await cursor.fetchall()]
                    await cursor.close()

                    if message.guild.id in guild_ids:
                        # Calculate AFK time
                        meth = int(time.time()) - int(afk_data[1])
                        been_afk_for = await self.time_formatter(meth)
                        mention_count = afk_data[2]
                        
                        # Remove AFK status
                        await db.execute(
                            "UPDATE afk SET AFK = 'False', reason = 'None' WHERE user_id = ?", 
                            (message.author.id,)
                        )
                        await db.execute(
                            "DELETE FROM afk_guild WHERE user_id = ? AND guild_id = ?", 
                            (message.author.id, message.guild.id)
                        )
                        await db.commit()

                        # Send welcome back message using Component V2
                        view = self.create_response(
                            "💤 Welcome Back!",
                            f"**{message.author.name}**, I removed your AFK status!\n\n"
                            f"**Total Mentions:** {mention_count}\n"
                            f"**AFK Time:** {been_afk_for}",
                            SUCCESS_COLOR
                        )
                        try:
                            await message.reply(view=view)
                        except discord.Forbidden:
                            print(f"(AFK module) Missing permissions to send messages in channel: {message.channel.id}")

            # Check if anyone mentioned is AFK
            if message.mentions:
                async with aiosqlite.connect(DB_PATH) as db:
                    for user_mention in message.mentions:
                        cursor = await db.execute(
                            "SELECT AFK, reason, time, mentions, dm FROM afk WHERE user_id = ?", 
                            (user_mention.id,)
                        )
                        afk_data = await cursor.fetchone()
                        await cursor.close()

                        if afk_data and afk_data[0] == 'True':
                            cursor = await db.execute(
                                "SELECT guild_id FROM afk_guild WHERE user_id = ?", 
                                (user_mention.id,)
                            )
                            guild_ids = [row[0] for row in await cursor.fetchall()]
                            await cursor.close()

                            if message.guild.id in guild_ids:
                                reason = afk_data[1]
                                timestamp = afk_data[2]
                                
                                # Send notification about mentioned user's AFK status
                                view = self.create_response(
                                    "💤 User is AFK",
                                    f"**{user_mention.name}** is AFK since <t:{timestamp}:R>\n\n"
                                    f"**Reason:** {reason}",
                                    WARNING_COLOR
                                )
                                try:
                                    await message.reply(view=view)
                                except discord.Forbidden:
                                    print(f"(AFK module) Missing permissions to send messages in channel: {message.channel.id}")

                                # Update mention count
                                new_mentions = afk_data[3] + 1
                                await db.execute(
                                    "UPDATE afk SET mentions = ? WHERE user_id = ?", 
                                    (new_mentions, user_mention.id)
                                )
                                await db.commit()

                                # Send DM if enabled
                                if afk_data[4] == 'True':
                                    try:
                                        dm_view = LayoutView()
                                        dm_container = Container()
                                        dm_container.add_item(TextDisplay("## 💬 You Were Mentioned!"))
                                        dm_container.add_item(Separator())
                                        dm_container.add_item(TextDisplay(
                                            f"**Server:** {message.guild.name}\n"
                                            f"**Mentioned by:** {message.author.name}\n"
                                            f"**Total Mentions:** {new_mentions}\n\n"
                                            f"**Message:** {message.content}\n\n"
                                            f"[Jump to message]({message.jump_url})"
                                        ))
                                        dm_view.add_item(dm_container)
                                        await user_mention.send(view=dm_view)
                                    except discord.Forbidden:
                                        print(f"(AFK module) Missing permissions to send DMs to user: {user_mention.id}")

            # Update user data
            if not message.author.bot:
                await self.update_data(message.author, message.guild.id)
        except Exception as e:
            print(f"Ignoring exception in on_message: {e}")

    @commands.command(description="Set your AFK status")
    @blacklist_check()
    @ignore_check()
    @commands.guild_only()
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def afk(self, ctx, *, reason: str = None):
        """Set AFK status when you're away"""
        
        if not reason:
            reason = "I am AFK"

        # Check for server invite links
        if any(invite in reason.lower() for invite in ['discord.gg', 'gg/']):
            view = self.create_response(
                "❌ Invalid Reason",
                "You can't advertise server invites in your AFK reason!",
                ERROR_COLOR
            )
            return await ctx.send(view=view)

        # Ask if user wants DM notifications with buttons integrated into LayoutView
        from discord.ui import ActionRow, Button
        
        ask_view = LayoutView()
        ask_container = Container()
        ask_container.add_item(TextDisplay("## 💤 DM Notifications"))
        ask_container.add_item(Separator())
        ask_container.add_item(TextDisplay("Should I DM you when someone mentions you?"))
        ask_container.add_item(Separator())
        
        # Create button row
        button_row = ActionRow()
        
        # Store the selected value
        selected_dm_choice = {'value': None}
        
        # DM Yes Button
        dm_yes_btn = Button(style=discord.ButtonStyle.green, label="DM me", emoji="💬", custom_id=f"afk_dm_yes_{ctx.author.id}")
        async def dm_yes_callback(interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message(f"Only **{ctx.author}** can use this button!", ephemeral=True)
            selected_dm_choice['value'] = 'Yes'
            await interaction.response.defer()
        dm_yes_btn.callback = dm_yes_callback
        button_row.add_item(dm_yes_btn)
        
        # DM No Button
        dm_no_btn = Button(style=discord.ButtonStyle.danger, label="Don't DM", emoji="🚫", custom_id=f"afk_dm_no_{ctx.author.id}")
        async def dm_no_callback(interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message(f"Only **{ctx.author}** can use this button!", ephemeral=True)
            selected_dm_choice['value'] = 'No'
            await interaction.response.defer()
        dm_no_btn.callback = dm_no_callback
        button_row.add_item(dm_no_btn)
        
        ask_container.add_item(button_row)
        ask_view.add_item(ask_container)
        
        # Send message and wait for button interaction
        test = await ctx.reply(view=ask_view)
        
        # Wait for button interaction (timeout 180 seconds)
        start_time = time.time()
        while selected_dm_choice['value'] is None:
            await asyncio.sleep(0.5)
            if time.time() - start_time > 180:  # 180 second timeout
                break

        async with aiosqlite.connect(DB_PATH) as db:
            if not selected_dm_choice['value']:
                # Timeout
                timeout_view = self.create_response(
                    "⏳ Timeout",
                    "You took too long to respond. Please try again.",
                    ERROR_COLOR
                )
                return await test.edit(view=timeout_view)

            dm_status = 'True' if selected_dm_choice['value'] == 'Yes' else 'False'

            # Set AFK status
            await db.execute(
                "INSERT OR REPLACE INTO afk (user_id, AFK, reason, time, mentions, dm) VALUES (?, 'True', ?, ?, 0, ?)", 
                (ctx.author.id, reason, int(time.time()), dm_status)
            )
            await db.commit()
            await db.execute(
                "INSERT OR IGNORE INTO afk_guild (user_id, guild_id) VALUES (?, ?)", 
                (ctx.author.id, ctx.guild.id)
            )
            await db.commit()

            # Send success message
            dm_status_text = " Enabled" if dm_status == 'True' else " Disabled"
            success_view = self.create_response(
                " AFK Status Set",
                f"**Reason:** {reason}\n**DM Notifications:** {dm_status_text}",
                SUCCESS_COLOR
            )
            
            await test.delete()
            await ctx.reply(view=success_view)


async def setup(bot):
    await bot.add_cog(Afk(bot.client if hasattr(bot, "client") else bot))
