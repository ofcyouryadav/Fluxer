import discord
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay, Separator, Button
from datetime import timedelta
from typing import Optional
import asyncio

SUCCESS_COLOR = 0x00ff88
ERROR_COLOR = 0xff0033
INFO_COLOR = 0x2f3136
WARNING_COLOR = 0xffaa00

class NukeConfirmButton(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=30)
        self.author_id = author_id
        self.result = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.danger, emoji="⚠️")
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ You can't use this button!", ephemeral=True)
            return
        self.result = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary, emoji="❌")
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ You can't use this button!", ephemeral=True)
            return
        self.result = False
        self.stop()
        await interaction.response.defer()


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.media_channels = {}

    def create_embed(self, title: str, description: str = "", color: int = INFO_COLOR):
        """Helper to create Component V2 responses"""
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## {title}"))
        if description:
            container.add_item(Separator())
            container.add_item(TextDisplay(description))
        view.add_item(container)
        return view

    # ==================== BAN COMMANDS ====================
    @commands.command(name="ban", aliases=["hackban", "fuckban"])
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(self, ctx, user: discord.User, *, reason: str = "No reason provided"):
        """Ban a user from the server"""
        
        # Validation checks
        if user.id == ctx.author.id:
            view = self.create_embed("❌ Cannot Ban Self", "You cannot ban yourself!", ERROR_COLOR)
            return await ctx.reply(view=view)
        
        if user.id == self.bot.user.id:
            view = self.create_embed("❌ Cannot Ban Bot", "If you ban me, who will protect your server?!", ERROR_COLOR)
            return await ctx.reply(view=view)
        
        if user.id == ctx.guild.owner_id:
            view = self.create_embed("❌ Cannot Ban Owner", "I cannot ban the server owner!", ERROR_COLOR)
            return await ctx.reply(view=view)
        
        try:
            full_reason = f"{ctx.author.tag} ({ctx.author.id}) | {reason}"
            await ctx.guild.ban(user, reason=full_reason)
            
            # Try to DM the user
            try:
                dm_embed = discord.Embed(
                    title=f"🔨 Banned from {ctx.guild.name}",
                    description=f"**Executor:** {ctx.author.tag}\n**Reason:** {reason}",
                    color=ERROR_COLOR
                )
                await user.send(embed=dm_embed)
            except:
                pass
            
            view = self.create_embed(
                "✅ Member Banned",
                f"**User:** {user.name}\n**Reason:** {reason}",
                SUCCESS_COLOR
            )
            await ctx.reply(view=view)
        except discord.Forbidden:
            view = self.create_embed("❌ Permission Error", "My role is not high enough to ban this user!", ERROR_COLOR)
            await ctx.reply(view=view)
        except Exception as e:
            view = self.create_embed("❌ Error", f"Failed to ban: {str(e)}", ERROR_COLOR)
            await ctx.reply(view=view)

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def unban(self, ctx, user_id: str, *, reason: str = "No reason provided"):
        """Unban a user from the server"""
        
        try:
            user = await self.bot.fetch_user(int(user_id))
        except (ValueError, discord.NotFound):
            view = self.create_embed("❌ Invalid User", "Please provide a valid user ID!", ERROR_COLOR)
            return await ctx.reply(view=view)
        
        try:
            await ctx.guild.unban(user, reason=reason)
            view = self.create_embed(
                "✅ Member Unbanned",
                f"**User:** {user.name}\n**Reason:** {reason}",
                SUCCESS_COLOR
            )
            await ctx.reply(view=view)
        except discord.NotFound:
            view = self.create_embed("❌ Not Banned", "This user is not banned in this server!", ERROR_COLOR)
            await ctx.reply(view=view)
        except Exception as e:
            view = self.create_embed("❌ Error", f"Failed to unban: {str(e)}", ERROR_COLOR)
            await ctx.reply(view=view)

    @commands.command(name="unbanall")
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def unbanall(self, ctx):
        """Unban all users from the server"""
        
        try:
            bans = await ctx.guild.bans()
            ban_count = len(bans)
            
            if ban_count == 0:
                view = self.create_embed("ℹ️ No Bans", "There are no banned users in this server!", INFO_COLOR)
                return await ctx.reply(view=view)
            
            status_msg = await ctx.send("⏳ Unbanning users...")
            
            for ban_entry in bans:
                try:
                    await ctx.guild.unban(ban_entry.user, reason="Unban all command")
                except:
                    pass
            
            await status_msg.delete()
            view = self.create_embed(
                "✅ All Users Unbanned",
                f"Successfully unbanned **{ban_count}** users!",
                SUCCESS_COLOR
            )
            await ctx.reply(view=view)
        except Exception as e:
            view = self.create_embed("❌ Error", f"Failed: {str(e)}", ERROR_COLOR)
            await ctx.reply(view=view)

    # ==================== KICK COMMANDS ====================
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member from the server"""
        
        # Validation checks
        if member.id == ctx.author.id:
            view = self.create_embed("❌ Cannot Kick Self", "You cannot kick yourself!", ERROR_COLOR)
            return await ctx.reply(view=view)
        
        if member.id == self.bot.user.id:
            view = self.create_embed("❌ Cannot Kick Bot", "You can't kick me!", ERROR_COLOR)
            return await ctx.reply(view=view)
        
        if member.id == ctx.guild.owner_id:
            view = self.create_embed("❌ Cannot Kick Owner", "I cannot kick the server owner!", ERROR_COLOR)
            return await ctx.reply(view=view)
        
        if not member.kickable:
            view = self.create_embed("❌ Cannot Kick User", "My role is not high enough to kick this user!", ERROR_COLOR)
            return await ctx.reply(view=view)
        
        try:
            full_reason = f"{ctx.author.tag} ({ctx.author.id}) | {reason}"
            
            # Try to DM the user
            try:
                dm_embed = discord.Embed(
                    title=f"👢 Kicked from {ctx.guild.name}",
                    description=f"**Executor:** {ctx.author.tag}\n**Reason:** {reason}",
                    color=WARNING_COLOR
                )
                await member.send(embed=dm_embed)
            except:
                pass
            
            await ctx.guild.kick(member, reason=full_reason)
            
            view = self.create_embed(
                "✅ Member Kicked",
                f"**User:** {member.name}\n**Reason:** {reason}",
                SUCCESS_COLOR
            )
            await ctx.reply(view=view)
        except Exception as e:
            view = self.create_embed("❌ Error", f"Failed to kick: {str(e)}", ERROR_COLOR)
            await ctx.reply(view=view)

    # ==================== MUTE/TIMEOUT COMMANDS ====================
    @commands.command(name="mute", aliases=["timeout", "stfu"])
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def mute(self, ctx, member: discord.Member, time: str = "27d", *, reason: str = "No reason provided"):
        """Mute/timeout a member"""
        
        # Validation checks
        if member.id == ctx.author.id:
            view = self.create_embed("❌ Cannot Mute Self", "You cannot mute yourself!", ERROR_COLOR)
            return await ctx.reply(view=view)
        
        if member.id == self.bot.user.id:
            view = self.create_embed("❌ Cannot Mute Bot", "You can't mute me!", ERROR_COLOR)
            return await ctx.reply(view=view)
        
        if member.id == ctx.guild.owner_id:
            view = self.create_embed("❌ Cannot Mute Owner", "I cannot mute the server owner!", ERROR_COLOR)
            return await ctx.reply(view=view)
        
        if member.is_timed_out():
            view = self.create_embed("❌ Already Muted", f"{member.name} is already muted!", ERROR_COLOR)
            return await ctx.reply(view=view)
        
        if member.guild_permissions.administrator:
            view = self.create_embed("❌ Cannot Mute Admin", f"{member.name} has administrator permissions!", ERROR_COLOR)
            return await ctx.reply(view=view)
        
        # Parse time
        time_multipliers = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400,
            'w': 604800
        }
        
        try:
            duration_seconds = int(time[:-1]) * time_multipliers.get(time[-1], 1)
            if duration_seconds > 2419200:  # 28 days max
                duration_seconds = 2419200
        except:
            view = self.create_embed("❌ Invalid Time", "Use format: 30s, 5m, 2h, 1d, 1w", ERROR_COLOR)
            return await ctx.reply(view=view)
        
        try:
            await member.timeout(timedelta(seconds=duration_seconds), reason=reason)
            
            # Try to DM the user
            try:
                dm_embed = discord.Embed(
                    title=f"🔇 Muted in {ctx.guild.name}",
                    description=f"**Duration:** {time}\n**Executor:** {ctx.author.tag}\n**Reason:** {reason}",
                    color=WARNING_COLOR
                )
                await member.send(embed=dm_embed)
            except:
                pass
            
            view = self.create_embed(
                "✅ Member Muted",
                f"**User:** {member.name}\n**Duration:** {time}\n**Reason:** {reason}",
                SUCCESS_COLOR
            )
            await ctx.reply(view=view)
        except Exception as e:
            view = self.create_embed("❌ Error", f"Failed to mute: {str(e)}", ERROR_COLOR)
            await ctx.reply(view=view)

    @commands.command(name="unmute")
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def unmute(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Unmute a member"""
        
        if not member.is_timed_out():
            view = self.create_embed("❌ Not Muted", f"{member.name} is not muted!", ERROR_COLOR)
            return await ctx.reply(view=view)
        
        try:
            await member.timeout(None, reason=reason)
            
            view = self.create_embed(
                "✅ Member Unmuted",
                f"**User:** {member.name}\n**Reason:** {reason}",
                SUCCESS_COLOR
            )
            await ctx.reply(view=view)
        except Exception as e:
            view = self.create_embed("❌ Error", f"Failed to unmute: {str(e)}", ERROR_COLOR)
            await ctx.reply(view=view)

    # ==================== PURGE/CLEAR COMMANDS ====================
    @commands.command(name="purge", aliases=["clear"])
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge(self, ctx, amount: int = 10):
        """Delete messages from the channel"""
        
        if amount < 1 or amount > 999:
            view = self.create_embed("❌ Invalid Amount", "Please specify between 1 and 999 messages!", ERROR_COLOR)
            return await ctx.reply(view=view)
        
        try:
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include command message
            
            status_msg = await ctx.send(f"🗑️ Deleting {amount} messages...")
            await asyncio.sleep(2)
            await status_msg.delete()
            
            view = self.create_embed(
                "✅ Messages Purged",
                f"Successfully deleted **{len(deleted) - 1}** messages!",
                SUCCESS_COLOR
            )
            await ctx.reply(view=view)
        except Exception as e:
            view = self.create_embed("❌ Error", f"Failed to purge: {str(e)}", ERROR_COLOR)
            await ctx.reply(view=view)

    @commands.command(name="purgebot")
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purgebot(self, ctx, amount: int = 50):
        """Delete bot messages from the channel"""
        
        if amount < 1 or amount > 999:
            view = self.create_embed("❌ Invalid Amount", "Please specify between 1 and 999 messages!", ERROR_COLOR)
            return await ctx.reply(view=view)
        
        try:
            def is_bot(msg):
                return msg.author.bot
            
            deleted = await ctx.channel.purge(limit=amount, check=is_bot)
            
            view = self.create_embed(
                "✅ Bot Messages Purged",
                f"Successfully deleted **{len(deleted)}** bot messages!",
                SUCCESS_COLOR
            )
            await ctx.reply(view=view)
        except Exception as e:
            view = self.create_embed("❌ Error", f"Failed to purge bot messages: {str(e)}", ERROR_COLOR)
            await ctx.reply(view=view)

    # ==================== CHANNEL LOCK/UNLOCK ====================
    @commands.command(name="lock")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def lock(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Lock a channel (disable messaging)"""
        
        channel = channel or ctx.channel
        
        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
            
            view = self.create_embed(
                "🔒 Channel Locked",
                f"**Channel:** {channel.name}\n\n**@everyone** can no longer send messages!",
                SUCCESS_COLOR
            )
            await ctx.reply(view=view)
        except Exception as e:
            view = self.create_embed("❌ Error", f"Failed to lock channel: {str(e)}", ERROR_COLOR)
            await ctx.reply(view=view)

    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def unlock(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Unlock a channel (enable messaging)"""
        
        channel = channel or ctx.channel
        
        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=True)
            
            view = self.create_embed(
                "🔓 Channel Unlocked",
                f"**Channel:** {channel.name}\n\n**@everyone** can now send messages!",
                SUCCESS_COLOR
            )
            await ctx.reply(view=view)
        except Exception as e:
            view = self.create_embed("❌ Error", f"Failed to unlock channel: {str(e)}", ERROR_COLOR)
            await ctx.reply(view=view)

    # ==================== NUKE COMMAND ====================
    @commands.command(name="nuke")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def nuke(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Nuke a channel (delete all messages)"""
        
        channel = channel or ctx.channel
        
        # Confirmation view
        view = NukeConfirmButton(ctx.author.id)
        embed = discord.Embed(
            title="⚠️ Confirm Channel Nuke",
            description=f"Are you sure you want to nuke {channel.name}?\n\n**This will delete all messages in this channel!**",
            color=WARNING_COLOR
        )
        msg = await ctx.reply(embed=embed, view=view)
        
        await view.wait()
        
        if view.result is None:
            view2 = self.create_embed("❌ Timeout", "You took too long to respond!", ERROR_COLOR)
            await ctx.reply(view=view2)
        elif view.result is False:
            view2 = self.create_embed("❌ Cancelled", "Channel nuke cancelled!", ERROR_COLOR)
            await ctx.reply(view=view2)
        else:
            try:
                # Clone the channel
                new_channel = await channel.clone(name=channel.name)
                
                # Set position and category
                await new_channel.edit(position=channel.position, category=channel.category)
                
                # Delete old channel
                await channel.delete()
                
                # Send success message in new channel
                view2 = self.create_embed(
                    "💣 Channel Nuked",
                    f"Successfully nuked and recreated the channel!\n\n**Executor:** {ctx.author.name}",
                    SUCCESS_COLOR
                )
                await new_channel.send(view=view2)
            except Exception as e:
                view2 = self.create_embed("❌ Error", f"Failed to nuke channel: {str(e)}", ERROR_COLOR)
                await ctx.reply(view=view2)


    # ==================== NICKNAME COMMANDS ====================
    @commands.command(name="nick")
    @commands.has_permissions(manage_nicknames=True)
    @commands.guild_only()
    async def nick(self, ctx, member: discord.Member, *, nickname: str):
        """Set a member's nickname"""
        
        if len(nickname) > 32:
            view = self.create_embed("❌ Nickname Too Long", "Nicknames must be 32 characters or less!", ERROR_COLOR)
            return await ctx.reply(view=view)
        
        try:
            await member.edit(nick=nickname, reason=f"Changed by {ctx.author.tag}")
            
            view = self.create_embed(
                "✅ Nickname Changed",
                f"**User:** {member.name}\n**New Nickname:** {nickname}",
                SUCCESS_COLOR
            )
            await ctx.reply(view=view)
        except discord.Forbidden:
            view = self.create_embed("❌ Permission Error", "My role is not high enough to change this user's nickname!", ERROR_COLOR)
            await ctx.reply(view=view)
        except Exception as e:
            view = self.create_embed("❌ Error", f"Failed to change nickname: {str(e)}", ERROR_COLOR)
            await ctx.reply(view=view)

    @commands.command(name="unnick", aliases=["removenick", "resetnick"])
    @commands.has_permissions(manage_nicknames=True)
    @commands.guild_only()
    async def unnick(self, ctx, member: discord.Member):
        """Remove a member's nickname"""
        
        try:
            await member.edit(nick=None, reason=f"Nickname removed by {ctx.author.tag}")
            
            view = self.create_embed(
                "✅ Nickname Removed",
                f"**User:** {member.name}\n**Nickname reset to:** {member.name}",
                SUCCESS_COLOR
            )
            await ctx.reply(view=view)
        except discord.Forbidden:
            view = self.create_embed("❌ Permission Error", "My role is not high enough to change this user's nickname!", ERROR_COLOR)
            await ctx.reply(view=view)
        except Exception as e:
            view = self.create_embed("❌ Error", f"Failed to remove nickname: {str(e)}", ERROR_COLOR)
            await ctx.reply(view=view)

    # ==================== MASS MODERATION ====================
    @commands.command(name="lockall", help="Locks down all channels in the server")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.channel)
    @commands.guild_only()
    async def lockall(self, ctx, *, reason=None):
        """Lock all channels in the server"""
        view = self.create_embed(
            "🔒 Locking Server",
            "Locking all channels in a few seconds...",
            WARNING_COLOR
        )
        await ctx.reply(view=view)
        
        for channel in ctx.guild.channels:
            try:
                await channel.set_permissions(
                    ctx.guild.default_role,
                    overwrite=discord.PermissionOverwrite(send_messages=False, read_messages=True),
                    reason=reason or f"Server lockdown by {ctx.author}"
                )
            except:
                pass

    @commands.command(name="unlockall", help="Unlocks all channels in the server")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.channel)
    @commands.guild_only()
    async def unlockall(self, ctx, *, reason=None):
        """Unlock all channels in the server"""
        view = self.create_embed(
            "🔓 Unlocking Server",
            "Unlocking all channels in a few seconds...",
            SUCCESS_COLOR
        )
        await ctx.reply(view=view)
        
        for channel in ctx.guild.channels:
            try:
                await channel.set_permissions(
                    ctx.guild.default_role,
                    overwrite=discord.PermissionOverwrite(send_messages=True, read_messages=True),
                    reason=reason or f"Server unlock by {ctx.author}"
                )
            except:
                pass

    @commands.command(name="hideall", help="Hides all channels from @everyone")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def hideall(self, ctx):
        """Hide all channels"""
        view = self.create_embed(
            "👁️ Hiding Channels",
            "Hiding all channels in a few seconds...",
            WARNING_COLOR
        )
        await ctx.reply(view=view)
        
        for channel in ctx.guild.channels:
            try:
                await channel.set_permissions(ctx.guild.default_role, view_channel=False)
            except:
                pass

    @commands.command(name="unhideall", help="Unhides all channels for @everyone")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def unhideall(self, ctx):
        """Unhide all channels"""
        view = self.create_embed(
            "👁️ Unhiding Channels",
            "Unhiding all channels in a few seconds...",
            SUCCESS_COLOR
        )
        await ctx.reply(view=view)
        
        for channel in ctx.guild.channels:
            try:
                await channel.set_permissions(ctx.guild.default_role, view_channel=True)
            except:
                pass

    @commands.command(name="hide", help="Hides a specific channel")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def hide(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Hide a channel"""
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = False
        await channel.set_permissions(
            ctx.guild.default_role,
            overwrite=overwrite,
            reason=f"Channel hidden by {ctx.author}"
        )
        
        view = self.create_embed(
            "✅ Channel Hidden",
            f"Successfully hidden {channel.name}",
            SUCCESS_COLOR
        )
        await ctx.reply(view=view)

    @commands.command(name="unhide", help="Unhides a specific channel")
    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    async def unhide(self, ctx, channel: Optional[discord.TextChannel] = None):
        """Unhide a channel"""
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = True
        await channel.set_permissions(
            ctx.guild.default_role,
            overwrite=overwrite,
            reason=f"Channel unhidden by {ctx.author}"
        )
        
        view = self.create_embed(
            "✅ Channel Unhidden",
            f"Successfully unhidden {channel.name}",
            SUCCESS_COLOR
        )
        await ctx.reply(view=view)

    # ==================== UTILITY ====================
    @commands.command(name="give", help="Give or remove a role from a member", aliases=["addrole", "roleadd", "rolegive"])
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def give(self, ctx, member: discord.Member, role: discord.Role):
        """Give or remove a role"""
        if role not in member.roles:
            await member.add_roles(role, reason=f"{ctx.author} (ID: {ctx.author.id})")
            view = self.create_embed(
                "✅ Role Added",
                f"Changed roles for {member.name}, +{role.name}",
                SUCCESS_COLOR
            )
            await ctx.send(view=view)
        else:
            await member.remove_roles(role, reason=f"{ctx.author} (ID: {ctx.author.id})")
            view = self.create_embed(
                "✅ Role Removed",
                f"Changed roles for {member.name}, -{role.name}",
                SUCCESS_COLOR
            )
            await ctx.send(view=view)

    @commands.command(name="audit", help="See recent audit log actions")
    @commands.has_permissions(view_audit_log=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def audit(self, ctx, limit: int = 10):
        """View audit logs"""
        if limit > 30:
            await ctx.reply("Action rejected, you are not allowed to fetch more than `30` entries.")
            return
        
        entries = []
        async for entry in ctx.guild.audit_logs(limit=limit):
            entries.append(f"**User:** `{entry.user}`\n**Action:** `{entry.action}`\n**Target:** `{entry.target}`\n**Reason:** {entry.reason or 'None'}\n")
        
        content = "\n".join(entries).replace("AuditLogAction.", "")
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## Audit Logs Of {ctx.guild.name}"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f">>> {content[:3900]}"))
        view.add_item(container)
        await ctx.reply(view=view)

    # ==================== ON MESSAGE EVENT ====================
    @commands.Cog.listener()
    async def on_message(self, message):
        """Check for non-media messages in media channels"""
        
        if message.author.bot or not message.guild:
            return
        
        try:
            db = self.bot.db
            config = await db.mediachannel.find_one({"guild_id": message.guild.id})
            
            if not config or not config.get("channel_id"):
                return
            
            if message.channel.id != config["channel_id"]:
                return
            
            # Check if message has attachments with media
            has_media = False
            for attachment in message.attachments:
                if attachment.content_type and ('image' in attachment.content_type or 'video' in attachment.content_type):
                    has_media = True
                    break
            
            # Delete if no media and has text
            if not has_media and message.content and not message.reference:
                try:
                    await message.delete()
                    
                    # Send warning
                    embed = discord.Embed(
                        title="📸 Media Channel Only",
                        description=f"Hey {message.author.name}! This channel is for media only.\n\nOnly images and videos are allowed here!",
                        color=WARNING_COLOR
                    )
                    msg = await message.channel.send(embed=embed)
                    await asyncio.sleep(5)
                    await msg.delete()
                except:
                    pass
        except:
            pass


async def setup(bot):
    await bot.add_cog(Moderation(bot))
