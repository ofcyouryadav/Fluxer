from __future__ import annotations

import discord
from discord.ui import LayoutView, Container, TextDisplay, Separator, Thumbnail, Section
from typing import Any, List, Protocol, Tuple
from discord.ext.commands import Context, Paginator as CmdPaginator
from .paginator import Paginator as XPaginator
from Config import Config as cf

class PageSource(Protocol):
    def is_paginating(self) -> bool:
        ...

    async def get_page(self, page_number: int) -> Any:
        ...

    def get_max_pages(self) -> int:
        ...

class FieldPagePaginator(PageSource):
    def __init__(
        self,
        entries: list[tuple[Any, Any]],
        *,
        per_page: int = 5,
        inline: bool = False,
        **kwargs
    ) -> None:
        self.entries = entries
        self.per_page = per_page
        self.max_pages = ((len(self.entries) - 1) // per_page) + 1
        self.title = kwargs.get('title')
        self.description = kwargs.get('description')
        self.footer = kwargs.get('footer')
        self.inline = inline

    def is_paginating(self) -> bool:
        return len(self.entries) > self.per_page

    def get_max_pages(self) -> int:
        return self.max_pages

    async def get_page(self, page_number: int) -> List[Tuple[Any, Any]]:
        base = page_number * self.per_page
        return self.entries[base:base + self.per_page]

    async def format_page(self, menu: XPaginator, entries: List[Tuple[Any, Any]]) -> Container:
        container = Container()
        
        if self.title:
            container.add_item(TextDisplay(f"## {self.title}"))
            container.add_item(Separator())
        
        if self.description:
            container.add_item(TextDisplay(self.description))
            container.add_item(Separator())
        
        # Add field entries
        for key, value in entries:
            container.add_item(TextDisplay(f"**{key}**\n{value}"))
        
        if self.max_pages > 1:
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Page {menu.current_page + 1}/{self.max_pages} • Thanks For Choosing Fluxer"))

        return container

class TextPaginator(PageSource):
    def __init__(self, text: str, *, prefix: str = '```', suffix: str = '```', max_size: int = 2000):
        paginator = CmdPaginator(prefix=prefix, suffix=suffix, max_size=max_size - 200)
        for line in text.split('\n'):
            paginator.add_line(line)

        self.pages = paginator.pages
        self.per_page = 1
        self.max_pages = len(self.pages)

    def is_paginating(self) -> bool:
        return len(self.pages) > 1

    def get_max_pages(self) -> int:
        return self.max_pages

    async def get_page(self, page_number: int) -> str:
        return self.pages[page_number]

    async def format_page(self, menu: XPaginator, content: str) -> str:
        if self.max_pages > 1:
            return f'{content}\\Fluxer • Page {menu.current_page + 1}/{self.max_pages}'
        return content

class DescriptionLayoutPaginator(PageSource):
    def __init__(
        self,
        entries: list[Any],
        *,
        per_page: int = 5,
        **kwargs
    ) -> None:
        self.entries = entries
        self.per_page = per_page
        self.max_pages = ((len(self.entries) - 1) // per_page) + 1
        self.title = kwargs.get('title')
        self.thumbnail = kwargs.get('thumbnail')
        self.author = kwargs.get('author')
        self.author_icon = kwargs.get('author_icon')
        self.color = 0x2f3136

    def is_paginating(self) -> bool:
        return len(self.entries) > self.per_page

    def get_max_pages(self) -> int:
        return self.max_pages

    async def get_page(self, page_number: int) -> Container:
        base = page_number * self.per_page
        page_entries = self.entries[base:base + self.per_page]
        
        container = Container()
        
        # Add Header
        if self.title:
            container.add_item(TextDisplay(f"## {self.title}"))
            container.add_item(Separator())
            
        # Format content
        if isinstance(page_entries, list):
            content = '\n'.join(str(entry) for entry in page_entries)
        else:
            content = str(page_entries)
            
        # Add content with optional thumbnail
        if self.thumbnail:
            thumb = Thumbnail(self.thumbnail)
            section = Section(TextDisplay(content), accessory=thumb)
            container.add_item(section)
        else:
            container.add_item(TextDisplay(content))
            
        container.add_item(Separator())
            
        return container

class DescriptionEmbedPaginator(PageSource):
    def __init__(
        self,
        entries: list[Any],
        *,
        per_page: int = 10,
        **kwargs
    ) -> None:
        self.entries = entries
        self.per_page = per_page
        self.max_pages = ((len(self.entries) - 1) // per_page) + 1
        self.title = kwargs.get('title')
        self.description = kwargs.get('description')
        self.color = kwargs.get('color', 0x2f3136)
        self.footer = kwargs.get('footer')
        self.thumbnail = kwargs.get('thumbnail')
        self.author = kwargs.get('author')
        self.author_icon = kwargs.get('author_icon')

    def is_paginating(self) -> bool:
        return len(self.entries) > self.per_page

    def get_max_pages(self) -> int:
        return self.max_pages

    async def get_page(self, page_number: int) -> List[Any]:
        base = page_number * self.per_page
        return self.entries[base:base + self.per_page]

    async def format_page(self, menu: XPaginator, entries: List[Any]) -> Container:
        container = Container()
        
        # Add title/author
        if self.title:
            container.add_item(TextDisplay(f"## {self.title}"))
            container.add_item(Separator())
        
        # Join entries with newlines
        if isinstance(entries, list):
            content = '\n'.join(str(entry) for entry in entries)
        else:
            content = str(entries)
        
        # Add content with optional thumbnail
        if self.thumbnail:
            thumb = Thumbnail(self.thumbnail)
            section = Section(TextDisplay(content), accessory=thumb)
            container.add_item(section)
        else:
            container.add_item(TextDisplay(content))
        
        # Add footer/pagination
        if self.max_pages > 1:
            container.add_item(Separator())
            footer_text = f'Page {menu.current_page + 1}/{self.max_pages}'
            if self.footer:
                footer_text = f'{self.footer} • {footer_text}'
            container.add_item(TextDisplay(footer_text))

        return container