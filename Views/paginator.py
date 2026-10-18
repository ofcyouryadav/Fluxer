from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Dict, Optional
import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord import Interaction, ButtonStyle
from discord.ui import LayoutView, Container, TextDisplay, Separator, ActionRow, Button

class Paginator(LayoutView):
    def __init__(
        self,
        source: Any,
        *,
        ctx: Context | Interaction,
        check_embeds: bool = True,
        timeout: float = 180.0
    ):
        super().__init__(timeout=timeout)
        self.source = source
        self.check_embeds = check_embeds
        self.ctx = ctx
        self.message: Optional[discord.Message] = None
        self.current_page = 0

    def build_controls(self) -> ActionRow:
        """Build the control buttons in an ActionRow"""
        row = ActionRow()
        
        # Previous button
        prev_btn = Button(emoji="<:melodic_forwardl:1315388554657927280>", style=ButtonStyle.grey, custom_id="prev_page_btn")
        async def prev_callback(interaction: discord.Interaction):
            await self.show_checked_page(interaction, self.current_page - 1)
        prev_btn.callback = prev_callback
        prev_btn.disabled = self.current_page == 0
        
        # First page button
        first_btn = Button(emoji="<:melodic_home:1307006457241407599>", style=ButtonStyle.grey, custom_id="first_page_btn")
        async def first_callback(interaction: discord.Interaction):
            await self.show_page(interaction, 0)
        first_btn.callback = first_callback
        first_btn.disabled = self.current_page == 0
        
        # Stop button
        stop_btn = Button(emoji="<:melodic_delete:1307016346956988447>", style=ButtonStyle.grey, custom_id="stop_btn")
        async def stop_callback(interaction: discord.Interaction):
            await interaction.response.defer()
            await interaction.delete_original_response()
            self.stop()
        stop_btn.callback = stop_callback
        
        # Next button
        next_btn = Button(emoji="<:melodic_forwardr:1315390300591489055>", style=ButtonStyle.grey, custom_id="next_page_btn")
        async def next_callback(interaction: discord.Interaction):
            await self.show_checked_page(interaction, self.current_page + 1)
        next_btn.callback = next_callback
        
        max_pages = self.source.get_max_pages()
        if max_pages is not None and (self.current_page + 1) >= max_pages:
            next_btn.disabled = True
        
        # Add buttons to row
        if hasattr(self.source, 'is_paginating') and self.source.is_paginating():
            max_pages = self.source.get_max_pages()
            if max_pages is not None and max_pages >= 2:
                row.add_item(prev_btn)
            row.add_item(first_btn)
            row.add_item(stop_btn)
            row.add_item(next_btn)
        
        return row

    async def _get_kwargs_from_page(self, page: int) -> Dict[str, Any]:
        value = await discord.utils.maybe_coroutine(self.source.format_page, self, page)
        if isinstance(value, dict):
            return value
        elif isinstance(value, str):
            return {'content': value, 'embed': None}
        elif isinstance(value, discord.Embed):
            return {'embed': value, 'content': None}
        else:
            return {}

    async def show_page(self, interaction: discord.Interaction, page_number: int) -> None:
        page = await self.source.get_page(page_number)
        self.current_page = page_number
        kwargs = await self._get_kwargs_from_page(page)
        
        # Rebuild view with controls
        self.clear_items()
        
        # For embed-based paginators, we keep the embed in kwargs and add controls
        if 'embed' in kwargs and kwargs['embed'] is not None:
            # Keep using embed for backwards compatibility
            controls_row = self.build_controls()
            container = Container()
            container.add_item(controls_row)
            self.add_item(container)
            
            # Always edit with both embed and view
            if interaction.response.is_done():
                if self.message:
                    await self.message.edit(**kwargs, view=self)
            else:
                await interaction.response.edit_message(**kwargs, view=self)
        else:
            # For content-based paginators
            if kwargs:
                controls_row = self.build_controls()
                container = Container()
                if 'content' in kwargs and kwargs['content']:
                    container.add_item(TextDisplay(kwargs['content']))
                    container.add_item(Separator())
                container.add_item(controls_row)
                self.add_item(container)
                
                # Edit without embed
                if interaction.response.is_done():
                    if self.message:
                        await self.message.edit(view=self, embed=None)
                else:
                    await interaction.response.edit_message(view=self, embed=None)

    async def show_checked_page(self, interaction: discord.Interaction, page_number: int) -> None:
        max_pages = self.source.get_max_pages()
        try:
            if max_pages is None:
                await self.show_page(interaction, page_number)
            elif max_pages > page_number >= 0:
                await self.show_page(interaction, page_number)
        except IndexError:
            pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if isinstance(self.ctx, discord.Interaction):
            if interaction.user and interaction.user.id in (self.ctx.client.owner_id, self.ctx.user.id):
                return True
            await interaction.response.send_message(
                'This pagination menu cannot be controlled by you, sorry!',
                ephemeral=True
            )
            return False

        if interaction.user and interaction.user.id in (self.ctx.bot.owner_id, self.ctx.author.id):
            return True
        await interaction.response.send_message(
            'This pagination menu cannot be controlled by you, sorry!',
            ephemeral=True
        )
        return False

    async def on_timeout(self) -> None:
        if self.message:
            try:
                await self.message.delete()
            except:
                pass

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        if interaction.response.is_done():
            await interaction.followup.send('An unknown error occurred, sorry', ephemeral=True)
        else:
            await interaction.response.send_message('An unknown error occurred, sorry', ephemeral=True)

    async def paginate(self, *, content: Optional[str] = None, ephemeral: bool = False) -> None:
        if hasattr(self.source, '_prepare_once'):
            await self.source._prepare_once()

        page = await self.source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        if content:
            kwargs.setdefault('content', content)

        # Build initial view with controls
        self.clear_items()
        
        # For embed-based paginators
        if 'embed' in kwargs and kwargs['embed'] is not None:
            controls_row = self.build_controls()
            container = Container()
            container.add_item(controls_row)
            self.add_item(container)
            
            if isinstance(self.ctx, discord.Interaction):
                await self.ctx.response.send_message(**kwargs, view=self, ephemeral=ephemeral)
                self.message = await self.ctx.original_response()
                return
            
            self.message = await self.ctx.send(**kwargs, view=self)
        else:
            # For content-based paginators
            controls_row = self.build_controls()
            container = Container()
            if 'content' in kwargs and kwargs['content']:
                container.add_item(TextDisplay(kwargs['content']))
                container.add_item(Separator())
            container.add_item(controls_row)
            self.add_item(container)
            
            if isinstance(self.ctx, discord.Interaction):
                await self.ctx.response.send_message(view=self, ephemeral=ephemeral)
                self.message = await self.ctx.original_response()
                return
            
            self.message = await self.ctx.send(view=self)


