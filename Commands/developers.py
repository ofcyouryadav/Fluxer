from typing import Optional
from discord.ext import commands
from contextlib import redirect_stdout
import asyncio, os, discord , psutil, sys
from Views.paginators import DescriptionEmbedPaginator
from Views.paginator import Paginator
from Config import Config as config
import json
from Views.CogsReloadView import CogsView
from discord.ui import LayoutView, Container, TextDisplay, Separator
from Database.utils import cache_manager
Cross = "<a:melodic_cross:1307006642633572482>"
Tick = "<a:melodic_check:1307006796497551370>"

class Owner(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.bot = client
        self.bot.name = "Fluxer"
        self.process = psutil.Process(os.getpid())

    @commands.group(aliases=['nop', 'np'], description="No prefix commands.", invoke_without_command=True)
    @commands.check_any(config.owner(), commands.is_owner(),config.bot_owner())
    async def noprefix(self, ctx):
        pass


    @noprefix.command(name="add", description="Adds user to no prefix.")
    @commands.check_any(config.owner(), commands.is_owner(),config.bot_owner())
    async def _add__(self, ctx, user: discord.User):
        data = await self.bot.db.noprefix.find_one({"noprefix": self.bot.user.id}) 
        if not data:
            await self.bot.db.noprefix.update_one({"noprefix": self.bot.user.id}, {"$push": {"user_id": user.id}}, upsert=True)
            
            # Invalidate cache for this user
            cache_key = f"noprefix:{user.id}"
            await cache_manager.delete('noprefix', cache_key)
            
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## No Prefix"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"✅ **{user.name}** Has Been Added To Global No Prefix List."))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
            view.add_item(container)
            
            await ctx.send(view=view)
            return



        if user.id not in data["user_id"]:
            await self.bot.db.noprefix.update_one({"noprefix": self.bot.user.id}, {"$push": {"user_id": user.id}}, upsert=True)
            
            # Invalidate cache for this user
            cache_key = f"noprefix:{user.id}"
            await cache_manager.delete('noprefix', cache_key)
            
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## No Prefix"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"✅ **{user.name}** Has Been Added To Global No Prefix List."))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
            view.add_item(container)
            
            await ctx.send(view=view)
        else:
          if user.id in data["user_id"]:

            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## No Prefix"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"⚠️ **{user.name}** Found In Global No Prefix List."))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
            view.add_item(container)
            
            await ctx.send(view=view)



    @noprefix.command(name="remove", description="Removes no prefix from a user.", aliases=['rmv'])
    @commands.check_any(config.owner(), commands.is_owner(),config.bot_owner())
    async def _remov_e_(self, ctx, user: discord.User):
        data = await self.bot.db.noprefix.find_one({"noprefix": self.bot.user.id})
        if not data:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## No Prefix"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"❌ **{user.name}** Not Found In Global No Prefix List."))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
            view.add_item(container)
            
            await ctx.send(view=view)
            return

        if user.id in data["user_id"]:
            await ctx.typing()
            await self.bot.db.noprefix.update_one({"noprefix": self.bot.user.id}, {"$pull": {"user_id": user.id}}, upsert=True)
            
            # Invalidate cache for this user
            cache_key = f"noprefix:{user.id}"
            await cache_manager.delete('noprefix', cache_key)
            
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## No Prefix"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"✅ **{user.name}** Has Been Removed From Global No Prefix List."))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
            view.add_item(container)
            
            await ctx.send(view=view)

        else:
          if user.id not in data["user_id"]:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## No Prefix"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"❌ **{user.name}** Not Found In Global No Prefix List."))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
            view.add_item(container)
            
            await ctx.send(view=view)



    @noprefix.command(name="debug", description="Debug no-prefix database")
    @commands.check_any(config.owner(), commands.is_owner(),config.bot_owner())
    async def _debu_g(self, ctx):
        """Show raw MongoDB data for debugging"""
        # Fetch the raw data
        data = await self.bot.db.noprefix.find_one({"noprefix": self.bot.user.id})
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay("## 🔍 No-Prefix Database Debug"))
        container.add_item(Separator())
        
        if not data:
            container.add_item(TextDisplay("❌ No document found in MongoDB!"))
        else:
            user_list = data.get("user_id", [])
            container.add_item(TextDisplay(f"**Bot ID:** {self.bot.user.id}"))
            container.add_item(TextDisplay(f"**User List:** {user_list}"))
            container.add_item(TextDisplay(f"**Count:** {len(user_list)}"))
            container.add_item(TextDisplay(f"**Your ID in list?** {ctx.author.id in user_list}"))
            container.add_item(Separator())
            
            # Test the prefix for this user
            from main import get_prefix
            prefix = await get_prefix(self.bot, ctx.message)
            container.add_item(TextDisplay(f"**Your Prefixes:** {prefix}"))
        
        view.add_item(container)
        await ctx.send(view=view)

    @noprefix.command(name="list", description="Shows all users in no prefix.")
    @commands.check_any(config.owner(), commands.is_owner(),config.bot_owner())
    async def _lis_t(self, ctx):
      data = await self.bot.db.noprefix.find_one({"noprefix": self.bot.user.id})
      if not data or len(data["user_id"]) == 0:
          view = LayoutView()
          container = Container()
          container.add_item(TextDisplay("## No Prefix Commands"))
          container.add_item(Separator())
          container.add_item(TextDisplay("No Users Found In Global No Prefix List."))
          container.add_item(Separator())
          container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
          view.add_item(container)
          
          await ctx.send(view=view)
          return


      start = 0

      entries = [
        f"`{i+1}.` [{mem}](https://discord.com/users/{mem.id}) | ID: `{mem.id}`" for i, mem in enumerate([
            await self.bot.fetch_user(int(mem)) for mem in data["user_id"]
        ])
      ]
      paginator = Paginator(source=DescriptionEmbedPaginator(
        entries=entries,
        title=f"No Prefix Users: {len(entries)}", 
        description=f"Total: `{(len(data))}`", author="Fluxer's", 
        per_page=10),ctx=ctx)
      await paginator.paginate()

    @noprefix.command(name="reset", description="Resets all users in no prefix.") 
    @commands.check_any(config.owner(), commands.is_owner(),config.bot_owner())
    async def _rese_t(self, ctx):
        data = await self.bot.db.noprefix.find_one({"noprefix": self.bot.user.id})

        if not data:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## No Prefix"))
            container.add_item(Separator())
            container.add_item(TextDisplay("No Users Found In Global No Prefix List."))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
            view.add_item(container)
            
            await ctx.send(view=view)
            return

        await self.bot.db.noprefix.update_one({"noprefix": self.bot.user.id}, {"$set": {"user_id": []}}, upsert=True)
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay("## No Prefix"))
        container.add_item(Separator())
        container.add_item(TextDisplay("✅ All Users In Global No Prefix List Has Been Removed."))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
        view.add_item(container)
        
        await ctx.send(view=view)


    @commands.command(name="addowner", description="Adds user to owner.", aliases=['addown', 'addowners', 'ao'])
    @commands.check_any(config.bot_owner(), commands.is_owner())
    async def _addowner(self, ctx, user: discord.User):
        data = await self.bot.db.owner.find_one({"owners": self.bot.user.id})
        if not data:
            await self.bot.db.owner.update_one({"owners": self.bot.user.id}, {"$push": {"user_id": user.id}}, upsert=True)
            
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## Owner Commands"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"✅ **{user.name}** Has Been Added To {self.bot.name}'s Owner List."))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
            view.add_item(container)
            
            await ctx.send(view=view)
            return

        if user.id not in data["user_id"]:
            await ctx.typing()
            await self.bot.db.owner.update_one({"owners": self.bot.user.id}, {"$push": {"user_id": user.id}}, upsert=True)
            
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## Owner Commands"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"✅ **{user.name}** Has Been Added To {self.bot.name}'s Owner List."))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
            view.add_item(container)
            
            await ctx.send(view=view)
        else:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## Owner Commands"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"⚠️ **{user.name}** Found In {self.bot.name}'s Owner List."))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
            view.add_item(container)
            
            await ctx.send(view=view)
            return





    @commands.command(name="removeowner", description="Removes owner from a user.", aliases=['removeown', 'removeowners', 'ro'])
    @commands.check_any(config.bot_owner(), commands.is_owner())
    async def _removeowner(self, ctx, user: discord.User):
        data = await self.bot.db.owner.find_one({"owners": self.bot.user.id})
        if not data:

            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## Owner Commands"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"❌ **{user.name}** Not Found In {self.bot.name}'s Owner List."))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
            view.add_item(container)
            
            await ctx.send(view=view)
            return

        if user.id in data["user_id"]:

            await ctx.typing()
            await self.bot.db.owner.update_one({
                "owners": self.bot.user.id}, {"$pull": {"user_id": user.id}}, upsert=True)
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## Owner Commands"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"✅ **{user.name}** Has Been Removed From Owner List."))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
            view.add_item(container)
            
            await ctx.send(view=view)
            return




        else:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## Owner Commands"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"❌ **{user.name}** Not Found In Owner List."))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
            view.add_item(container)
            
            await ctx.send(view=view)
            return




    @commands.command(name="listowner", description="Shows all users in owner.", aliases=['listown', 'listowners', 'lo']) 
    @commands.check_any(config.owner(), commands.is_owner())
    async def _listowner(self, ctx):
      data = await self.bot.db.owner.find_one({"owners": self.bot.user.id})
      if not data or len(data["user_id"]) == 0:
          view = LayoutView()
          container = Container()
          container.add_item(TextDisplay("## Owner"))
          container.add_item(Separator())
          container.add_item(TextDisplay("No Users Found In Owner List."))
          container.add_item(Separator())
          container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
          view.add_item(container)
          
          await ctx.send(view=view)
          return
      start = 0

      entries = [
        f"`{i+1}.` [{mem}](https://discord.com/users/{mem.id}) | ID: `{mem.id}`" for i, mem in enumerate([await self.bot.fetch_user(int(mem)) for mem in data["user_id"]])
      ]
      paginator = Paginator(source=DescriptionEmbedPaginator(
        entries=entries,
        title=f"Owner Users: {len(entries)}",
        description=f"Total: `{len(data)}`", author = "Argo's",
        per_page=10)
                            , ctx = ctx)
      await paginator.paginate()



    @commands.group(name="blacklist", description="Blacklist commands.",aliases=["bl"],invoke_without_command=True)
    @commands.check_any(config.owner(), commands.is_owner(),config.bot_owner())
    async def _blacklist(self, ctx):
      try:
          pass
     #   await ctx.send_help(ctx.command)

      except:
        return


    @_blacklist.command(name="add", description="Adds user to blacklist.")
    @commands.check_any(config.owner(), commands.is_owner(),config.bot_owner())
    async def _add_(self, ctx, user: discord.User):
      try:
        data = await self.bot.db.blacklist.find_one({"blacklist": self.bot.user.id})
        if not data:
            await self.bot.db.blacklist.update_one({"blacklist": self.bot.user.id}, {"$push": {"user_id": user.id}}, upsert=True)
            
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## Blacklist Commands"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"✅ **{user.name}** Has Been Added To {self.bot.name}'s Blacklist List."))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
            view.add_item(container)
            
            await ctx.send(view=view)
            return

        if user.id in data["user_id"]:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## Blacklist Command"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"⚠️ **{user.name}** Is Found On Blacklisted Users."))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
            view.add_item(container)
            
            await ctx.send(view=view)
            return 
        else:
          await ctx.typing()
          await self.bot.db.blacklist.update_one({"blacklist": self.bot.user.id}, {"$push": {"user_id": user.id}}, upsert=True)
          
          view = LayoutView()
          container = Container()
          container.add_item(TextDisplay("## Blacklist Command"))
          container.add_item(Separator())
          container.add_item(TextDisplay(f"✅ **{user.name}** has been added to the blacklist."))
          container.add_item(Separator())
          container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
          view.add_item(container)
          
          await ctx.send(view=view)
      except:
        return


    @_blacklist.command(name="remove", description="Removes user from blacklist") 
    @commands.check_any(config.owner(), commands.is_owner(),config.bot_owner())
    async def _remove_(self, ctx, user: discord.User):
      try:
        data = await self.bot.db.blacklist.find_one({"blacklist": self.bot.user.id})
        if not data:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## Blacklist Command"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"❌ **{user.name}** Not Found In Blacklisted Users."))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
            view.add_item(container)
            
            await ctx.send(view=view)
            return

        if user.id not in data["user_id"]:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## Blacklist Command"))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"❌ **{user.name}** is not in the blacklist."))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
            view.add_item(container)
            
            await ctx.send(view=view)
            return 
        else:
          await ctx.typing()
          await self.bot.db.blacklist.update_one({"blacklist": self.bot.user.id}, {"$pull": {"user_id": user.id}}, upsert=True)
          
          view = LayoutView()
          container = Container()
          container.add_item(TextDisplay("## Blacklist Command"))
          container.add_item(Separator())
          container.add_item(TextDisplay(f"✅ **{user.name}** has been removed from the blacklist."))
          container.add_item(Separator())
          container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
          view.add_item(container)
          
          await ctx.send(view=view)

      except:
        return
    @commands.command(name="restart", description="Restarts the bot.", aliases=["reboot"])
    @commands.check_any(config.bot_owner(), commands.is_owner())
    async def _restart(self, ctx):
        await ctx.message.add_reaction("✅")
        python = sys.executable
        os.execl(python, python, *sys.argv)



    @commands.command(name="reload")
    @commands.check_any(config.bot_owner(), commands.is_owner())
    async def _reload(self, ctx):
        try:
             view = CogsView(ctx.bot)     
             await ctx.send(view=view)


        except Exception as e:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"{Cross} | {e}"))
            view.add_item(container)
            await ctx.send(view=view)
    @_blacklist.command(name="list", description="Shows all users in blacklist.")
    @commands.check_any(config.owner(), commands.is_owner(),config.bot_owner())
    async def _list_(self, ctx):
      try:
        data = await self.bot.db.blacklist.find_one({"blacklist": self.bot.user.id})
        if not data or len(data["user_id"]) == 0:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## Blacklist Command"))
            container.add_item(Separator())
            container.add_item(TextDisplay("No Users Found In Blacklist."))
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Actioned by {ctx.author}"))
            view.add_item(container)
            
            await ctx.send(view=view)
            return

        else:
          start = 0

          entries = [
            f"`{i+1}` [{mem}](https://discord.com/users/{mem.id}) | ID: `{mem.id}`" for i, mem in enumerate([await self.bot.fetch_user(int(mem)) for mem in data["user_id"]])] #for start in enumerate(range(len(re)), start = 1)]
          paginator = Paginator(source=DescriptionEmbedPaginator(
            entries=entries,
            title=f"Blacklisted Users: {len(entries)}",
            description=f"Total: `{len(data['user_id'])}`", author = "Argo's",
            per_page=10),ctx=ctx)
          await paginator.paginate()

      except:
        return




async def setup(bot):
    await bot.add_cog(Owner(bot))