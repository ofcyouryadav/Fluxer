import asyncio
import discord
from discord.ext import commands, tasks
from discord.utils import get
import datetime
import random
import requests
import aiohttp
import re
from discord.ext.commands.errors import BadArgument
from discord.ext.commands import Cog
from discord.colour import Color
from discord import ui
import hashlib
from utils.Tools import *
from traceback import format_exception
import discord
from discord.ext import commands
import datetime
from discord import ButtonStyle
from discord.ui import Button, View, LayoutView, Container, TextDisplay, Separator
import psutil
import time
from datetime import datetime, timezone, timedelta
import sqlite3
from typing import *
import string
from motor.motor_asyncio import AsyncIOMotorClient
#from cogs.commands.moderation import do_removal

lawda = [
  '8', '3821', '23', '21', '313', '43', '29', '76', '11', '9',
  '44', '470', '318' , '26', '69'
]



class AvatarView(View):
  def __init__(self, user, member, author_id, banner_url):
    super().__init__()
    self.user = user
    self.member = member
    self.author_id = author_id
    self.banner_url = banner_url

    if self.user.avatar.is_animated():
      self.add_item(Button(label='GIF', url=self.user.avatar.with_format('gif').url, style=discord.ButtonStyle.link))
    self.add_item(Button(label='PNG', url=self.user.avatar.with_format('png').url, style=discord.ButtonStyle.link))
    self.add_item(Button(label='JPEG', url=self.user.avatar.with_format('jpg').url, style=discord.ButtonStyle.link))
    self.add_item(Button(label='WEBP', url=self.user.avatar.with_format('webp').url, style=discord.ButtonStyle.link))

  async def interaction_check(self, interaction: discord.Interaction) -> bool:
    if interaction.user.id != self.author_id:
      await interaction.response.send_message(
        "Uh oh! That message doesn't belong to you. You must run this command to interact with it.",
        ephemeral=True
      )
      return False
    return True

  @discord.ui.button(label='Server Avatar', style=discord.ButtonStyle.success, custom_id='server_avatar_button')
  async def server_avatar(self, interaction: discord.Interaction, button: Button):
    if not self.member.guild_avatar:
      await interaction.response.send_message(
        "This user doesn't have a different guild avatar.",
        ephemeral=True
      )
    else:
      embed = interaction.message.embeds[0]
      embed.set_image(url=self.member.guild_avatar.url)
      await interaction.response.edit_message(embed=embed)

  @discord.ui.button(label='User Banner', style=discord.ButtonStyle.success, custom_id='banner_button')
  async def banner(self, interaction: discord.Interaction, button: Button):
    if not self.banner_url:
      await interaction.response.send_message(
        "This user doesn't have a banner.",
        ephemeral=True
      )
    else:
      embed = interaction.message.embeds[0]
      embed.set_image(url=self.banner_url)
      await interaction.response.edit_message(embed=embed)





