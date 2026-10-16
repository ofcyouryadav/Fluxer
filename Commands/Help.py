from typing import List, Optional, Union
import discord 
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
import os
from discord import app_commands 
from discord.ui import LayoutView, Container, Section, TextDisplay, Separator, ActionRow, Button, Select

# Custom emojis and styles
EMOJIS = {
    "home": "<:HOME:1435491250982621226>",
    "music": "<:music:1435491622031724595>",
    "filter": "<:filters:1435491760171122844>",
    "spotify": "<:Spotify:1435491869458169988>",
    "playlist": "<:playlists:1435492006448070666>",
    "config": "<:Settings:1435492265656193055>",
    "commands": "<:Zycron_Slash:1416048107619094611>",
    "delete": "<:uo_delete:1435494431347445770>",
    "amf": "🎵",
    "leveling": "📊",
    "serverutility": "📈",
    "birthday": "🎂",
    "giveaway": "🎁",
    "voice": "🎙️",
    "games": "🎮",
    "media": "🎬",
    "vcroles": "🎙️",
    "joindm": "📬",
    "autopfp": "📸",
    "greet": "👋",
    "boost": "🚀",
    "mediachannel": "📸",
    "moderation": "🛡️",
    "economy": "💰",
    "afk": "💤",
    "automod": "🛡️",
    "autoresponder": "🤖",
    "autorole": "🎭",
    "customrole": "✨",
    "general": "📋",
    "ignore": "🚫",
    "jointocreate": "🔗",
    "steal": "🎨",
    "ship": "💕",
    "reactionrole": "🎭",
    "verification": "✅",
    "helper": "ℹ️",
    "vanityroles": "✨",
    "botavatar": "🖼️",
    "voice": "🎙️",
    "notify": "🔔"
}

CATEGORY_DESCRIPTIONS = {
  "music": "Play, skip, and manage songs",
  "filter": "Add sound effects to music",
  "spotify": "Connect & Play music directly from Spotify",
  "playlist": "Save and share playlists",
  "config": "Change bot and server settings | 247notifier, playingredirect",
  "amf": "Use advanced music tools",
  "leveling": "XP, levels, rank cards, stats, and notifications",
  "serverutility": "Track invites, voice time, messages, and leaderboards",
  "birthday": "Birthday celebrations and tracking",
  "giveaway": "Create and manage giveaways",
  "voice": "Voice channel moderation",
  "games": "Fun games and activities",
  "media": "Memes, images, and text effects",
  "vcroles": "Voice channel role management",
  "joindm": "Welcome DMs for new members",
  "autopfp": "Auto-post profile pictures | setup, disable, remove, list, post",
  "greet": "Welcome messages for new members",
  "boost": "Server boost notifications",
  "mediachannel": "Create and manage media channels",
  "moderation": "Moderation and server management",
  "economy": "Currency system with daily rewards and shop",
  "afk": "Set AFK status when away",
  "autoresponder": "Automatic message responses",
  "autorole": "Auto-assign roles to new members",
  "customrole": "Create and manage custom roles",
  "general": "General utility commands",
  "ignore": "Ignore channels for bot commands",
  "jointocreate": "Voice channel creation system",
  "steal": "Steal emojis and stickers from other servers",
  "ship": "Love compatibility tester",
  "reactionrole": "Reaction role management panel",
  "verification": "User verification and role management",
  "helper": "Utility commands for server and user info",
  "vanityroles": "Auto-assign roles based on custom status",
  "botavatar": "Customize bot avatar and banner per server",
  "notify": "Notification settings for various features"
}

temp_icon = "https://cdn.discordapp.com/avatars/914785889329233931/acc9c19e09a7896237899937b57d9d89.png?size=1024"

def get_full_command_name(command: Union[commands.Command, commands.Group]) -> List[str]:
    """Get the full command name including parent commands."""
    if isinstance(command, commands.Group):
        return [subcommand.qualified_name for subcommand in command.walk_commands()]
    return [command.qualified_name]

