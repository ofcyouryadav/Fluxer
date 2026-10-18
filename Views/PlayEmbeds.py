import discord
from discord import ui
from discord.ui import LayoutView
from Config import Config

## Now Playing Layouts using Component V2
# All embeds converted to LayoutView with containers

# LAYOUT 1 - Default/Compact Design
async def play_embed1(title, author, duration, requester, volume, queue_length, artwork):
    """Compact now playing layout with essential info"""
    view = LayoutView()
    container = ui.Container()
    
    container.add_item(ui.TextDisplay("## <a:Arziyaan_Music:1442615980365709624> Now Playing"))
    container.add_item(ui.Separator())
    
    # Track info with thumbnail
    track_info = f"**[{title}]({Config.support_server})**\n`{author}`\n\n"
    track_info += f" **Duration:** `{duration}`\n"
    track_info += f" **Volume:** `{volume}%`"
    
    thumb = ui.Thumbnail(artwork)
    section = ui.Section(ui.TextDisplay(track_info), accessory=thumb)
    container.add_item(section)
    
    container.add_item(ui.Separator())
    container.add_item(ui.TextDisplay(f"-# Requested by {requester} • Queue Position: {queue_length}"))
    
    view.add_item(container)
    return view

# LAYOUT 2 - Detailed Design
async def play_embed2(title, author, duration, requester, volume, queue_length, artwork):
    """Detailed now playing layout with full information"""
    view = LayoutView()
    container = ui.Container()
    
    container.add_item(ui.TextDisplay("## Now Playing"))
    container.add_item(ui.Separator())
    
    # Detailed track info
    track_info = f"<a:Arziyaan_Music:1442615980365709624> **Track:** [{title}]({Config.support_server})\n"
    track_info += f" **Artist:** {author}\n"
    track_info += f" **Duration:** {duration}\n"
    track_info += f" **Requested by:** {requester}\n"
    track_info += f" **Queue Position:** {queue_length}\n"
    track_info += f" **Volume:** {volume}%"
    
    thumb = ui.Thumbnail(artwork)
    section = ui.Section(ui.TextDisplay(track_info), accessory=thumb)
    container.add_item(section)
    
    container.add_item(ui.Separator())
    
    view.add_item(container)
    return view

# LAYOUT 3 - Minimalist
async def play_embed3(title, author, duration, requester, volume, queue_length, artwork):
    """Minimalist now playing layout"""
    view = LayoutView()
    container = ui.Container()
    
    container.add_item(ui.TextDisplay("## Now Playing"))
    container.add_item(ui.Separator())
    
    # Simple track display
    track_info = f"**[{title}]({Config.support_server})**\n\nRequester: {requester}"
    
    thumb = ui.Thumbnail(artwork)
    section = ui.Section(ui.TextDisplay(track_info), accessory=thumb)
    container.add_item(section)
    
    container.add_item(ui.Separator())
    container.add_item(ui.TextDisplay(f"-# Duration: {duration} | Queue: {queue_length} | Volume: {volume}%"))
    
    view.add_item(container)
    return view

# LAYOUT 4 - Dynamic with Queue Focus
async def play_embed4(title, author, duration, requester, volume, queue_length, artwork):
    """Dynamic layout with queue emphasis"""
    view = LayoutView()
    container = ui.Container()
    
    container.add_item(ui.TextDisplay(f"## Now Playing • Track {queue_length} in Queue"))
    container.add_item(ui.Separator())
    
    # Track details
    track_info = f"**[{title}]({Config.support_server})**\n\n"
    track_info += f"**Artist:** {author}\n"
    track_info += f"**Duration:** {duration}\n"
    track_info += f"**Volume:** {volume}%\n"
    track_info += f"**Requested by:** {requester}"
    
    thumb = ui.Thumbnail(artwork)
    section = ui.Section(ui.TextDisplay(track_info), accessory=thumb)
    container.add_item(section)
    
    container.add_item(ui.Separator())
    container.add_item(ui.TextDisplay("-# Use /queue to view the full playlist"))
    
    view.add_item(container)
    return view

# LAYOUT 5 - Aesthetic Focus with Media Gallery
async def play_embed5(title, author, duration, requester, volume, queue_length, artwork):
    """Aesthetic layout with large artwork display"""
    view = LayoutView()
    container = ui.Container()
    
    container.add_item(ui.TextDisplay("## Now Playing"))
    container.add_item(ui.Separator())
    
    # Track info
    track_info = f"### <a:Arziyaan_Music:1442615980365709624> [{title}]({Config.support_server})\n\n"
    track_info += f"> Artist: **{author}**\n"
    track_info += f"> Duration: **{duration}**\n"
    track_info += f"> Requested by: **{requester}**"
    
    container.add_item(ui.TextDisplay(track_info))
    
    # Large artwork in media gallery
    gallery = ui.MediaGallery()
    gallery.add_item(media=artwork)
    container.add_item(gallery)
    
    container.add_item(ui.Separator())
    container.add_item(ui.TextDisplay(f"-# Volume: {volume}% • Queue Position: {queue_length}"))
    
    view.add_item(container)
    return view
