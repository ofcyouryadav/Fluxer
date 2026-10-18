import discord 
from discord.ext import commands
from discord.ext.commands import Context, CheckFailure
from discord.ui import LayoutView, Container, TextDisplay
from Config import Config
from datetime import datetime
from time import strptime
from typing import Optional, Union, Dict, Any, TypeVar, Callable
import os
import aiohttp
import logging

logger = logging.getLogger(__name__)

def create_check_message(text):
    """Helper function to create check message view"""
    view = LayoutView()
    container = Container()
    container.add_item(TextDisplay(f"## {text}"))
    view.add_item(container)
    return view

## CLASS OF FUNCTIONS
class NotVoter(commands.CheckFailure):
    pass

def DotEnv(query: str) -> Optional[str]:
    return os.getenv(query)

class NotConnectToVoice(CheckFailure):
    pass

class PlayerNotConnected(CheckFailure):
    pass

class MustBeSameVoice(CheckFailure): 
    pass

class NotDJ(CheckFailure):
    pass

## CHECKS
def check_voice() -> Callable:
    async def predicate(ctx: Context) -> bool:
        if ctx.author.voice is None:
            await ctx.send(view=create_check_message("You are not connected to a voice channel"))
            raise NotConnectToVoice()
        return True
    return commands.check(predicate)

def check_player() -> Callable:
    async def predicate(ctx: Context) -> bool:
        if ctx.me.voice is None:
            await ctx.send(view=create_check_message("No player has found on this server."), delete_after=30)
            raise PlayerNotConnected()
        return True
    return commands.check(predicate)

def same_voice() -> Callable:
    async def predicate(ctx: Context) -> bool:
        if ctx.me.voice is None:
            await ctx.send(view=create_check_message("No player has found on this server."), delete_after=30)
            raise PlayerNotConnected()
        if ctx.author.voice is None:
            await ctx.send(view=create_check_message("You are not connected to a voice channel"))
            raise NotConnectToVoice() 
        if ctx.me.voice.channel != ctx.author.voice.channel:
            await ctx.send(view=create_check_message("You are not connected to the same voice channel as me"), delete_after=30)
            raise MustBeSameVoice()
        return True
    return commands.check(predicate)

def time(millis: int) -> str:
    seconds = (millis/1000) % 60
    minutes = (millis/(1000*60)) % 60
    hours = (millis/(1000*60*60)) % 24
    if hours > 1:
        return "%02d:%02d:%02d" % (hours, minutes, seconds)
    else:
        return "%02d:%02d" % (minutes, seconds)

def FormatTime(number: str) -> Optional[int]:
    try:
        try:
            num = strptime(number, '%M:%S')
        except ValueError:
            try:
                num = strptime(number, '%S')
            except ValueError:
                num = strptime(number, '%H:%M:%S')
    except:
        return None

    return (int(num.tm_hour) * 3600 + int(num.tm_min) * 60 + int(num.tm_sec)) * 1000

voteDict = {
    "top_gg_api": "https://top.gg/api/bots/1069508321305960478/check", 
}

def is_voter() -> Callable:
    async def predicate(ctx: Context) -> bool:
        async with aiohttp.ClientSession() as cs:
            async with cs.get(
                voteDict["top_gg_api"], 
                params={"userId": ctx.author.id}, 
                headers={"Authorization": DotEnv("TOP_GG_TOKEN")}
            ) as res:
                try:
                    data = await res.json()
                    if res.status != 200:
                        return True

                    if data.get("voted", False):
                        return True

                    view = LayoutView()
                    container = Container()
                    container.add_item(TextDisplay("## You need to vote to use this command."))
                    container.add_item(TextDisplay("**Vote Link:** [Click Here](https://top.gg/bot/1131938711639183363/vote)"))
                    view.add_item(container)
                    await ctx.send(view=view, delete_after=30)
                    raise NotVoter()

                except Exception as e:
                    logger.error(f"Error checking voter status: {e}")
                    return True

    return commands.check(predicate)