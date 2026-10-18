import discord, json
#from core import Thunder, Cog
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay
#from Modules.blacklist import add_user_to_blacklist, remove_user_from_blacklist 
from discord.ext.commands import Cog

from motor.motor_asyncio import AsyncIOMotorClient
MONGO_URI = "mongodb+srv://fluxer8585:fluxer8585@fluxer.3izoeeq.mongodb.net/?appName=Fluxer"
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["ArgoBotV2"]


async def add_user_to_blacklist(bot_id, user_id: int) -> None:

    data = await db.blacklist.find_one({"blacklist": bot_id})
    if not data:
        return
    if user_id in data["user_id"]:
        return
    data["user_id"].append(user_id)
    await db.blacklist.update_one({"blacklist": bot_id}, {"$set": data}, upsert=True)
    

    

async def remove_user_from_blacklist(bot_id, user_id: int) -> None:
    data = await db.blacklist.find_one({"blacklist": bot_id})
    if not data:
        return
    if user_id not in data["user_id"]:
        return
    data["user_id"].remove(user_id)
    await db.blacklist.update_one({"blacklist": bot_id}, {"$set": data}, upsert=True)
    
    

class AutoBlacklist(Cog):
    def __init__(self, client):
      self.client = client
      self.spam_cd_mapping = commands.CooldownMapping.from_cooldown(5, 5, commands.BucketType.member)
      self.spam_command_mapping = commands.CooldownMapping.from_cooldown(6, 10, commands.BucketType.member)
      self.headers = {"Authorization": f"Bot {client.http.token}"}
   

   #   print("Cog Loaded: AutoBlacklist")

    @commands.Cog.listener()
    async def on_message(self, message):
      bucket = self.spam_cd_mapping.get_bucket(message)

      ch = self.client.get_channel(1367129093346295842) 
      unknown = f"<@{self.client.user.id}>"
      retry = bucket.update_rate_limit()

      if retry:
        if message.content == unknown or message.content == f"<@!{self.client.user.id}>":
          await add_user_to_blacklist(self.client.user.id, message.author.id)
          view = LayoutView()
          container = Container()
          container.add_item(TextDisplay(f"## {message.author.name} Added To Blacklisted For Spam Mentioning"))
          container.add_item(TextDisplay(f"**Guild:** {message.guild.name}\n**Guild ID:** {message.guild.id}"))
          view.add_item(container)
          await ch.send(view=view)
  # SHOWCASE   */

    @commands.Cog.listener()
    async def on_command(self, ctx):
      bucket = self.spam_command_mapping.get_bucket(ctx.message)
      ch = self.client.get_channel(1332675621305974804) 
      retry = bucket.update_rate_limit()
      if retry:
        await add_user_to_blacklist(self.client.user.id, ctx.author.id)
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## {ctx.author.name} Added To Blacklisted For Spamming Commands"))
        container.add_item(TextDisplay(f"**Guild:** {ctx.guild.name}\n**Guild ID:** {ctx.guild.id}"))
        view.add_item(container)
        await ch.send(view=view)
    


async def setup(client):
    await client.add_cog(AutoBlacklist(client))