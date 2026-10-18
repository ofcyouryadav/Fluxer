import discord
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
from io import BytesIO
import os
from typing import Optional
import math
import random
import aiohttp
from Functions.session_manager import session_manager, require_session
import logging

logger = logging.getLogger(__name__)

class NowPlayingCard:
    def __init__(self):
        self.WIDTH = 800
        self.HEIGHT = 120  # Reduced height to match Spotify's compact style
        self.BACKGROUND_COLOR = (18, 18, 18, 255)  # Spotify's exact dark background
        self.PROGRESS_COLOR = (29, 185, 84)  # Spotify's exact green
        self.GLOW_COLOR = (30, 215, 96)  # Lighter Spotify green
        self.TEXT_COLOR = (255, 255, 255)
        self.SECONDARY_COLOR = (179, 179, 179)  # Spotify's secondary text color
        self.CORNER_RADIUS = 8  # Spotify-style rounded corners

        try:
            system_fonts = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "C:\\Windows\\Fonts\\Arial.ttf"
            ]
            for font_path in system_fonts:
                if os.path.exists(font_path):
                    self.title_font = ImageFont.truetype(font_path, 20)  # Slightly smaller font
                    self.artist_font = ImageFont.truetype(font_path, 14)  # Adjusted for Spotify style
                    self.time_font = ImageFont.truetype(font_path, 12)
                    break
        except Exception as e:
            logger.error(f"Font loading error: {e}")
            self.title_font = ImageFont.load_default()
            self.artist_font = ImageFont.load_default()
            self.time_font = ImageFont.load_default()

    def create_background(self, size: tuple[int, int], radius: int) -> Image.Image:
        """Creates a Spotify-style background with subtle gradient"""
        base = Image.new('RGBA', size, self.BACKGROUND_COLOR)

        # Create gradient overlay
        gradient = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(gradient)

        # Add subtle gradient from top to bottom
        for y in range(size[1]):
            alpha = int(15 * (1 - y/size[1]))  # More subtle gradient
            draw.line([(0, y), (size[0], y)], fill=(255, 255, 255, alpha))

        # Apply rounded corners
        mask = Image.new('L', size, 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.rounded_rectangle((0, 0, size[0]-1, size[1]-1), radius, fill=255)

        # Combine background and gradient
        base.putalpha(mask)
        base = Image.alpha_composite(base, gradient)
        return base

    def create_progress_bar(self, position: float, duration: float) -> Image.Image:
        """Creates a Spotify-style progress bar"""
        width, height = 740, 3  # Increased width to 740 from 720 for better spacing
        progress = position / duration if duration > 0 else 0

        # Create base bar
        bar = Image.new('RGBA', (width, height), (255, 255, 255, 30))  # Spotify's inactive bar color
        draw = ImageDraw.Draw(bar)

        if progress > 0:
            progress_width = int(width * progress)
            # Draw progress
            draw.rectangle(((0, 0), (progress_width, height)), fill=self.PROGRESS_COLOR)

            # Add subtle glow to progress
            glow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow)
            glow_draw.rectangle(((0, 0), (progress_width, height)), fill=self.GLOW_COLOR + (100,))
            glow = glow.filter(ImageFilter.GaussianBlur(radius=1))
            bar = Image.alpha_composite(glow, bar)

        return bar

    def format_time(self, seconds: float) -> str:
        """Format time in Spotify style (M:SS or H:MM:SS if > 1 hour)"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        hours = minutes // 60
        minutes = minutes % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    @require_session
    async def generate(self, title: str, artist: str, thumbnail_url: str, 
                      position: float, duration: float, session: aiohttp.ClientSession = None) -> Optional[Image.Image]:
        """Generate the now playing card with async HTTP requests"""
        try:
            # Create base canvas with Spotify-style background
            base = Image.new('RGBA', (self.WIDTH, self.HEIGHT), (0, 0, 0, 0))
            background = self.create_background((self.WIDTH, self.HEIGHT), self.CORNER_RADIUS)
            base.paste(background, (0, 0), background)

            # Process thumbnail (album art)
            try:
                async with session.get(thumbnail_url) as response:
                    if response.status == 200:
                        thumbnail_data = await response.read()
                        thumbnail = Image.open(BytesIO(thumbnail_data))
                        thumbnail = thumbnail.convert('RGBA')
                        thumbnail = thumbnail.resize((90, 90))  # Spotify-sized album art

                        # Create rounded corners for thumbnail
                        mask = Image.new('L', (90, 90), 0)
                        mask_draw = ImageDraw.Draw(mask)
                        mask_draw.rounded_rectangle((0, 0, 89, 89), 4, fill=255)

                        # Create shadow
                        shadow = Image.new('RGBA', (90, 90), (0, 0, 0, 0))
                        shadow_draw = ImageDraw.Draw(shadow)
                        shadow_draw.rounded_rectangle((0, 0, 89, 89), 4, fill=(0, 0, 0, 100))
                        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=3))

                        # Apply mask and combine
                        output = Image.new('RGBA', (90, 90), (0, 0, 0, 0))
                        output.paste(shadow, (2, 2))  # Offset shadow
                        output.paste(thumbnail, (0, 0))
                        output.putalpha(mask)
                        thumbnail = output
                    else:
                        logger.error(f"Failed to fetch thumbnail: HTTP {response.status}")
                        raise Exception(f"HTTP {response.status}")

            except Exception as e:
                logger.error(f"Thumbnail error: {e}")
                thumbnail = Image.new('RGBA', (90, 90), (40, 40, 40))
                draw_thumb = ImageDraw.Draw(thumbnail)
                draw_thumb.text((45, 45), "♪", font=self.title_font, fill=(200, 200, 200))

            # Place thumbnail
            base.paste(thumbnail, (15, 15), thumbnail)

            draw = ImageDraw.Draw(base)

            # Title and artist text with adjusted spacing
            title = title[:40] + "..." if len(title) > 40 else title
            artist = artist[:30] + "..." if len(artist) > 30 else artist

            # Title and artist text
            draw.text((120, 25), title, font=self.title_font, fill=self.TEXT_COLOR)
            draw.text((120, 50), artist, font=self.artist_font, fill=self.SECONDARY_COLOR)

            # Progress bar and timestamps - Moved closer to text
          #  progress_bar = self.create_progress_bar(position, duration)
          #  base.paste(progress_bar, (60, 150), progress_bar)  # Moved closer to text and adjusted x position

            # Add timestamps in Spotify style
          #  current_time = self.format_time(position)
          #  total_time = self.format_time(duration)

            # Position timestamps directly below progress bar with tighter spacing
         #   draw.text((30, 80), current_time, font=self.time_font, fill=self.SECONDARY_COLOR)  # Reduced spacing to 5px
        #    draw.text((750, 80), total_time, font=self.time_font, fill=self.SECONDARY_COLOR)  # Adjusted x position to match new width

            return base

        except Exception as e:
            logger.error(f"Generation error: {e}")
            return None

    @staticmethod
    def truncate_string(text: str, length: int = 40) -> str:
        """Truncate a string to a specified length"""
        return text[:length - 3] + "..." if len(text) > length else text