import discord
import logging
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay, Separator
from typing import Optional

logger = logging.getLogger(__name__)

COLOR = 0x2f3136
SUCCESS_COLOR = 0x00ff88
ERROR_COLOR = 0xff0033

class VerifyButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.success,
            label="Verify",
            custom_id="verify_button_comp",
            emoji="✅"
        )

    async def callback(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
            
        guild = interaction.guild
        
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("❌ Unable to verify you at this time.", ephemeral=True)
            return
            
        member = interaction.user
        
        # Get verification config from MongoDB
        db = interaction.client.db
        config = await db.verification.find_one({"guild_id": guild.id})
        
        if not config:
            await interaction.response.send_message("❌ Verification is not set up in this server.", ephemeral=True)
            return
        
        verified_role_id = config.get("verified_role")
        unverified_role_id = config.get("unverified_role")
        
        verified_role = guild.get_role(verified_role_id) if verified_role_id else None
        unverified_role = guild.get_role(unverified_role_id) if unverified_role_id else None
        
        try:
            if verified_role and verified_role not in member.roles:
                await member.add_roles(verified_role, reason="Verification")
            
            if unverified_role and unverified_role in member.roles:
                await member.remove_roles(unverified_role, reason="Verification")
            
            await interaction.response.send_message("✅ You have been verified successfully! Welcome to **" + guild.name + "**!", ephemeral=True)
            logger.info(f"{member.name} verified in {guild.name}")
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to manage your roles.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)