class General(commands.Cog):

  def __init__(self, bot, *args, **kwargs):
    self.bot = bot

    self.aiohttp = aiohttp.ClientSession()
    self._URL_REGEX = r'(?P<url><[^: >]+:\/[^ >]+>|(?:https?|steam):\/\/[^\s<]+[^<.,:;\"\'\]\s])'
    self.color = 0x000000




  @commands.command(name="membercount",
                           help="Get total member count of the server",
                           usage="membercount",
                           aliases=["mc"])
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 2, commands.BucketType.user)
  async def membercount(self, ctx: commands.Context):
        total_members = len(ctx.guild.members)
        total_humans = len([member for member in ctx.guild.members if not member.bot])
        total_bots = len([member for member in ctx.guild.members if member.bot])

        online = len([member for member in ctx.guild.members if member.status == discord.Status.online])
        offline = len([member for member in ctx.guild.members if member.status == discord.Status.offline])
        idle = len([member for member in ctx.guild.members if member.status == discord.Status.idle])
        dnd = len([member for member in ctx.guild.members if member.status == discord.Status.do_not_disturb])

        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## Member Statistics"))
        container.add_item(Separator())
        
        count_stats = f"**Total Members:** {total_members}\n**Total Humans:** {total_humans}\n**Total Bots:** {total_bots}"
        container.add_item(TextDisplay(count_stats))
        
        container.add_item(Separator())
        
        presence_stats = f"**Online:** {online}\n**DND:** {dnd}\n**Idle:** {idle}\n**Offline:** {offline}"
        container.add_item(TextDisplay(presence_stats))
        
        view.add_item(container)
        await ctx.send(view=view)

  @commands.command(name="poll", usage="Poll <message>")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def poll(self, ctx: commands.Context, *, message):
    author = ctx.author
    
    view = LayoutView()
    container = Container()
    
    container.add_item(TextDisplay(f"## Poll by {author.name}"))
    container.add_item(Separator())
    container.add_item(TextDisplay(message))
    
    view.add_item(container)
    msg = await ctx.send(view=view)
    await msg.add_reaction("<:cryptora_tick:1404521529693306890>")
    await msg.add_reaction("<:cryptora_cross:1404521609569501417>")

  
  @commands.command(name="hack",
    help="hack someone's discord account",
    usage="Hack <member>")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def hack(self, ctx: commands.Context, member: discord.Member):
    stringi = member.name
    min_length = 2
    max_length = 12
    length = random.randint(min_length, max_length)
    stringg = member.name
    remaining_length = length - len(stringg)
    all_chars = string.ascii_letters + string.digits + string.punctuation
    random_chars = random.choices(all_chars, k=remaining_length)

    password = stringg + ''.join(random_chars)
    
    lund = await ctx.send(f"Processing to Hack {member.name}...")
    await asyncio.sleep(2)
    random_pass = random.choice(lawda)
    
    random_pass2 = ''.join(random.choices(string.ascii_letters + string.digits, k=3))
    
    view = LayoutView()
    container = Container()
    
    container.add_item(TextDisplay(f"## Hacked {member.display_name}"))
    container.add_item(Separator())
    
    hack_info = (
        f"**User:** {member.name}\n"
        f"**E-Mail:** {''.join(letter for letter in stringi if letter.isalnum())}{random_pass}@gmail.com\n"
        f"**Password:** {member.name}@{random_pass2}"
    )
    container.add_item(TextDisplay(hack_info))
    container.add_item(Separator())
    container.add_item(TextDisplay(f"-# Hacked by {ctx.author}"))
    
    view.add_item(container)
    await ctx.send(view=view)
    await lund.delete()


  @commands.command(name="token", usage="Token <member>")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 2, commands.BucketType.user)
  async def token(self, ctx: commands.Context, user: discord.Member = None):
    list = [
      "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N",
      "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "_"
      'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
      'ñ', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '0',
      '1', '2', '3', '4', '5', '6', '7', '8', '9'
    ]
    token = random.choices(list, k=59)
    if user is None:
      user = ctx.author
    
    view = LayoutView()
    container = Container()
    
    container.add_item(TextDisplay("## Discord Token"))
    container.add_item(Separator())
    container.add_item(TextDisplay(f"**User:** {user.name}\n**Token:** `{''.join(token)}`"))
    
    view.add_item(container)
    await ctx.send(view=view)




  @commands.command(name="wizz", usage="Wizz")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def wizz(self, ctx: commands.Context):
    message6 = await ctx.send(
      f"`Wizzing {ctx.guild.name}, will take 22 seconds to complete`")
    message7 = await ctx.send(f"Changing all guild settings...")
    message5 = await ctx.send(f"Deleting **{len(ctx.guild.roles)}** Roles...")
    await asyncio.sleep(1)
    message4 = await ctx.send(
      f"Deleting **{len(ctx.guild.channels)}** Channels...")
    await asyncio.sleep(1)
    message3 = await ctx.send(f"Deleting Webhooks...")
    message2 = await ctx.send(f"Deleting emojis")
    await asyncio.sleep(1)
    message1 = await ctx.send(f"Installing Ban Wave..")
    await asyncio.sleep(1)
    await message6.delete()
    await message7.delete()
    await message5.delete()
    await message4.delete()
    await message3.delete()
    await message2.delete()
    await message1.delete()
    
    view = LayoutView()
    container = Container()
    
    container.add_item(TextDisplay(f"## {self.bot.user.name}"))
    container.add_item(Separator())
    container.add_item(TextDisplay(f"**Successfully Wizzed {ctx.guild.name}**"))
    container.add_item(Separator())
    container.add_item(TextDisplay(f"-# Wizzed by {ctx.author}"))
    
    view.add_item(container)
    await ctx.send(view=view)


  @commands.command(
    name="urban",
    description="Searches for specified phrase on urbandictionary",
    help="Get meaning of specified phrase",
    usage="Urban <phrase>")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def urban(self, ctx: commands.Context, *, phrase):
    async with self.aiohttp.get(
        "http://api.urbandictionary.com/v0/define?term={}".format(
          phrase)) as urb:
      urban = await urb.json()
      try:
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## Meaning of \"{phrase}\""))
        container.add_item(Separator())
        
        definition = urban['list'][0]['definition'].replace('[', '').replace(']', '')
        container.add_item(TextDisplay(f"**Definition:**\n{definition}"))
        container.add_item(Separator())
        
        example = urban['list'][0]['example'].replace('[', '').replace(']', '')
        container.add_item(TextDisplay(f"**Example:**\n{example}"))
        container.add_item(Separator())
        
        author = urban['list'][0]['author'].replace('[', '').replace(']', '')
        written_on = urban['list'][0]['written_on'].replace('[', '').replace(']', '')
        container.add_item(TextDisplay(f"**Author:** {author}\n**Written On:** {written_on}"))
        
        view.add_item(container)
        temp = await ctx.reply(view=view, mention_author=True)
        await asyncio.sleep(45)
        await temp.delete()
        await ctx.message.delete()
      except:
        pass

  @commands.command(name="rickroll",
                           help="Detects if provided url is a rick-roll",
                           usage="Rickroll <url>")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def rickroll(self, ctx: commands.Context, *, url: str):
    if not re.match(self._URL_REGEX, url):
      raise BadArgument("Invalid URL")

    phrases = [
      "rickroll", "rick roll", "rick astley", "never gonna give you up"
    ]
    source = str(await (await self.aiohttp.get(
      url, allow_redirects=True)).content.read()).lower()
    rickRoll = bool((re.findall('|'.join(phrases), source,
                                re.MULTILINE | re.IGNORECASE)))
    
    view = LayoutView()
    container = Container()
    
    container.add_item(TextDisplay("## Rick Roll Detection"))
    container.add_item(Separator())
    container.add_item(TextDisplay(
        f"Rick Roll **{'was found' if rickRoll else 'was not found'}** in webpage"
    ))
    
    view.add_item(container)
    await ctx.reply(view=view, mention_author=True)

  @commands.command(name="hash",
                           help="Hashes provided text with provided algorithm")
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def hash(self, ctx: commands.Context, algorithm: str, *, message):
    algos: dict[str, str] = {
      "md5": hashlib.md5(bytes(message.encode("utf-8"))).hexdigest(),
      "sha1": hashlib.sha1(bytes(message.encode("utf-8"))).hexdigest(),
      "sha224": hashlib.sha224(bytes(message.encode("utf-8"))).hexdigest(),
      "sha3_224": hashlib.sha3_224(bytes(message.encode("utf-8"))).hexdigest(),
      "sha256": hashlib.sha256(bytes(message.encode("utf-8"))).hexdigest(),
      "sha3_256": hashlib.sha3_256(bytes(message.encode("utf-8"))).hexdigest(),
      "sha384": hashlib.sha384(bytes(message.encode("utf-8"))).hexdigest(),
      "sha3_384": hashlib.sha3_384(bytes(message.encode("utf-8"))).hexdigest(),
      "sha512": hashlib.sha512(bytes(message.encode("utf-8"))).hexdigest(),
      "sha3_512": hashlib.sha3_512(bytes(message.encode("utf-8"))).hexdigest(),
      "blake2b": hashlib.blake2b(bytes(message.encode("utf-8"))).hexdigest(),
      "blake2s": hashlib.blake2s(bytes(message.encode("utf-8"))).hexdigest()
    }
    
    view = LayoutView()
    container = Container()
    
    container.add_item(TextDisplay(f"## Hashed \"{message}\""))
    container.add_item(Separator())
    
    if algorithm.lower() not in list(algos.keys()):
      hash_list = "\n".join([f"**{algo}:**\n```{algos[algo]}```" for algo in list(algos.keys())])
      container.add_item(TextDisplay(hash_list))
    else:
      container.add_item(TextDisplay(f"**{algorithm}:**\n```{algos[algorithm.lower()]}```"))
    
    view.add_item(container)
    await ctx.reply(view=view, mention_author=True)

  


  @commands.command(
    name="italicize",
    help="Italicize the given text"
  )
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def italicize(self, ctx: commands.Context, *, message: str):
    """Italicize text"""
    await ctx.send(f'*{message}*')

  @commands.command(
    name="strike",
    help="Strikethrough the given text"
  )
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def strike(self, ctx: commands.Context, *, message: str):
    """Strikethrough text"""
    await ctx.send(f'~~{message}~~')

  @commands.command(
    name="quote",
    help="Quote the given text"
  )
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def quote(self, ctx: commands.Context, *, message: str):
    """Quote text"""
    await ctx.send(f'> {message}')

  @commands.command(
    name="code",
    help="Format the given text as code"
  )
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def code(self, ctx: commands.Context, *, message: str):
    """Code format text"""
    await ctx.send(f'`{message}`')

  @commands.command(
    name="bold",
    help="Bold the given text"
  )
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def bold(self, ctx: commands.Context, *, message: str):
    """Bold text"""
    await ctx.send(f'**{message}**')

  @commands.command(
    name="censor",
    help="Censor/spoiler the given text"
  )
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def censor(self, ctx: commands.Context, *, message: str):
    """Censor text"""
    await ctx.send(f'||{message}||')

  @commands.command(
    name="underline",
    help="Underline the given text"
  )
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def underline(self, ctx: commands.Context, *, message: str):
    """Underline text"""
    await ctx.send(f'__{message}__')

  @commands.command(
    name="gender",
    help="Check someone's gender (joke command)"
  )
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def gender(self, ctx: commands.Context, member: discord.Member):
    """Check gender (joke)"""
    view = LayoutView()
    container = Container()
    
    container.add_item(TextDisplay("## Gender Check"))
    container.add_item(Separator())
    container.add_item(TextDisplay(f"{member.name}'s gender is **None** "))
    
    view.add_item(container)
    await ctx.send(view=view)

  @commands.command(
    name="pikachu",
    help="Get a random pikachu gif"
  )
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 5, commands.BucketType.user)
  async def pikachu(self, ctx: commands.Context):
    """Get random pikachu image"""
    try:
      response = requests.get('https://some-random-api.ml/img/pikachu')
      if response.status_code == 200:
        data = response.json()
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## Pikachu! ⚡"))
        container.add_item(Separator())
        
        gallery = ui.MediaGallery()
        gallery.add_item(media=data['link'])
        container.add_item(gallery)
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Requested by {ctx.author.name}"))
        
        view.add_item(container)
        await ctx.send(view=view)
      else:
        await ctx.send("Failed to fetch pikachu image.")
    except Exception as e:
      await ctx.send(f"Error: {str(e)}")

  @commands.command(
    name="ping",
    help="Get bot latency/response time",
    aliases=["latency"]
  )
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 2, commands.BucketType.user)
  async def ping(self, ctx: commands.Context):
    """Get bot ping/latency"""
    import time
    import os
    
    # Websocket/Gateway latency
    ws_latency = round(self.bot.latency * 1000)
    
    # API latency - measure response time
    api_start = time.perf_counter()
    await ctx.typing()
    api_latency = round((time.perf_counter() - api_start) * 1000)
    
    # MongoDB ping
    mongo_latency = "Failed"
    try:
      mongo_uri = os.getenv("MONGO_URI", "mongodb+srv://fluxer8585:fluxer8585@fluxer.3izoeeq.mongodb.net/?appName=Fluxer")
      mongo_client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
      mongo_start = time.perf_counter()
      await mongo_client.admin.command('ping')
      mongo_latency = round((time.perf_counter() - mongo_start) * 1000)
      await mongo_client.close()
    except:
      pass
    
    view = LayoutView()
    container = ui.Container()
    
    container.add_item(ui.TextDisplay("## Pong! "))
    container.add_item(ui.Separator())
    
    latency_text = (
      f"**Websocket/Gateway:** {ws_latency}ms\n"
      f"**API Response:** {api_latency}ms\n"
      f"**MongoDB:** {mongo_latency}ms" if isinstance(mongo_latency, int) else f"**Websocket/Gateway:** {ws_latency}ms\n**API Response:** {api_latency}ms\n**MongoDB:** {mongo_latency}"
    )
    container.add_item(ui.TextDisplay(latency_text))
    
    view.add_item(container)
    await ctx.send(view=view)

  @commands.command(
    name="bot",
    help="Get bot invite link",
    aliases=["invite"]
  )
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def bot(self, ctx: commands.Context):
    """Get bot invite link"""
    invite_url = discord.utils.oauth_url(
      self.bot.user.id,
      permissions=discord.Permissions(administrator=True)
    )
    
    view = LayoutView()
    container = ui.Container()
    
    container.add_item(ui.TextDisplay("## Add Me to Your Server"))
    container.add_item(ui.Separator())
    container.add_item(ui.TextDisplay(" Click the button below to add me!"))
    
    view.add_item(container)
    
    btn_view = discord.ui.View()
    btn_view.add_item(discord.ui.Button(label="Add Bot to Server", url=invite_url, style=discord.ButtonStyle.link))
    
    await ctx.send(view=view)
    await ctx.send(view=btn_view)

  @commands.command(
    name="support",
    help="Get support server info",
    aliases=["server"]
  )
  @blacklist_check()
  @ignore_check()
  @commands.cooldown(1, 3, commands.BucketType.user)
  async def support(self, ctx: commands.Context):
    """Get support server information"""
    import os
    
    support_link = os.getenv("SUPPORT_SERVER_INVITE", "https://discord.gg/rrunYaSf2q")
    
    view = LayoutView()
    container = ui.Container()
    
    container.add_item(ui.TextDisplay("## Support Server"))
    container.add_item(ui.Separator())
    container.add_item(ui.TextDisplay(" Need help? Join our support server!\n\n**Features:**\n• Bot support and troubleshooting\n• Feature requests\n• Community discussions\n• Updates and announcements"))
    
    view.add_item(container)
    
    btn_view = discord.ui.View()
    btn_view.add_item(discord.ui.Button(label="Join Support Server", url=support_link, style=discord.ButtonStyle.link))
    
    await ctx.send(view=view)
    await ctx.send(view=btn_view)


async def setup(bot):
    await bot.add_cog(General(bot))