class LayoutPaginator(LayoutView):
    """
    Paginator that works with Component V2 LayoutView.
    The source must return a Container object or a list of items to add to the view.
    """
    def __init__(
        self,
        source: Any,
        *,
        ctx: Context | Interaction,
        timeout: float = 180.0
    ):
        super().__init__(timeout=timeout)
        self.source = source
        self.ctx = ctx
        self.message: Optional[discord.Message] = None
        self.current_page = 0
        
        # Initialize buttons
        self.previous_page_button = Button(emoji="<:melodic_forwardl:1315388554657927280>", style=ButtonStyle.grey, custom_id="prev_page")
        self.previous_page_button.callback = self.previous_page_callback
        
        self.first_page_button = Button(emoji="<:melodic_home:1307006457241407599>", style=ButtonStyle.grey, custom_id="first_page")
        self.first_page_button.callback = self.first_page_callback
        
        self.stop_button = Button(emoji="<:melodic_delete:1307016346956988447>", style=ButtonStyle.grey, custom_id="stop_page")
        self.stop_button.callback = self.stop_callback
        
        self.next_page_button = Button(emoji="<:melodic_forwardr:1315390300591489055>", style=ButtonStyle.grey, custom_id="next_page")
        self.next_page_button.callback = self.next_page_callback

    async def paginate(self, ephemeral: bool = False) -> None:
        if hasattr(self.source, '_prepare_once'):
            await self.source._prepare_once()

        await self.update_view(0)

        if isinstance(self.ctx, discord.Interaction):
            if self.ctx.response.is_done():
                self.message = await self.ctx.followup.send(view=self, ephemeral=ephemeral)
            else:
                await self.ctx.response.send_message(view=self, ephemeral=ephemeral)
                self.message = await self.ctx.original_response()
        else:
            self.message = await self.ctx.send(view=self)

    async def update_view(self, page_number: int):
        self.current_page = page_number
        page_content = await self.source.get_page(page_number)
        
        # Clear existing items
        self.children.clear()
        
        # Add page content (Container)
        if isinstance(page_content, Container):
            # If the page content is already a container, we need to add controls to it
            # or add it as a separate container
            self.add_item(page_content)
        elif isinstance(page_content, list):
            for item in page_content:
                self.add_item(item)
        
        # Add navigation buttons if needed
        if self.source.is_paginating():
            max_pages = self.source.get_max_pages()
            
            # Update button states
            self.first_page_button.disabled = page_number == 0
            self.previous_page_button.disabled = page_number == 0
            
            if max_pages is not None:
                self.next_page_button.disabled = (page_number + 1) >= max_pages
            
            # Create a controls container
            controls_container = Container()
            
            # Add buttons in a row
            row = ActionRow()
            if max_pages is not None and max_pages >= 2:
                row.add_item(self.previous_page_button)
            
            row.add_item(self.first_page_button)
            row.add_item(self.stop_button)
            row.add_item(self.next_page_button)
            
            controls_container.add_item(row)
            
            # Add footer with page info
            if max_pages:
                controls_container.add_item(Separator())
                footer = TextDisplay(f"-# Page {page_number + 1}/{max_pages}")
                controls_container.add_item(footer)
            
            self.add_item(controls_container)

    async def show_page(self, interaction: discord.Interaction, page_number: int):
        if interaction.user != (self.ctx.author if isinstance(self.ctx, Context) else self.ctx.user):
            return await interaction.response.send_message("You cannot control this pagination.", ephemeral=True)
            
        await self.update_view(page_number)
        
        # Properly edit the message
        if interaction.response.is_done():
            if self.message:
                await self.message.edit(view=self)
        else:
            await interaction.response.edit_message(view=self)

    async def previous_page_callback(self, interaction: discord.Interaction):
        await self.show_page(interaction, max(0, self.current_page - 1))

    async def first_page_callback(self, interaction: discord.Interaction):
        await self.show_page(interaction, 0)

    async def stop_callback(self, interaction: discord.Interaction):
        if interaction.user != (self.ctx.author if isinstance(self.ctx, Context) else self.ctx.user):
            return await interaction.response.send_message("You cannot control this pagination.", ephemeral=True)
        await interaction.message.delete()
        self.stop()

    async def next_page_callback(self, interaction: discord.Interaction):
        max_pages = self.source.get_max_pages()
        next_page = self.current_page + 1
        if max_pages is None or next_page < max_pages:
            await self.show_page(interaction, next_page)
