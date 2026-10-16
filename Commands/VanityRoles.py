import discord
from discord.ext import commands, tasks
from discord.ui import LayoutView, Container, TextDisplay, Separator, ActionRow, Button, Select
import aiosqlite
from core import Cryptora, Context
from utils.Tools import blacklist_check, ignore_check

DATABASE_PATH = 'db/vanity.db'

SUCCESS_COLOR = 0x00ff88
ERROR_COLOR = 0xff0033
INFO_COLOR = 0x2f3136


class VanityRoles(commands.Cog):
    def __init__(self, bot: Cryptora):
        self.bot = bot
        self.bot.loop.create_task(self.initialize_db())
        self.status_monitor.start()

    async def initialize_db(self):
        """Initialize vanity roles database"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS vanity_config (
                    guild_id INTEGER PRIMARY KEY,
                    role_id INTEGER,
                    enabled INTEGER DEFAULT 1,
                    custom_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS vanity_users (
                    user_id INTEGER,
                    guild_id INTEGER,
                    has_role INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, guild_id)
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS vanity_notifications (
                    guild_id INTEGER PRIMARY KEY,
                    enabled INTEGER DEFAULT 0,
                    channel_id INTEGER,
                    custom_message TEXT,
                    last_user_id INTEGER,
                    last_message_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()

    async def get_vanity_config(self, guild_id: int):
        """Get vanity role config for a guild"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute(
                "SELECT role_id, enabled, custom_text FROM vanity_config WHERE guild_id = ?",
                (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'role_id': row[0],
                        'enabled': row[1],
                        'custom_text': row[2]
                    }
                return None

    async def set_vanity_config(self, guild_id: int, role_id: int, custom_text: str = ""):
        """Set vanity role config for a guild"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                '''INSERT INTO vanity_config (guild_id, role_id, custom_text, enabled) 
                   VALUES (?, ?, ?, 1)
                   ON CONFLICT(guild_id) DO UPDATE SET 
                   role_id=?, custom_text=?, enabled=1''',
                (guild_id, role_id, custom_text, role_id, custom_text)
            )
            await db.commit()

    async def reset_vanity_config(self, guild_id: int):
        """Reset vanity role config for a guild"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("DELETE FROM vanity_config WHERE guild_id = ?", (guild_id,))
            await db.execute("DELETE FROM vanity_users WHERE guild_id = ?", (guild_id,))
            await db.commit()

    async def user_has_vanity_role(self, user_id: int, guild_id: int) -> bool:
        """Check if user has vanity role"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute(
                "SELECT has_role FROM vanity_users WHERE user_id = ? AND guild_id = ?",
                (user_id, guild_id)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] == 1 if row else False

    async def set_user_vanity_role(self, user_id: int, guild_id: int, has_role: bool):
        """Update user vanity role status"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                '''INSERT INTO vanity_users (user_id, guild_id, has_role) 
                   VALUES (?, ?, ?)
                   ON CONFLICT(user_id, guild_id) DO UPDATE SET has_role=?''',
                (user_id, guild_id, 1 if has_role else 0, 1 if has_role else 0)
            )
            await db.commit()

    async def get_notification_config(self, guild_id: int):
        """Get notification config for a guild"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute(
                "SELECT enabled, channel_id, custom_message FROM vanity_notifications WHERE guild_id = ?",
                (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'enabled': row[0] == 1,
                        'channel_id': row[1],
                        'custom_message': row[2]
                    }
                return None

    async def set_notification_config(self, guild_id: int, enabled: bool, channel_id: int = None, custom_message: str = None):
        """Set notification config for a guild"""
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                '''INSERT INTO vanity_notifications (guild_id, enabled, channel_id, custom_message) 
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(guild_id) DO UPDATE SET 
                   enabled=?, channel_id=?, custom_message=?''',
                (guild_id, 1 if enabled else 0, channel_id, custom_message,
                 1 if enabled else 0, channel_id, custom_message)
            )
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

    @commands.group(name="vanityroles", aliases=["vr"], invoke_without_command=True)
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def vanityroles(self, ctx: Context):
        """Vanity Roles system - auto-assign roles based on custom status"""
        view = self.create_response(
            "✨ Vanity Roles System",
            "`vr setup <role>` - Setup vanity role system\n"
            "`vr config` - Show current configuration\n"
            "`vr reset` - Disable vanity roles\n"
            "`vr info` - Show how it works",
            INFO_COLOR
        )
        await ctx.send(view=view)

    @vanityroles.command(name="setup")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def setup(self, ctx: Context):
        """Setup vanity role system with interactive panel"""
        
        # Get valid roles (no admin, ban, kick perms, and below bot's top role)
        valid_roles = [
            r for r in ctx.guild.roles 
            if not (r.permissions.administrator or r.permissions.ban_members or r.permissions.kick_members)
            and r < ctx.guild.me.top_role
            and r != ctx.guild.default_role
        ][:25]  # Max 25 options
        
        if not valid_roles:
            view = self.create_response(
                "❌ No Valid Roles",
                "No valid roles available for vanity system. Create a role without admin permissions.",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        # Create setup panel
        class VanitySetupPanel(discord.ui.View):
            def __init__(self, cog, author_id, guild):
                super().__init__(timeout=300)
                self.cog = cog
                self.author_id = author_id
                self.guild = guild
                self.selected_role = None
                self.custom_text = ""
            
            @discord.ui.select(
                placeholder="Select vanity role...",
                options=[
                    discord.SelectOption(
                        label=role.name[:100],
                        value=str(role.id),
                        emoji="🎭"
                    )
                    for role in valid_roles
                ]
            )
            async def role_select(self, interaction: discord.Interaction, select: discord.ui.Select):
                if interaction.user.id != self.author_id:
                    return await interaction.response.send_message("Not your setup!", ephemeral=True)
                
                self.selected_role = int(select.values[0])
                await interaction.response.defer()
            
            @discord.ui.button(style=discord.ButtonStyle.primary, emoji="⚙️", label="Configure Text")
            async def configure_text(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != self.author_id:
                    return await interaction.response.send_message("Not your setup!", ephemeral=True)
                
                class CustomTextModal(discord.ui.Modal, title="Vanity Roles - Custom Text"):
                    text_input = discord.ui.TextInput(
                        label="Optional: Filter by status text",
                        placeholder="Leave blank for any custom status",
                        max_length=100,
                        required=False
                    )
                    
                    async def on_submit(self, modal_interaction: discord.Interaction):
                        self.parent.custom_text = self.text_input.value or ""
                        await modal_interaction.response.defer()
                
                modal = CustomTextModal()
                modal.parent = self
                await interaction.response.send_modal(modal)
            
            @discord.ui.button(style=discord.ButtonStyle.success, emoji="✅", label="Confirm Setup")
            async def confirm_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != self.author_id:
                    return await interaction.response.send_message("Not your setup!", ephemeral=True)
                
                if not self.selected_role:
                    return await interaction.response.send_message("Please select a role first!", ephemeral=True)
                
                role = self.guild.get_role(self.selected_role)
                if not role:
                    return await interaction.response.send_message("Role not found!", ephemeral=True)
                
                # Save config
                await self.cog.set_vanity_config(self.guild.id, self.selected_role, self.custom_text)
                
                # Show success response (Component V2 doesn't allow content in edit_message)
                success_view = LayoutView()
                success_container = Container()
                success_container.add_item(TextDisplay("## ✅ Vanity Role Setup Complete"))
                success_container.add_item(Separator())
                success_container.add_item(TextDisplay(
                    f"**Role:** {role.name}\n"
                    f"**Text Filter:** {self.custom_text or 'Any custom status'}\n"
                    f"**Status:** 🟢 Active"
                ))
                success_container.add_item(Separator())
                success_container.add_item(TextDisplay(
                    "✨ **How it works:**\n"
                    "• User sets custom status → Gets vanity role ✅\n"
                    "• User clears status → Role removed ❌\n"
                    "• User goes offline → Role removed ❌"
                ))
                success_view.add_item(success_container)
                
                await interaction.response.edit_message(view=success_view)
                self.stop()
            
            @discord.ui.button(style=discord.ButtonStyle.danger, emoji="❌", label="Cancel")
            async def cancel_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != self.author_id:
                    return await interaction.response.send_message("Not your setup!", ephemeral=True)
                
                await interaction.response.defer()
                self.stop()
        
        # Create and send panel
        panel = VanitySetupPanel(self, ctx.author.id, ctx.guild)
        
        # Create instruction view (Component V2 - no content needed)
        instruction_view = LayoutView()
        instruction_container = Container()
        instruction_container.add_item(TextDisplay("## ✨ Vanity Roles Setup"))
        instruction_container.add_item(Separator())
        instruction_container.add_item(TextDisplay(
            "**Step 1:** Select the role from dropdown\n"
            "**Step 2:** Click ⚙️ to add optional text filter\n"
            "**Step 3:** Click ✅ to confirm setup"
        ))
        instruction_view.add_item(instruction_container)
        
        # Send instructions with LayoutView, then panel with buttons
        await ctx.send(view=instruction_view)
        await ctx.send(view=panel)

    @vanityroles.command(name="notifications")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def notifications(self, ctx: Context, channel: discord.TextChannel = None):
        """Configure status change notifications"""
        if channel is None:
            # Show current notification config
            notif_config = await self.get_notification_config(ctx.guild.id)
            
            if not notif_config or not notif_config['enabled']:
                view = self.create_response(
                    "🔔 Notifications Disabled",
                    "Status change notifications are currently disabled.\n\n"
                    "Use: `/vr notifications <channel>` to enable",
                    INFO_COLOR
                )
                return await ctx.send(view=view)
            
            notif_channel = ctx.guild.get_channel(notif_config['channel_id'])
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## 🔔 Notification Settings"))
            container.add_item(Separator())
            container.add_item(TextDisplay(
                f"**Status:** 🟢 Enabled\n"
                f"**Channel:** {notif_channel.name if notif_channel else 'Unknown'}\n"
                f"**Custom Message:** {'Yes ✅' if notif_config['custom_message'] else 'Default 📝'}\n\n"
                f"-# Use `/vr notifications <channel>` to change channel\n"
                f"-# Use `/vr setstatus` to set custom message"
            ))
            view.add_item(container)
            return await ctx.send(view=view)
        
        # Enable notifications for specified channel
        await self.set_notification_config(ctx.guild.id, True, channel.id, None)
        
        view = self.create_response(
            "✅ Notifications Enabled",
            f"Status change notifications will be sent to {channel.name}\n\n"
            "Use `/vr setstatus` to customize the notification message",
            SUCCESS_COLOR
        )
        await ctx.send(view=view)

    @vanityroles.command(name="setstatus")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def setstatus(self, ctx: Context, *, message: str = None):
        """Set custom notification message"""
        if message is None:
            view = self.create_response(
                "📝 Custom Message Format",
                "Use placeholders in your message:\n\n"
                "`{user}` - User mention\n"
                "`{status}` - Custom status text\n"
                "`{role}` - Vanity role mention\n\n"
                "Example: `{user} set their status to: {status}`\n\n"
                "Use `/vr setstatus <message>` to set a custom message",
                INFO_COLOR
            )
            return await ctx.send(view=view)
        
        if len(message) > 200:
            view = self.create_response(
                "❌ Message Too Long",
                "Custom message must be 200 characters or less",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        notif_config = await self.get_notification_config(ctx.guild.id)
        if not notif_config or not notif_config['channel_id']:
            view = self.create_response(
                "⚠️ Notifications Not Enabled",
                "Enable notifications first using `/vr notifications <channel>`",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        await self.set_notification_config(ctx.guild.id, True, notif_config['channel_id'], message)
        
        view = self.create_response(
            "✅ Custom Message Set",
            f"Message: `{message}`",
            SUCCESS_COLOR
        )
        await ctx.send(view=view)

    @vanityroles.command(name="config")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def config(self, ctx: Context):
        """Show vanity roles configuration"""
        config = await self.get_vanity_config(ctx.guild.id)
        
        if not config:
            view = self.create_response(
                "⚠️ Not Configured",
                "Vanity roles system is not setup for this server.\nUse `/vr setup` to enable it.",
                ERROR_COLOR
            )
            return await ctx.send(view=view)

        role = ctx.guild.get_role(config['role_id'])
        if not role:
            view = self.create_response(
                "❌ Role Not Found",
                "The configured role was deleted.",
                ERROR_COLOR
            )
            await self.reset_vanity_config(ctx.guild.id)
            return await ctx.send(view=view)

        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay("## ⚙️ Vanity Roles Configuration"))
        container.add_item(Separator())
        container.add_item(TextDisplay(
            f"**Status:** {'✅ Active' if config['enabled'] else '❌ Disabled'}\n"
            f"**Role:** {role.name}\n"
            f"**Custom Text Filter:** {config['custom_text'] or 'Any status'}"
        ))
        view.add_item(container)
        await ctx.send(view=view)

    @vanityroles.command(name="reset")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def reset(self, ctx: Context):
        """Disable vanity roles system"""
        config = await self.get_vanity_config(ctx.guild.id)
        
        if not config:
            view = self.create_response(
                "⚠️ Not Active",
                "Vanity roles system is not setup for this server.",
                ERROR_COLOR
            )
            return await ctx.send(view=view)

        await self.reset_vanity_config(ctx.guild.id)
        
        view = self.create_response(
            "✅ Vanity Roles Disabled",
            "All vanity role configurations and user data have been cleared.",
            SUCCESS_COLOR
        )
        await ctx.send(view=view)

    @vanityroles.command(name="info")
    @blacklist_check()
    @ignore_check()
    async def info(self, ctx: Context):
        """Show how vanity roles work"""
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay("## ℹ️ How Vanity Roles Work"))
        container.add_item(Separator())
        container.add_item(TextDisplay(
            "**Automatic Status Detection:**\n"
            "• User sets custom status → Gets vanity role ✅\n"
            "• User clears status → Role removed ❌\n"
            "• User goes offline → Role removed ❌\n"
            "• User comes back online with status → Gets role back ✅\n\n"
            "**Setup:**\n"
            "1. Use `/vr setup <role>` to enable\n"
            "2. The bot monitors user presence changes\n"
            "3. Roles are managed automatically\n\n"
            "**Per-Server Configuration:**\n"
            "• Each server has its own role\n"
            "• Use `/vr config` to see current settings\n"
            "• Use `/vr reset` to disable"
        ))
        view.add_item(container)
        await ctx.send(view=view)

    @tasks.loop(minutes=2)
    async def status_monitor(self):
        """Monitor user presence changes and assign/remove vanity roles"""
        try:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                async with db.execute("SELECT guild_id, role_id FROM vanity_config WHERE enabled = 1") as cursor:
                    configs = await cursor.fetchall()

            for guild_id, role_id in configs:
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue

                role = guild.get_role(role_id)
                if not role:
                    await self.reset_vanity_config(guild_id)
                    continue

                # Check all members
                for member in guild.members:
                    has_status = member.activity and isinstance(member.activity, discord.CustomActivity)
                    is_online = member.status != discord.Status.offline

                    should_have_role = has_status and is_online
                    currently_has_role = role in member.roles
                    user_record = await self.user_has_vanity_role(member.id, guild_id)

                    # Give role if should have and doesn't
                    if should_have_role and not currently_has_role:
                        try:
                            await member.add_roles(role)
                            await self.set_user_vanity_role(member.id, guild_id, True)
                        except discord.Forbidden:
                            pass

                    # Remove role if shouldn't have but does
                    elif not should_have_role and currently_has_role:
                        try:
                            await member.remove_roles(role)
                            await self.set_user_vanity_role(member.id, guild_id, False)
                        except discord.Forbidden:
                            pass

        except Exception as e:
            print(f"Error in status_monitor: {e}")

    @status_monitor.before_loop
    async def before_status_monitor(self):
        """Wait until bot is ready before starting monitor"""
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        """Real-time presence update handler"""
        guild_id = after.guild.id
        config = await self.get_vanity_config(guild_id)
        
        if not config or not config['enabled']:
            return

        role = after.guild.get_role(config['role_id'])
        if not role:
            return

        # Check if status changed
        before_status = before.activity and isinstance(before.activity, discord.CustomActivity)
        after_status = after.activity and isinstance(after.activity, discord.CustomActivity)
        
        # Status added
        if not before_status and after_status and after.status != discord.Status.offline:
            if role not in after.roles:
                try:
                    await after.add_roles(role)
                    await self.set_user_vanity_role(after.id, guild_id, True)
                    
                    # Send notification if enabled
                    await self._send_status_notification(
                        after, after_status.name, role, 
                        guild_id, "status_set"
                    )
                except discord.Forbidden:
                    pass
        
        # Status removed or went offline
        elif before_status and (not after_status or after.status == discord.Status.offline):
            if role in after.roles:
                try:
                    await after.remove_roles(role)
                    await self.set_user_vanity_role(after.id, guild_id, False)
                    
                    # Send notification if enabled
                    await self._send_status_notification(
                        after, before_status.name if before_status else "offline", 
                        role, guild_id, "status_removed"
                    )
                except discord.Forbidden:
                    pass

    async def _send_status_notification(self, member: discord.Member, status: str, role: discord.Role, guild_id: int, action: str):
        """Send status change notification to configured channel"""
        notif_config = await self.get_notification_config(guild_id)
        if not notif_config or not notif_config['enabled']:
            return
        
        guild = member.guild
        channel = guild.get_channel(notif_config['channel_id'])
        if not channel:
            return
        
        try:
            # Format notification message
            if notif_config['custom_message']:
                message = notif_config['custom_message'].format(
                    user=member.name,
                    status=status,
                    role=role.name
                )
            else:
                # Default message
                if action == "status_set":
                    message = f"✅ {member.name} set their custom status and got {role.name}"
                else:
                    message = f"❌ {member.name} cleared their status and lost {role.name}"
            
            await channel.send(message)
        except Exception as e:
            print(f"Error sending notification: {e}")

    def cog_unload(self):
        """Cleanup when cog is unloaded"""
        self.status_monitor.cancel()


async def setup(bot: Cryptora):
    await bot.add_cog(VanityRoles(bot))
