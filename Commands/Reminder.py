import discord
from discord.ext import commands, tasks
from discord import ui
from discord.ui import LayoutView, Container, TextDisplay, Separator
import json
import asyncio
import datetime
import re
from dateutil.relativedelta import relativedelta
from typing import Optional
from utils.Tools import blacklist_check, ignore_check
from pathlib import Path

color = 0x2f3136


class ShortTime:
    """Time parser for reminders"""
    compiled = re.compile(
        r"""
            (?:(?P<years>[0-9])(?:years?|y))?             # e.g. 2y
            (?:(?P<months>[0-9]{1,2})(?:months?|mo))?     # e.g. 2months
            (?:(?P<weeks>[0-9]{1,4})(?:weeks?|w))?        # e.g. 10w
            (?:(?P<days>[0-9]{1,5})(?:days?|d))?          # e.g. 14d
            (?:(?P<hours>[0-9]{1,5})(?:hours?|h))?        # e.g. 12h
            (?:(?P<minutes>[0-9]{1,5})(?:minutes?|m))?    # e.g. 10m
            (?:(?P<seconds>[0-9]{1,5})(?:seconds?|s))?    # e.g. 15s
        """,
        re.VERBOSE,
    )

    def __init__(self, argument: Optional[str], *, now=None):
        self.argument = argument
        match = self.compiled.fullmatch(str(argument).lower())
        if match is None or not match.group(0):
            raise commands.BadArgument(
                "Invalid time provided. Try something like: `5m`, `2h` or `60s`"
            )

        data = {k: int(v) for k, v in match.groupdict(default=0).items()}
        now = now or datetime.datetime.now(datetime.timezone.utc)
        self.dt: datetime.datetime = now + relativedelta(**data)

    def __str__(self) -> str:
        return str(self.argument)

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    async def convert(cls, ctx, argument):
        return cls(argument, now=ctx.message.created_at)


async def create_timer(id, name, exp, cre, auth, c):
    """Create a new reminder timer"""
    remind_file = Path("remind.json")
    
    if not remind_file.exists():
        remind_file.write_text("{}")
    
    with open("remind.json", "r") as f:
        datab = json.load(f)
    
    data = {
        'name': name,
        "id": id,
        "guild": c.guild.id,
        "created": cre,
        "expire": exp,
        "author": auth.id,
        "channel": c.id
    }
    datab[str(id)] = data
    
    with open("remind.json", "w") as f:
        json.dump(datab, f, indent=4)


async def delete_timer(id):
    """Delete a reminder timer"""
    remind_file = Path("remind.json")
    
    if not remind_file.exists():
        return "Land"
    
    with open("remind.json", "r") as f:
        data = json.load(f)
        if not data.get(str(id)):
            return "Land"
    
    data.pop(str(id))
    
    with open("remind.json", "w") as f:
        json.dump(data, f, indent=4)


