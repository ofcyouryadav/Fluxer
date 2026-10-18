"""Quick Component V2 conversion helpers for fast migration"""
import discord
from discord import ui
from discord.ui import LayoutView

def quick_success_layout(message: str, color: int = 0x2f3136) -> LayoutView:
    """Quick success message layout"""
    view = LayoutView()
    container = ui.Container()
    container.add_item(ui.TextDisplay(f"✅ {message}"))
    view.add_item(container)
    return view

def quick_error_layout(message: str, color: int = 0xff0000) -> LayoutView:
    """Quick error message layout"""
    view = LayoutView()
    container = ui.Container()
    container.add_item(ui.TextDisplay(f"❌ {message}"))
    view.add_item(container)
    return view

def quick_info_layout(title: str, description: str, color: int = 0x2f3136, thumbnail: str = None) -> LayoutView:
    """Quick info layout with optional thumbnail"""
    view = LayoutView()
    container = ui.Container()
    
    if title:
        container.add_item(ui.TextDisplay(f"## {title}"))
        container.add_item(ui.Separator())
    
    if thumbnail:
        thumb = ui.Thumbnail(thumbnail)
        section = ui.Section(ui.TextDisplay(description), accessory=thumb)
        container.add_item(section)
    else:
        container.add_item(ui.TextDisplay(description))
    
    view.add_item(container)
    return view
