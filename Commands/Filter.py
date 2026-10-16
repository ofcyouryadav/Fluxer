import discord
from discord.ext import commands
from Config import Config
from discord import app_commands
import wavelink
from discord.ext.commands import Context, Cog
from Functions.CheckFunctions import same_voice
from logging import basicConfig, INFO, info
from Views.EqualizerView import EqualizerView
import asyncio
from typing import Optional
from discord.ui import LayoutView, Container, TextDisplay, Separator

basicConfig(
    level=INFO,
    format=
    "\x1b[38;5;197m[\x1b[0m%(asctime)s\x1b[38;5;197m]\x1b[0m -> \x1b[38;5;197m%(message)s\x1b[0m",
    datefmt="%H:%M:%S",
)

# Predefined equalizer presets
PRESETS = {
    "flat": [{"band": i, "gain": 0.0} for i in range(15)],
    "bass": [{"band": i, "gain": 0.6 if i < 4 else 0.0} for i in range(15)],
    "rock": [
        {"band": i, "gain": gain} for i, gain in enumerate([
            0.3, 0.2, 0.0, -0.1, -0.2, -0.1, 0.2, 0.3, 0.4, 0.3, 0.2, 0.1, 0.0, -0.1, -0.2
        ])
    ],
    "classical": [
        {"band": i, "gain": gain} for i, gain in enumerate([
            0.4, 0.3, 0.2, 0.1, 0.0, -0.1, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 0.4, 0.3
        ])
    ]
}

async def filter_layout(text):
    view = LayoutView()
    container = Container()
    container.add_item(TextDisplay(f"### {text}"))
    view.add_item(container)
    return view

