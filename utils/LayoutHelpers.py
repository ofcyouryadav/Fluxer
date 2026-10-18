import discord
from discord import ui
from discord.ui import LayoutView, Container, Section, TextDisplay, Separator, MediaGallery, ActionRow, Button, Thumbnail
from typing import Optional, List, Union
from discord.enums import ButtonStyle

class LayoutHelpers:
    """Helper utilities for creating Component V2 layouts"""
    
    DEFAULT_COLOR = 0x2f3136
    
    @staticmethod
    def create_basic_container(
        title: str,
        description: str,
        color: int = DEFAULT_COLOR,
        thumbnail_url: Optional[str] = None
    ) -> Container:
        """Create a basic container with title and description"""
        container = Container()
        
        if title:
            container.add_item(TextDisplay(f"## {title}"))
            container.add_item(Separator())
        
        if thumbnail_url:
            thumb = Thumbnail(thumbnail_url)
            section = Section(TextDisplay(description), accessory=thumb)
            container.add_item(section)
        else:
            container.add_item(TextDisplay(description))
        
        return container
    
    @staticmethod
    def create_info_container(
        title: str,
        fields: List[tuple],  # List of (name, value) tuples
        color: int = DEFAULT_COLOR,
        thumbnail_url: Optional[str] = None
    ) -> Container:
        """Create container for displaying information with fields"""
        container = Container()
        
        # Add title
        if title:
            container.add_item(TextDisplay(f"## {title}"))
            container.add_item(Separator())
        
        # Add fields
        field_text = []
        for name, value in fields:
            field_text.append(f"**{name}:**\n{value}")
        
        description = "\n\n".join(field_text)
        
        if thumbnail_url:
            thumb = Thumbnail(thumbnail_url)
            section = Section(TextDisplay(description), accessory=thumb)
            container.add_item(section)
        else:
            container.add_item(TextDisplay(description))
        
        return container
    
    @staticmethod
    def add_media_gallery(container: Container, media_url: str) -> Container:
        """Add media gallery to container"""
        gallery = MediaGallery()
        gallery.add_item(media=media_url)
        container.add_item(gallery)
        return container
    
    @staticmethod
    def create_button_row(buttons: List[dict]) -> ActionRow:
        """
        Create action row with buttons
        buttons: List of dicts with keys: label, url/custom_id, style
        Example: [{"label": "Click Me", "url": "https://...", "style": "secondary"}]
        """
        row = ActionRow()
        for btn in buttons:
            style = getattr(ButtonStyle, btn.get("style", "secondary"))
            if "url" in btn:
                row.add_item(Button(style=style, label=btn["label"], url=btn["url"]))
            else:
                row.add_item(Button(style=style, label=btn["label"], custom_id=btn.get("custom_id", btn["label"])))
        return row
    
    @staticmethod
    def create_error_view(message: str, color: int = 0xff0000) -> LayoutView:
        """Create error message view"""
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"❌ **Error**\n{message}"))
        view.add_item(container)
        return view
    
    @staticmethod
    def create_success_view(message: str, color: int = 0x00ff00) -> LayoutView:
        """Create success message view"""
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"✅ **Success**\n{message}"))
        view.add_item(container)
        return view

    @staticmethod
    def create_simple_layout(description: str, title: Optional[str] = None, color: int = DEFAULT_COLOR) -> LayoutView:
        """Create a simple layout with just text/description"""
        view = LayoutView()
        container = Container()
        
        if title:
            container.add_item(TextDisplay(f"## {title}"))
            container.add_item(Separator())
            
        container.add_item(TextDisplay(description))
        view.add_item(container)
        return view


class MusicLayoutTemplates:
    """Templates for music-related layouts"""
    
    @staticmethod
    def now_playing(
        title: str,
        author: str,
        duration: str,
        requester: str,
        artwork_url: str,
        track_url: Optional[str] = None,
        volume: int = 100,
        queue_length: int = 0
    ) -> LayoutView:
        """Create now playing layout"""
        view = LayoutView()
        container = Container()
        
        # Title
        container.add_item(TextDisplay("## Now Playing"))
        container.add_item(Separator())
        
        # Track info with thumbnail
        track_info = f"**[{title}]({track_url or 'https://discord.com'})**\n"
        track_info += f"**Artist:** {author}\n"
        track_info += f"**Duration:** {duration}\n"
        track_info += f"**Requested by:** {requester}\n"
        track_info += f"**Volume:** {volume}%"
        if queue_length > 0:
            track_info += f"\n**Queue:** {queue_length} tracks"
        
        thumb = Thumbnail(artwork_url)
        section = Section(TextDisplay(track_info), accessory=thumb)
        container.add_item(section)
        
        # Media gallery
        container.add_item(Separator())
        gallery = MediaGallery()
        gallery.add_item(media=artwork_url)
        container.add_item(gallery)
        
        view.add_item(container)
        return view
    
    @staticmethod
    def queue_view(tracks: List[dict], total_duration: str) -> LayoutView:
        """Create queue view"""
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## Queue - {len(tracks)} tracks"))
        container.add_item(Separator())
        
        track_list = []
        for i, track in enumerate(tracks[:10], 1):  # Show first 10
            track_list.append(f"`{i}.` **[{track['title']}]({track.get('url', 'https://discord.com')})** - `{track['duration']}`")
        
        container.add_item(TextDisplay("\n".join(track_list)))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"**Total Duration:** {total_duration}"))
        
        view.add_item(container)
        return view


