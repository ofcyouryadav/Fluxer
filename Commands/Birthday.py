import discord
from discord.ext import commands, tasks
from discord.ui import LayoutView, Container, TextDisplay, Separator, Section, Thumbnail
from typing import Optional
from datetime import datetime, timezone, timedelta
import calendar

COLOR = 0x2f3136
SUCCESS_COLOR = 0x00ff88
ERROR_COLOR = 0xff0033
BIRTHDAY_COLOR = 0xff69b4

class Birthday(commands.Cog):
    """Advanced birthday management and celebration system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.color = COLOR
        self.birthdays_collection = bot.db["birthdays"]
        self.birthday_settings_collection = bot.db["birthday_settings"]
        self.check_birthdays_task.start()
    
    def cog_unload(self):
        self.check_birthdays_task.cancel()
    
    @tasks.loop(hours=1)
    async def check_birthdays_task(self):
        """Check and announce birthdays every hour"""
        await self.check_birthdays()
    
    @check_birthdays_task.before_loop
    async def before_check_birthdays(self):
        await self.bot.wait_until_ready()
    
    async def check_birthdays(self):
        """Check for birthdays today and announce them"""
        try:
            today = datetime.now()
            current_day = today.day
            current_month = today.month
            
            # Find all birthdays for today
            birthdays_today = await self.birthdays_collection.find({
                "day": current_day,
                "month": current_month
            }).to_list(None)
            
            for bday in birthdays_today:
                try:
                    guild = self.bot.get_guild(bday["guild_id"])
                    if not guild:
                        continue
                    
                    member = guild.get_member(bday["user_id"])
                    if not member:
                        continue
                    
                    # Check if already announced today
                    last_announced = bday.get("last_announced")
                    if last_announced and last_announced.date() == today.date():
                        continue
                    
                    # Get guild settings
                    settings = await self.birthday_settings_collection.find_one({"guild_id": guild.id})
                    
                    # Find announcement channel
                    channel = None
                    if settings and settings.get("channel_id"):
                        channel = guild.get_channel(settings["channel_id"])
                    
                    if not channel:
                        # Try to find a suitable channel
                        for ch_name in ["birthdays", "general", "announcements"]:
                            channel = discord.utils.get(guild.text_channels, name=ch_name)
                            if channel:
                                break
                    
                    if not channel:
                        channel = guild.text_channels[0] if guild.text_channels else None
                    
                    if not channel:
                        continue
                    
                    # Calculate age if year provided
                    age_text = ""
                    if bday.get("year"):
                        age = today.year - bday["year"]
                        age_text = f"Turning **{age}** years old today!"
                    
                    # Create birthday announcement
                    view = LayoutView()
                    container = Container()
                    
                    container.add_item(TextDisplay("##  Happy Birthday! "))
                    container.add_item(Separator())
                    
                    desc = f"Everyone wish {member.name} a happy birthday! \n\n"
                    if age_text:
                        desc += f"{age_text}\n\n"
                    desc += "Have an amazing day filled with joy! "
                    
                    thumb = Thumbnail(member.display_avatar.url)
                    section = Section(TextDisplay(desc), accessory=thumb)
                    container.add_item(section)
                    
                    container.add_item(Separator())
                    
                    # Add birthday role if configured
                    if settings and settings.get("role_id"):
                        role = guild.get_role(settings["role_id"])
                        if role:
                            try:
                                await member.add_roles(role, reason="Birthday role")
                                desc2 = f"-# Birthday role {role.name} added for 24 hours!"
                                container.add_item(TextDisplay(desc2))
                            except:
                                pass
                    
                    view.add_item(container)
                    
                    await channel.send(f" {member.name}", view=view)
                    
                    # Update last announced
                    await self.birthdays_collection.update_one(
                        {"_id": bday["_id"]},
                        {"$set": {"last_announced": datetime.now(timezone.utc)}}
                    )
                    
                except Exception as e:
                    print(f"Error announcing birthday: {e}")
                    
        except Exception as e:
            print(f"Error checking birthdays: {e}")
    
    @commands.hybrid_group(name="birthday", aliases=["bday"])
    async def birthday(self, ctx):
        """Birthday management commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
    
    @birthday.command(name="set", aliases=["add"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def birthday_set(self, ctx, *, date: str):
        """Set your birthday (Format: DD/MM/YYYY or DD/MM)
        
        Examples:
        /birthday set 15/03/2005
        /birthday set 15/03
        """
        try:
            # Parse date
            if "/" in date:
                parts = date.split("/")
                if len(parts) == 2:
                    day, month = int(parts[0]), int(parts[1])
                    year = None
                elif len(parts) == 3:
                    day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                else:
                    raise ValueError("Invalid format")
            else:
                raise ValueError("Invalid format")
            
            # Validate month
            if not (1 <= month <= 12):
                raise ValueError("Month must be between 1 and 12")
            
            # Validate day for the specific month
            max_day = calendar.monthrange(year if year else 2000, month)[1]
            if not (1 <= day <= max_day):
                raise ValueError(f"Day must be between 1 and {max_day} for month {month}")
            
            # Validate year
            current_year = datetime.now().year
            if year and (year < 1900 or year > current_year):
                raise ValueError(f"Year must be between 1900 and {current_year}")
            
            # Save to database
            await self.birthdays_collection.update_one(
                {"guild_id": ctx.guild.id, "user_id": ctx.author.id},
                {"$set": {
                    "day": day,
                    "month": month,
                    "year": year,
                    "username": str(ctx.author),
                    "updated_at": datetime.now(timezone.utc)
                }},
                upsert=True
            )
            
            # Create success view
            view = LayoutView()
            container = Container()
            
            container.add_item(TextDisplay("## 🎂 Birthday Set!"))
            container.add_item(Separator())
            
            date_str = f"{day:02d}/{month:02d}"
            if year:
                date_str += f"/{year}"
                age = datetime.now().year - year
                desc = f"**Birthday:** {date_str}\n**Current Age:** {age} years old\n\n Your birthday has been saved!"
            else:
                desc = f"**Birthday:** {date_str}\n\n Your birthday has been saved!"
            
            thumb = Thumbnail(ctx.author.display_avatar.url)
            section = Section(TextDisplay(desc), accessory=thumb)
            container.add_item(section)
            
            container.add_item(Separator())
            container.add_item(TextDisplay("-# We'll announce it on your special day! "))
            
            view.add_item(container)
            await ctx.reply(view=view)
            
        except ValueError as e:
            view = LayoutView()
            container = Container()
            error_msg = str(e) if str(e) != "Invalid format" else "Please use: DD/MM/YYYY or DD/MM\nExample: 15/03/2005 or 15/03"
            container.add_item(TextDisplay(f" **Invalid Date**\n\n{error_msg}"))
            view.add_item(container)
            await ctx.reply(view=view)
    
    @birthday.command(name="remove", aliases=["delete"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def birthday_remove(self, ctx):
        """Remove your birthday"""
        result = await self.birthdays_collection.delete_one({
            "guild_id": ctx.guild.id,
            "user_id": ctx.author.id
        })
        
        if result.deleted_count == 0:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(" You don't have a birthday set."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(" Your birthday has been removed."))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @birthday.command(name="list", aliases=["upcoming"])
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def birthday_list(self, ctx):
        """View upcoming birthdays in this server"""
        birthdays = await self.birthdays_collection.find({"guild_id": ctx.guild.id}).to_list(None)
        
        if not birthdays:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("##  No Birthdays\n\nNo one has set their birthday yet!"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        # Sort by upcoming
        today = datetime.now()
        current_month = today.month
        current_day = today.day
        
        def sort_key(b):
            month, day = b["month"], b["day"]
            if month < current_month or (month == current_month and day < current_day):
                return (month + 12) * 100 + day
            return month * 100 + day
        
        birthdays.sort(key=sort_key)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"##  Upcoming Birthdays - {ctx.guild.name}"))
        container.add_item(Separator())
        
        bday_list = []
        for i, bday in enumerate(birthdays[:20], 1):
            user = ctx.guild.get_member(bday["user_id"])
            if not user:
                continue
            
            date_str = f"{bday['day']:02d}/{bday['month']:02d}"
            year_info = ""
            if bday.get("year"):
                age = today.year - bday["year"]
                year_info = f" (Turning {age + 1})"
            
            if bday["month"] == current_month and bday["day"] == current_day:
                bday_list.append(f" `{i}.` **{user.name}** - **TODAY!** {date_str}{year_info}")
            else:
                bday_list.append(f"`{i}.` **{user.name}** - {date_str}{year_info}")
        
        if bday_list:
            container.add_item(TextDisplay("\n".join(bday_list)))
        else:
            container.add_item(TextDisplay("No upcoming birthdays found."))
        
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Total: {len(birthdays)} birthdays set"))
        
        view.add_item(container)
        await ctx.reply(view=view)
    
    @birthday.command(name="setchannel")
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def birthday_setchannel(self, ctx, channel: discord.TextChannel):
        """Set the birthday announcement channel (Admin only)"""
        await self.birthday_settings_collection.update_one(
            {"guild_id": ctx.guild.id},
            {"$set": {"channel_id": channel.id}},
            upsert=True
        )
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f" Birthday announcements will be sent to {channel.name}"))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @birthday.command(name="setrole")
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def birthday_setrole(self, ctx, role: discord.Role):
        """Set the birthday role (Admin only)
        
        This role will be given to members on their birthday for 24 hours.
        """
        await self.birthday_settings_collection.update_one(
            {"guild_id": ctx.guild.id},
            {"$set": {"role_id": role.id}},
            upsert=True
        )
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f" {role.name} will be given to members on their birthday!"))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @birthday.command(name="test")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def birthday_test(self, ctx):
        """Test the birthday announcement system (Admin only)"""
        await self.check_birthdays()
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(" Birthday check completed! Check announcement channel."))
        view.add_item(container)
        await ctx.reply(view=view)


async def setup(bot):
    await bot.add_cog(Birthday(bot))