class Filter(Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 3.0, commands.BucketType.user)
        self.active_filters = {}  # Store active filters per guild

    async def cog_check(self, ctx):
        bucket = self.cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(bucket, retry_after, commands.BucketType.user) 
        return True

    async def apply_filter(self, ctx: Context, filter_name: str, filter_settings: dict):
        try:
            vc: wavelink.Player = ctx.voice_client
            if not vc.playing:
                return await ctx.send(view=await filter_layout("I am not playing anything."))

            # Store active filter
            guild_id = ctx.guild.id
            if guild_id not in self.active_filters:
                self.active_filters[guild_id] = []
            self.active_filters[guild_id].append(filter_name)

            filter: wavelink.Filters = vc.filters
            for key, value in filter_settings.items():
                getattr(filter, key).set(**value)

            await vc.set_filters(filter)
            await ctx.send(view=await filter_layout(f"Applied {filter_name} filter."))

        except Exception as e:
            info(f"Error applying {filter_name} filter: {e}")
            await ctx.send(view=await filter_layout(f"Error applying filter: {str(e)}"))

    @commands.hybrid_command(name="preset", description="Apply an equalizer preset")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @same_voice()
    async def preset(self, ctx: Context, preset_name: str):
        if preset_name.lower() not in PRESETS:
            presets_list = ", ".join(PRESETS.keys())
            return await ctx.send(view=await filter_layout(f"Available presets: {presets_list}"))

        try:
            vc: wavelink.Player = ctx.voice_client
            if not vc.playing:
                return await ctx.send(view=await filter_layout("I am not playing anything."))

            filter: wavelink.Filters = vc.filters
            filter.equalizer.set(bands=PRESETS[preset_name.lower()])
            await vc.set_filters(filter)
            await ctx.send(view=await filter_layout(f"Applied {preset_name} preset."))
        except Exception as e:
            info(f"Error applying preset: {e}")
            await ctx.send(view=await filter_layout(f"Error applying preset: {str(e)}"))

    @commands.hybrid_command(name="echo", description="Adds an echo effect to the current song")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @same_voice()
    async def echo(self, ctx: Context, delay: float = 0.8, decay: float = 0.5):
        settings = {
            "echo": {
                "delay": min(max(delay, 0.1), 2.0),  # Limit between 0.1 and 2.0 seconds
                "decay": min(max(decay, 0.1), 0.95)  # Limit between 0.1 and 0.95
            }
        }
        await self.apply_filter(ctx, "echo", settings)

    @commands.hybrid_command(name="reverb", description="Adds a reverb effect to the current song")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @same_voice()
    async def reverb(self, ctx: Context, room_size: float = 0.8, damping: float = 0.5):
        settings = {
            "reverb": {
                "room_size": min(max(room_size, 0.1), 1.0),
                "damping": min(max(damping, 0.1), 1.0)
            }
        }
        await self.apply_filter(ctx, "reverb", settings)

    # Enhanced version of existing filters
    @commands.hybrid_command(name="8d", description="Adds an enhanced 8D audio effect")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @same_voice()
    async def _8d(self, ctx: Context, rotation_hz: float = 0.2):
        settings = {
            "rotation": {"rotation_hz": min(max(rotation_hz, 0.1), 0.5)},
            "timescale": {"pitch": 1.05}  # Slight pitch adjustment for better effect
        }
        await self.apply_filter(ctx, "8d", settings)

    @commands.hybrid_command(name="bassboost", description="Enhanced bass boost with customizable gain")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @same_voice()
    async def bassboost(self, ctx: Context, intensity: str = "medium"):
        gains = {
            "low": 0.3,
            "medium": 0.5,
            "high": 0.7,
            "extreme": 1.0
        }
        gain = gains.get(intensity.lower(), 0.5)

        settings = {
            "equalizer": {
                "bands": [
                    {"band": 0, "gain": gain},
                    {"band": 1, "gain": gain * 0.9},
                    {"band": 2, "gain": gain * 0.8},
                    {"band": 3, "gain": gain * 0.6}
                ]
            }
        }
        await self.apply_filter(ctx, f"bassboost_{intensity}", settings)

    @commands.hybrid_command(name="activefilters", description="Shows currently active filters")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @same_voice()
    async def activefilters(self, ctx: Context):
        guild_id = ctx.guild.id
        if guild_id not in self.active_filters or not self.active_filters[guild_id]:
            return await ctx.send(view=await filter_layout("No active filters."))

        filters_list = ", ".join(self.active_filters[guild_id])
        await ctx.send(view=await filter_layout(f"Active filters: {filters_list}"))

    @commands.hybrid_command(name="clearfilters", description="Removes all active filters")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @same_voice()
    async def clearfilters(self, ctx: Context):
        try:
            vc: wavelink.Player = ctx.voice_client
            if not vc.playing:
                return await ctx.send(view=await filter_layout("I am not playing anything."))

            filter: wavelink.Filters = vc.filters
            filter.reset()
            await vc.set_filters(filter)

            # Clear active filters for this guild
            self.active_filters[ctx.guild.id] = []

            await ctx.send(view=await filter_layout("Removed all filters."))
        except Exception as e:
            info(f"Error clearing filters: {e}")
            await ctx.send(view=await filter_layout(f"Error clearing filters: {str(e)}"))

    @commands.hybrid_command(name="nightcore", with_app_command=True, description="Adds a nightcore filter to the current song.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def nightcore(self, ctx: Context):
        settings = {"timescale": {"speed": 1.2, "pitch": 1.1, "rate": 1.0}}
        await self.apply_filter(ctx, "nightcore", settings)

    @commands.hybrid_command(name="vaporwave", with_app_command=True, description= "Adds a vaporwave filter to the current song.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def vaporwave(self, ctx: Context):
        settings = {"timescale": {"speed": 0.75, "pitch": 1.25, "rate": 1.0}}
        await self.apply_filter(ctx, "vaporwave", settings)

    @commands.hybrid_command(name="tremolo", with_app_command=True, description="Adds a tremolo filter to the current song.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def tremolo(self, ctx: Context):
        settings = {"tremolo": {"frequency": 2.0, "depth": .8}}
        await self.apply_filter(ctx, "tremolo", settings)

    @commands.hybrid_command(name="karaoke", with_app_command=True, description="Adds a karaoke filter to the current song.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def karaoke(self, ctx: Context):
        settings = {"karaoke": {"level": 1.0, "mono_level": 1.0, "filter_band": 220.0, "filter_width": 100.0}}
        await self.apply_filter(ctx, "karaoke", settings)

    @commands.hybrid_command(name="vibrato", with_app_command=True, description= "Adds a vibrato filter to the current song.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def vibrato(self, ctx: Context):
        settings = {"vibrato": {"frequency": 2.0, "depth": .8}}
        await self.apply_filter(ctx, "vibrato", settings)

    @commands.hybrid_command(name="treble", with_app_command=True, description= "Adds a treble filter to the current song.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def treble(self, ctx: Context):
        settings = {"tremolo": {"frequency": 1.0, "depth": .8}}
        await self.apply_filter(ctx, "treble", settings)

    @commands.hybrid_command(name="lofi", with_app_command=True, description="Adds a lofi filter to the current song.")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    @same_voice()
    async def lofi(self, ctx: Context):
        settings = {"timescale": {"speed": 0.7500000238418579, "pitch": 0.800000011920929, "rate": 1}}
        await self.apply_filter(ctx, "lofi", settings)

    @commands.hybrid_command(name="equalizer", with_app_command=True, description="Apply The Customizable Equalizer To The Current Song.", aliases=["eq"])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.guild_only()
    @same_voice()
    async def equalizer(self, ctx: Context):
        try:
            vc: wavelink.Player = ctx.voice_client
            if not vc.playing:
                return await ctx.send(view=await filter_layout("I am not playing anything."))
            view = EqualizerView(ctx, vc)
            await ctx.send( view=view)
            await view.wait()
        except Exception as e:
            info(f"Error: {e}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Filter(bot))