class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(VerifyButton())


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = COLOR

    async def get_verification_config(self, guild_id: int):
        db = self.bot.db
        return await db.verification.find_one({"guild_id": guild_id})

    async def update_verification_config(self, guild_id: int, **kwargs):
        db = self.bot.db
        await db.verification.update_one(
            {"guild_id": guild_id},
            {"$set": {**kwargs}},
            upsert=True
        )

    @commands.group(name="verification", aliases=['verify'], invoke_without_command=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _verification(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @_verification.command(name="setup", help="Setup verification channel and send verification message")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _verify_setup(self, ctx, channel: discord.TextChannel, setup_permissions: bool = True):
        config = await self.get_verification_config(ctx.guild.id)
        
        message_text = "Click the button below to verify yourself and get access to the server!"
        if config and config.get("message"):
            message_text = config["message"]
        
        # Create verification message with embed and persistent button
        embed = discord.Embed(
            title="🔐 Server Verification",
            description=message_text,
            color=self.color
        )
        embed.set_footer(text=f"{ctx.guild.name} Verification System")
        
        view = VerificationView()
        msg = await channel.send(embed=embed, view=view)
        
        await self.update_verification_config(ctx.guild.id, channel_id=channel.id)
        
        # Get unverified role if it exists
        if config and config.get("unverified_role"):
            unverified_role = ctx.guild.get_role(config["unverified_role"])
            if unverified_role and setup_permissions:
                setup_msg = await ctx.send("⚙️ Setting up permissions...")
                
                success_count = 0
                # Hide all channels from unverified role except verification channel
                for ch in ctx.guild.channels:
                    try:
                        if ch.id == channel.id:
                            await ch.set_permissions(unverified_role, read_messages=True, send_messages=False)
                        else:
                            await ch.set_permissions(unverified_role, read_messages=False)
                        success_count += 1
                    except:
                        pass
                
                await setup_msg.delete()
                
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("## ✅ Success"))
                container.add_item(Separator())
                container.add_item(TextDisplay(f"Verification system set up in {channel.name}\n\n✅ Configured permissions for {success_count} channels\n• Unverified members can only see {channel.name}\n• After verification, they'll see all channels\n\n**Next steps:**\n• Use `,verification setrole <role>` to set verified role\n• Use `,verification message <text>` to customize message"))
                view.add_item(container)
                await ctx.reply(view=view)
                return
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay("## ✅ Success"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"Verification system set up in {channel.name}\n\n**Next steps:**\n• Use `,verification setrole <role>` to set verified role\n• Use `,verification setunverified <role>` to set unverified role\n• Use `,verification message <text>` to customize message\n• Run `,verification lockdown` to hide all channels from unverified users"))
        view.add_item(container)
        await ctx.reply(view=view)

    @_verification.command(name="setrole", help="Set the role to give when users verify")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _verify_setrole(self, ctx, *, role: discord.Role):
        if role >= ctx.guild.me.top_role:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ {role.name} is higher than or equal to my top role."))
            view.add_item(container)
            await ctx.reply(view=view)
            return
        
        await self.update_verification_config(ctx.guild.id, verified_role=role.id)
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay("## ✅ Success"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"Verified role set to {role.name}"))
        view.add_item(container)
        await ctx.reply(view=view)

    @_verification.command(name="setunverified", help="Set the role to remove when users verify")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _verify_setunverified(self, ctx, *, role: discord.Role):
        if role >= ctx.guild.me.top_role:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ {role.name} is higher than or equal to my top role."))
            view.add_item(container)
            await ctx.reply(view=view)
            return
        
        await self.update_verification_config(ctx.guild.id, unverified_role=role.id)
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay("## ✅ Success"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"Unverified role set to {role.name}\n\n**Note:** This role will be automatically added to new members and removed when they verify."))
        view.add_item(container)
        await ctx.reply(view=view)

    @_verification.command(name="message", help="Set custom verification message")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _verify_message(self, ctx, *, message: str):
        await self.update_verification_config(ctx.guild.id, message=message)
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay("## ✅ Success"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"Verification message updated to:\n\n{message}"))
        view.add_item(container)
        await ctx.reply(view=view)

    @_verification.command(name="config", help="View current verification configuration")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _verify_config(self, ctx):
        config = await self.get_verification_config(ctx.guild.id)
        
        if not config:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ No Configuration"))
            container.add_item(Separator())
            container.add_item(TextDisplay("Verification system is not set up in this server."))
            view.add_item(container)
            await ctx.reply(view=view)
            return
        
        channel_id = config.get("channel_id")
        verified_role_id = config.get("verified_role")
        unverified_role_id = config.get("unverified_role")
        message = config.get("message")
        enabled = config.get("enabled", 1)
        
        channel = ctx.guild.get_channel(channel_id) if channel_id else None
        verified_role = ctx.guild.get_role(verified_role_id) if verified_role_id else None
        unverified_role = ctx.guild.get_role(unverified_role_id) if unverified_role_id else None
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay("## 🔐 Verification Configuration"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"**Status:** {'✅ Enabled' if enabled else '❌ Disabled'}"))
        container.add_item(TextDisplay(f"**Verification Channel:** {channel.name if channel else '❌ Not set'}"))
        container.add_item(TextDisplay(f"**Verified Role:** {verified_role.name if verified_role else '❌ Not set'}"))
        container.add_item(TextDisplay(f"**Unverified Role:** {unverified_role.name if unverified_role else '❌ Not set'}"))
        if message:
            container.add_item(TextDisplay(f"**Custom Message:** {message[:100] + '...' if len(message) > 100 else message}"))
        view.add_item(container)
        await ctx.reply(view=view)

    @_verification.command(name="enable", help="Enable verification system")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _verify_enable(self, ctx):
        await self.update_verification_config(ctx.guild.id, enabled=1)
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay("## ✅ Success"))
        container.add_item(Separator())
        container.add_item(TextDisplay("Verification system has been enabled."))
        view.add_item(container)
        await ctx.reply(view=view)

    @_verification.command(name="disable", help="Disable verification system")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _verify_disable(self, ctx):
        await self.update_verification_config(ctx.guild.id, enabled=0)
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay("## ✅ Success"))
        container.add_item(Separator())
        container.add_item(TextDisplay("Verification system has been disabled."))
        view.add_item(container)
        await ctx.reply(view=view)

    @_verification.command(name="reset", help="Reset verification configuration")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _verify_reset(self, ctx):
        await self.bot.db.verification.delete_one({"guild_id": ctx.guild.id})
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay("## ✅ Success"))
        container.add_item(Separator())
        container.add_item(TextDisplay("Verification configuration has been reset."))
        view.add_item(container)
        await ctx.reply(view=view)

    @_verification.command(name="lockdown", help="Hide all channels from unverified users except verification channel")
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def _verify_lockdown(self, ctx):
        config = await self.get_verification_config(ctx.guild.id)
        
        if not config:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Error"))
            container.add_item(Separator())
            container.add_item(TextDisplay("Please set up verification first using `,verification setup <channel>`"))
            view.add_item(container)
            await ctx.reply(view=view)
            return
        
        unverified_role_id = config.get("unverified_role")
        channel_id = config.get("channel_id")
        
        if not unverified_role_id:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Error"))
            container.add_item(Separator())
            container.add_item(TextDisplay("Please set the unverified role first using `,verification setunverified <role>`"))
            view.add_item(container)
            await ctx.reply(view=view)
            return
        
        unverified_role = ctx.guild.get_role(unverified_role_id)
        if not unverified_role:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Error"))
            container.add_item(Separator())
            container.add_item(TextDisplay("Unverified role not found."))
            view.add_item(container)
            await ctx.reply(view=view)
            return
        
        verification_channel = ctx.guild.get_channel(channel_id) if channel_id else None
        
        progress_msg = await ctx.send("⚙️ Setting up lockdown...")
        
        success_count = 0
        for channel in ctx.guild.channels:
            try:
                if verification_channel and channel.id == verification_channel.id:
                    await channel.set_permissions(unverified_role, read_messages=True, send_messages=False)
                else:
                    await channel.set_permissions(unverified_role, read_messages=False)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to set permissions for {channel.name}: {e}")
        
        await progress_msg.delete()
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay("## ✅ Lockdown Complete"))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"✅ Configured {success_count} channels\n\n• Unverified users can only see {verification_channel.name if verification_channel else 'the verification channel'}\n• After verification, they'll see all channels"))
        view.add_item(container)
        await ctx.reply(view=view)


async def setup(bot):
    await bot.add_cog(Verification(bot))
    bot.add_view(VerificationView())