class UserLayoutTemplates:
    """Templates for user-related layouts"""
    
    @staticmethod
    def avatar_view(
        member: Union[discord.Member, discord.User],
        bot
    ) -> LayoutView:
        """Create avatar display view"""
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"**[{member.name}'s](https://discord.com/users/{member.id}) avatar**"))
        container.add_item(Separator())
        
        # Format links
        png = member.display_avatar.with_format('png').url
        jpg = member.display_avatar.with_format('jpg').url
        webp = member.display_avatar.with_format('webp').url
        
        container.add_item(TextDisplay(f"[`PNG`]({png}) | [`JPG`]({jpg}) | [`WEBP`]({webp})"))
        
        # Media gallery
        gallery = MediaGallery()
        gallery.add_item(media=member.display_avatar.url)
        container.add_item(gallery)
        
        container.add_item(Separator())
        
        # Download buttons
        buttons = ActionRow()
        buttons.add_item(Button(style=ButtonStyle.secondary, label="PNG", url=png))
        buttons.add_item(Button(style=ButtonStyle.secondary, label="JPG", url=jpg))
        container.add_item(buttons)
        
        view.add_item(container)
        return view
    
    @staticmethod
    def user_info_view(member: discord.Member) -> LayoutView:
        """Create user info view"""
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## {member.name}'s Information"))
        container.add_item(Separator())
        
        # User info
        info = f"**ID:** `{member.id}`\n"
        info += f"**Created:** <t:{int(member.created_at.timestamp())}:R>\n"
        if isinstance(member, discord.Member):
            info += f"**Joined:** <t:{int(member.joined_at.timestamp())}:R>\n"
            info += f"**Roles:** {len(member.roles)}\n"
        
        thumb = Thumbnail(member.display_avatar.url)
        section = Section(TextDisplay(info), accessory=thumb)
        container.add_item(section)
        
        view.add_item(container)
        return view


class ServerLayoutTemplates:
    """Templates for server-related layouts"""
    
    @staticmethod
    def server_icon_view(guild: discord.Guild) -> LayoutView:
        """Create server icon view"""
        view = LayoutView()
        container = Container()
        
        if not guild.icon:
            container.add_item(TextDisplay(f"❌ **{guild.name} does not have a server icon.**"))
            view.add_item(container)
            return view
        
        container.add_item(TextDisplay(f"## {guild.name}'s Server Icon"))
        container.add_item(Separator())
        
        # Format links
        png = guild.icon.with_format('png').url
        jpg = guild.icon.with_format('jpg').url
        webp = guild.icon.with_format('webp').url
        
        links = f"[`PNG`]({png}) | [`JPG`]({jpg}) | [`WEBP`]({webp})"
        if guild.icon.is_animated():
            gif = guild.icon.with_format('gif').url
            links += f" | [`GIF`]({gif})"
        
        container.add_item(TextDisplay(links))
        
        # Media gallery
        gallery = MediaGallery()
        gallery.add_item(media=guild.icon.url)
        container.add_item(gallery)
        
        # Download buttons
        buttons = ActionRow()
        buttons.add_item(Button(style=ButtonStyle.secondary, label="PNG", url=png))
        buttons.add_item(Button(style=ButtonStyle.secondary, label="JPG", url=jpg))
        if guild.icon.is_animated():
            buttons.add_item(Button(style=ButtonStyle.secondary, label="GIF", url=gif))
        container.add_item(buttons)
        
        view.add_item(container)
        return view


class BotLayoutTemplates:
    """Templates for bot-related layouts"""
    
    @staticmethod
    def invite_view(bot) -> LayoutView:
        """Create invite view"""
        view = LayoutView()
        container = Container()
        
        thumb = Thumbnail(bot.user.avatar.url)
        text = f"## {bot.user.name} - Invite Links\n"
        text += "Brings fast and multipurpose features with just on your fingertips.\n\n"
        text += f"-# Use the button below to add {bot.user.name} to your server!"
        
        section = Section(TextDisplay(text), accessory=thumb)
        container.add_item(section)
        
        # Buttons
        buttons = ActionRow()
        invite_url = f"https://discord.com/oauth2/authorize?client_id={bot.user.id}&permissions=8&integration_type=0&scope=bot+applications.commands"
        buttons.add_item(Button(style=ButtonStyle.secondary, label="Add Bot", url=invite_url))
        buttons.add_item(Button(style=ButtonStyle.secondary, label="Support Server", url="https://discord.gg/support"))
        container.add_item(buttons)
        
        view.add_item(container)
        return view
    
    @staticmethod
    def vote_view(bot) -> LayoutView:
        """Create vote view"""
        view = LayoutView()
        container = Container()
        
        thumb = Thumbnail(bot.user.avatar.url)
        text = f"## {bot.user.name} - Vote Links\n"
        text += "Vote on top.gg & dbl for 12hr free no prefix.\n\n"
        text += f"-# Use the button below to vote {bot.user.name}"
        
        section = Section(TextDisplay(text), accessory=thumb)
        container.add_item(section)
        
        # Buttons
        buttons = ActionRow()
        buttons.add_item(Button(style=ButtonStyle.secondary, label="Vote On Top.gg", url="https://top.gg/"))
        buttons.add_item(Button(style=ButtonStyle.secondary, label="Vote On DBL", url="https://top.gg/"))
        container.add_item(buttons)
        
        view.add_item(container)
        return view