class Reminder(commands.Cog):
    """Reminder system commands"""

    def __init__(self, bot):
        self.bot = bot
        self._ling = asyncio.Lock()
        self.color = color
        self.clear_reminders.start()

    async def cog_unload(self):
        self.clear_reminders.cancel()

    @tasks.loop(seconds=3)
    async def clear_reminders(self):
        """Check and dispatch reminders"""
        remind_file = Path("remind.json")
        
        if not remind_file.exists():
            remind_file.write_text("{}")
            return
        
        with open("remind.json", "r") as f:
            data = json.load(f)
        
        if data == {}:
            return
        
        async with self._ling:
            for id in list(data.keys()):
                inf = data.get(str(id))
                if discord.utils.utcnow().timestamp() >= inf["expire"]:
                    self.bot.dispatch("timer_end", **inf)
                    await delete_timer(id)
                    await asyncio.sleep(0)

    @clear_reminders.before_loop
    async def before_clear_reminders(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_group(
        name="remind",
        aliases=["reminder"],
        invoke_without_command=True
    )
    @blacklist_check()
    @ignore_check()
    async def remind_group(self, ctx):
        """Reminder commands"""
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## Reminder Commands"))
        container.add_item(Separator())
        
        prefix = ctx.prefix
        commands_text = (
            f"**{prefix}remind start <time> [message]**\n"
            f"Creates a reminder\n\n"
            f"**{prefix}remind delete <id>**\n"
            f"Deletes a reminder with message id\n\n"
            f"**{prefix}remind list**\n"
            f"Shows currently running reminders\n\n"
            f"**Time Examples:** `5m`, `2h`, `1d`, `3w`"
        )
        container.add_item(TextDisplay(commands_text))
        
        view.add_item(container)
        await ctx.send(view=view)

    @remind_group.command(name="start", aliases=["create", "set"])
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def remind_start(self, ctx, time: ShortTime, *, name: str = "..."):
        """Create a new reminder"""
        timestamp = time.dt.timestamp()
        await create_timer(
            ctx.message.id,
            name,
            timestamp,
            ctx.message.created_at.timestamp(),
            ctx.message.author,
            ctx.channel
        )
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## Reminder Created ⏰"))
        container.add_item(Separator())
        container.add_item(TextDisplay(
            f"**Alright {ctx.author.name},** I'll remind you <t:{int(timestamp)}:R>\n\n"
            f"**Message:** {name}\n"
            f"**ID:** {ctx.message.id}"
        ))
        
        view.add_item(container)
        await ctx.send(view=view, delete_after=10)

    @remind_group.command(name="delete", aliases=["remove", "close", "rmv"])
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def remind_delete(self, ctx, msg_id: str):
        """Delete a reminder"""
        snap = await delete_timer(msg_id)
        
        view = LayoutView()
        container = Container()
        
        if snap == "Land":
            container.add_item(TextDisplay("## Error"))
            container.add_item(Separator())
            container.add_item(TextDisplay("❌ Invalid reminder ID."))
        else:
            container.add_item(TextDisplay("## Reminder Deleted"))
            container.add_item(Separator())
            container.add_item(TextDisplay("✅ Successfully deleted reminder."))
        
        view.add_item(container)
        await ctx.send(view=view)

    @remind_group.command(name="list", aliases=["l", "lst"])
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def reminder_list(self, ctx):
        """List all reminders in this guild"""
        guild_id = ctx.guild.id
        remind_file = Path("remind.json")
        
        if not remind_file.exists():
            remind_file.write_text("{}")
        
        with open("remind.json", "r") as file:
            reminders = json.load(file)

        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## Reminder List 📋"))
        container.add_item(Separator())
        
        guild_reminders = []
        for reminder_id, reminder_data in reminders.items():
            if reminder_data["guild"] != guild_id:
                continue
            guild_reminders.append((reminder_id, reminder_data))
        
        if not guild_reminders:
            container.add_item(TextDisplay("No active reminders in this server."))
        else:
            reminders_text = ""
            for reminder_id, reminder_data in guild_reminders[:10]:  # Limit to 10
                name = reminder_data["name"]
                created = reminder_data["created"]
                author_id = reminder_data["author"]
                channel_id = reminder_data["channel"]
                
                guild = self.bot.get_guild(guild_id)
                author = guild.get_member(author_id) if guild else None
                channel = guild.get_channel(channel_id) if guild else None
                
                reminders_text += (
                    f"**ID:** `{reminder_id}`\n"
                    f"**Message:** {name}\n"
                    f"**Created:** <t:{int(created)}:R>\n"
                    f"**Author:** {author.name if author else 'Unknown'}\n"
                    f"**Channel:** {channel.name if channel else 'Unknown'}\n\n"
                )
            
            container.add_item(TextDisplay(reminders_text))
            
            if len(guild_reminders) > 10:
                container.add_item(Separator())
                container.add_item(TextDisplay(f"*...and {len(guild_reminders) - 10} more reminders*"))
        
        view.add_item(container)
        await ctx.send(view=view)

    @commands.Cog.listener()
    async def on_timer_end(self, name, id, channel, expire, created, guild, author):
        """Handle reminder expiration"""
        chf = self.bot.get_channel(channel)
        if not chf:
            return
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## ⏰ Reminder!"))
        container.add_item(Separator())
        container.add_item(TextDisplay(
            f"**Message:** {name}\n"
            f"**Set:** <t:{int(created)}:R>"
        ))
        
        view.add_item(container)
        
        try:
            await chf.send(content=f"<@{author}>", view=view)
        except:
            pass


async def setup(bot):
    await bot.add_cog(Reminder(bot))