def format_commands_list(commands: List[str]) -> str:
    """Format commands list to ensure full command names are displayed."""
    unique_commands = sorted(set(commands))
    return ", ".join(f"`{cmd}`" for cmd in unique_commands)

class HelpView(LayoutView):
    def __init__(self, ctx: commands.Context, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.bot = ctx.bot
        self.current_category = "home"
        self.all_commands_page = 0
        self.total_pages = 12
        
        # Initial render
        self.update_display("home")

    def update_display(self, category: str):
        self.current_category = category
        self.clear_items()
        
        container = Container()
        
        # Content generation based on category
        if category == "home":
            total_commands = len([cmd for cmd in self.bot.commands if not cmd.hidden])
            
            container.add_item(TextDisplay("## Fluxer Bot Help"))
            container.add_item(Separator())
            
            description = (
                f"**Music**\n"
                f"**Filters**\n"
                f"**Spotify**\n"
                f"**Playlist**\n"
                f"**Config**\n"
                f"**Leveling**\n"
                f"**Server Utility**\n"
                f"**Birthday**\n"
                f"**Giveaway**\n"
                f"**Verification**\n"
                f"**Voice**\n"
                f"**Games**\n"
                f"**Media**\n"
                f"**VC Roles**\n"
                f"**Join DM**\n"
                f"**Auto PFP**\n"
                f"**Greet**\n"
                f"**Boost**\n"
                f"**Media Channel**\n"
                f"**Moderation**\n"
                f"**Economy**\n"
                f"**AFK**\n"
                f"**Ship**\n"
                f"**Auto Responder**\n"
                f"**AutoRole**\n"
                f"**Custom Role**\n"
                f"**General**\n"
                f"**Ignore**\n"
                f"**Join to Create**\n"
                f"**Steal**\n"
                f"**Reaction Role**\n"
                f"**Helper**\n"
                f"**Vanity Roles**\n\n"
                f"-# Total Commands: {total_commands} | Use the dropdown below to navigate."
            )
            
            from discord.ui import Thumbnail
            thumb = Thumbnail(temp_icon)
            section = Section(TextDisplay(description), accessory=thumb)
            container.add_item(section)

        elif category == "all_commands":
            # Pagination for all commands
            container.add_item(TextDisplay(f"## All Commands (Page {self.all_commands_page + 1}/{self.total_pages})"))
            container.add_item(Separator())
            
            # Define pages - 3 categories per page
            pages = [
                ["Music", "Filter", "Spotifyx"],
                ["PlaylistCommands", "Config", "LevelingSystem"],
                ["ServerUtility", "Giveaway", "Verification"],
                ["Greet", "Boost", "MediaChannel"],
                ["Moderation", "Games", "Media"],
                ["VCRoles", "JoinDM", "Birthday"],
                ["VoiceModeration", "Economy", "afk"],
                ["Ship", "Autoresponder", "Autorole"],
                ["Customrole", "General", "Ignore"],
                ["JoinToCreate", "Steal", "ReactionRole"],
                ["AutoPFP", "Helper", "VanityRoles"],
                ["BotAvatar"]
            ]
            
            current_cogs = pages[self.all_commands_page]
            
            for cog_name in current_cogs:
                cog = self.bot.get_cog(cog_name)
                if cog:
                    commands_list = []
                    for cmd in cog.walk_commands():
                        commands_list.extend(get_full_command_name(cmd))
                    
                    if commands_list:
                        formatted = format_commands_list(commands_list)
                        # Map cog name to display name
                        display_map = {
                            "Music": "Music",
                            "Filter": "Filter",
                            "Spotifyx": "Spotify",
                            "PlaylistCommands": "Playlist",
                            "Config": "Config",
                            "LevelingSystem": "Leveling",
                            "ServerUtility": "Server Utility",
                            "Giveaway": "Giveaway",
                            "Verification": "Verification",
                            "AutoPFP": "Auto PFP",
                            "Greet": "Greet",
                            "Boost": "Boost",
                            "MediaChannel": "Media Channel",
                            "Moderation": "Moderation",
                            "Games": "Games",
                            "Media": "Media",
                            "VCRoles": "VC Roles",
                            "JoinDM": "Join DM",
                            "Birthday": "Birthday",
                            "VoiceModeration": "Voice Moderation",
                            "Economy": "Economy",
                            "afk": "AFK",
                            "Ship": "Ship",
                            "Autoresponder": "Auto Responder",
                            "Autorole": "AutoRole",
                            "Customrole": "Custom Role",
                            "General": "General",
                            "Ignore": "Ignore",
                            "JoinToCreate": "Join to Create",
                            "Steal": "Steal",
                            "ReactionRole": "Reaction Role",
                            "Helper": "Helper",
                            "VanityRoles": "Vanity Roles",
                            "BotAvatar": "Bot Avatar"
                        }
                        display_name = display_map.get(cog_name, cog_name)
                        
                        container.add_item(TextDisplay(f"### {display_name}"))
                        container.add_item(TextDisplay(formatted))
                        container.add_item(Separator())

        else:
            # Category pages
            title = f"{category.capitalize()} Commands"
                
            container.add_item(TextDisplay(f"## {title}"))
            container.add_item(Separator())
            
            # Get commands
            cog_map = {
                "music": "Music",
                "filter": "Filter",
                "spotify": "Spotifyx",
                "playlist": "PlaylistCommands",
                "config": "Config",
                "leveling": "LevelingSystem",
                "serverutility": "ServerUtility",
                "birthday": "Birthday",
                "giveaway": "Giveaway",
                "verification": "Verification",
                "voice": "VoiceModeration",
                "games": "Games",
                "media": "Media",
                "vcroles": "VCRoles",
                "joindm": "JoinDM",
                "autopfp": "AutoPFP",
                "greet": "Greet",
                "boost": "Boost",
                "mediachannel": "MediaChannel",
                "moderation": "Moderation",
                "economy": "Economy",
                "afk": "afk",
                "ship": "Ship",
                "autoresponder": "Autoresponder",
                "autorole": "Autorole",
                "customrole": "Customrole",
                "general": "General",
                "ignore": "Ignore",
                "jointocreate": "JoinToCreate",
                "steal": "Steal",
                "reactionrole": "ReactionRole",
                "helper": "Helper",
                "vanityroles": "VanityRoles",
                "botavatar": "BotAvatar"
            }
            
            cog_name = cog_map.get(category)
            cog = self.bot.get_cog(cog_name) if cog_name else None
            
            if cog:
                commands_list = []
                for cmd in cog.walk_commands():
                    commands_list.extend(get_full_command_name(cmd))
                
                formatted = format_commands_list(commands_list)
                desc = f"{CATEGORY_DESCRIPTIONS.get(category, '')}\n\n**Available Commands:**\n{formatted}"
                
                from discord.ui import Thumbnail
                thumb = Thumbnail(temp_icon)
                section = Section(TextDisplay(desc), accessory=thumb)
                container.add_item(section)
                
                container.add_item(Separator())
                container.add_item(TextDisplay(f"Total: {len(commands_list)} commands"))
            else:
                container.add_item(TextDisplay(f"Module {cog_name} not loaded."))

        container.add_item(Separator())
        
        # 1. First Dropdown - Core Features (separate ActionRow)
        options_1 = [
            discord.SelectOption(label="Home", value="home"),
            discord.SelectOption(label="Music", value="music"),
            discord.SelectOption(label="Filters", value="filter"),
            discord.SelectOption(label="Spotify", value="spotify"),
            discord.SelectOption(label="Playlist", value="playlist"),
            discord.SelectOption(label="Config", value="config"),
            discord.SelectOption(label="Leveling", value="leveling"),
            discord.SelectOption(label="Server Utility", value="serverutility"),
            discord.SelectOption(label="Giveaway", value="giveaway"),
            discord.SelectOption(label="Verification", value="verification"),
            discord.SelectOption(label="Moderation", value="moderation"),
            discord.SelectOption(label="Birthday", value="birthday"),
            discord.SelectOption(label="Voice", value="voice"),
            discord.SelectOption(label="Greet", value="greet"),
            discord.SelectOption(label="Boost", value="boost"),
        ]
        
        select_1 = Select(placeholder="Core Features", options=options_1, custom_id=f"help_select_1_{self.ctx.author.id}")
        
        async def select_callback_1(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("Not your menu!", ephemeral=True)
            self.update_display(select_1.values[0])
            await interaction.response.edit_message(view=self)
            
        select_1.callback = select_callback_1
        
        select_1_row = ActionRow()
        select_1_row.add_item(select_1)
        container.add_item(select_1_row)
        
        # 2. Second Dropdown - Additional Features (separate ActionRow)
        options_2 = [
            discord.SelectOption(label="Media Channel", value="mediachannel"),
            discord.SelectOption(label="Games", value="games"),
            discord.SelectOption(label="Media", value="media"),
            discord.SelectOption(label="VC Roles", value="vcroles"),
            discord.SelectOption(label="Join DM", value="joindm"),
            discord.SelectOption(label="Auto PFP", value="autopfp"),
            discord.SelectOption(label="Vanity Roles", value="vanityroles"),
            discord.SelectOption(label="Economy", value="economy"),
            discord.SelectOption(label="AFK", value="afk"),
            discord.SelectOption(label="Ship", value="ship"),
            discord.SelectOption(label="Auto Responder", value="autoresponder"),
            discord.SelectOption(label="AutoRole", value="autorole"),
            discord.SelectOption(label="General", value="general"),
            discord.SelectOption(label="Bot Avatar", value="botavatar"),
        ]
        
        select_2 = Select(placeholder="Additional Features", options=options_2, custom_id=f"help_select_2_{self.ctx.author.id}")
        
        async def select_callback_2(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("Not your menu!", ephemeral=True)
            self.update_display(select_2.values[0])
            await interaction.response.edit_message(view=self)
            
        select_2.callback = select_callback_2
        
        select_2_row = ActionRow()
        select_2_row.add_item(select_2)
        container.add_item(select_2_row)
        
        # 3. Third Dropdown - More Features (separate ActionRow)
        options_3 = [
            discord.SelectOption(label="Custom Role", value="customrole"),
            discord.SelectOption(label="Ignore", value="ignore"),
            discord.SelectOption(label="Join to Create", value="jointocreate"),
            discord.SelectOption(label="Steal", value="steal"),
            discord.SelectOption(label="Reaction Role", value="reactionrole"),
            discord.SelectOption(label="Helper", value="helper"),
        ]
        
        select_3 = Select(placeholder="More Features", options=options_3, custom_id=f"help_select_3_{self.ctx.author.id}")
        
        async def select_callback_3(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("Not your menu!", ephemeral=True)
            self.update_display(select_3.values[0])
            await interaction.response.edit_message(view=self)
            
        select_3.callback = select_callback_3
        
        select_3_row = ActionRow()
        select_3_row.add_item(select_3)
        container.add_item(select_3_row)
        
        # Buttons ActionRow (separate from selects)
        buttons_action_row = ActionRow()
        
        # 3. Buttons
        if category == "all_commands":
            # Navigation Buttons
            prev_btn = Button(style=discord.ButtonStyle.primary, label="Previous", disabled=(self.all_commands_page == 0), custom_id=f"help_prev_{self.ctx.author.id}")
            async def prev_callback(interaction: discord.Interaction):
                if interaction.user != self.ctx.author:
                    return await interaction.response.send_message("Not your menu!", ephemeral=True)
                self.all_commands_page = max(0, self.all_commands_page - 1)
                self.update_display("all_commands")
                await interaction.response.edit_message(view=self)
            prev_btn.callback = prev_callback
            buttons_action_row.add_item(prev_btn)
            
            next_btn = Button(style=discord.ButtonStyle.primary, label="Next", disabled=(self.all_commands_page == self.total_pages - 1), custom_id=f"help_next_{self.ctx.author.id}")
            async def next_callback(interaction: discord.Interaction):
                if interaction.user != self.ctx.author:
                    return await interaction.response.send_message("Not your menu!", ephemeral=True)
                self.all_commands_page = min(self.total_pages - 1, self.all_commands_page + 1)
                self.update_display("all_commands")
                await interaction.response.edit_message(view=self)
            next_btn.callback = next_callback
            buttons_action_row.add_item(next_btn)
            
        else:
            # All Commands Button
            all_btn = Button(style=discord.ButtonStyle.green, label="All Commands", custom_id=f"help_all_{self.ctx.author.id}")
            async def all_callback(interaction: discord.Interaction):
                if interaction.user != self.ctx.author:
                    return await interaction.response.send_message("Not your menu!", ephemeral=True)
                self.all_commands_page = 0
                self.update_display("all_commands")
                await interaction.response.edit_message(view=self)
            all_btn.callback = all_callback
            buttons_action_row.add_item(all_btn)
        
        # Close Button
        close_btn = Button(style=discord.ButtonStyle.red, label="Close", custom_id=f"help_close_{self.ctx.author.id}")
        async def close_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("Not your menu!", ephemeral=True)
            if interaction.message:
                await interaction.message.delete()
        close_btn.callback = close_callback
        buttons_action_row.add_item(close_btn)
        
        container.add_item(buttons_action_row)
        self.add_item(container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This menu is not for you!", ephemeral=True)
            return False
        return True

class help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.remove_command("help")
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 3.0, commands.BucketType.user)

    def cog_check(self, ctx: commands.Context):
        bucket = self.cooldown.get_bucket(ctx.message)
        if bucket:
            retry_after = bucket.update_rate_limit()
            if retry_after:
                raise commands.CommandOnCooldown(bucket, retry_after, commands.BucketType.user)
        return True

    @commands.command(name="help", aliases=['h'])
    @cooldown(1, 4, BucketType.user)
    async def help(self, ctx: commands.Context, *, command: Optional[str] = None):
        """Get help with bot commands and features"""
        print(f"Help command invoked by {ctx.author} with argument: {command}")
        if command is None:
            # Component V2 Help Menu
            view = HelpView(ctx)
            print("Sending main help menu")
            await ctx.reply(view=view)

        else:
            cmd = self.bot.get_command(command.lower())
            if cmd is None:
                print(f"Command not found: {command}")
                # Use quick layout for error
                from discord.ui import LayoutView, Container, TextDisplay
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay(f"Command `{command}` not found."))
                view.add_item(container)
                await ctx.reply(view=view)
            else:
                print(f"Showing help for command: {cmd.name}")
                # Use Component V2 for specific command help
                from discord.ui import LayoutView, Container, TextDisplay, Separator, Section, Thumbnail
                view = LayoutView()
                container = Container()
                
                container.add_item(TextDisplay(f"## Command: {cmd.qualified_name}"))
                container.add_item(Separator())
                
                desc = "```yaml\n<> = Required Arguments\n[] = Optional Arguments\n```\n"
                
                if cmd.description:
                    desc += f"**Description:**\n{cmd.description}\n\n"
                if cmd.aliases:
                    desc += f"**Aliases:**\n" + ", ".join(f"`{alias}`" for alias in cmd.aliases) + "\n\n"
                if hasattr(cmd, 'usage') and cmd.usage:
                    desc += f"**Usage:**\n`{ctx.prefix}{cmd.qualified_name} {cmd.usage}`"
                
                thumb = Thumbnail(temp_icon)
                section = Section(TextDisplay(desc), accessory=thumb)
                container.add_item(section)
                
                container.add_item(Separator())
                container.add_item(TextDisplay(f"-# Type {ctx.prefix}help for all commands"))
                
                view.add_item(container)
                await ctx.reply(view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(help(bot))