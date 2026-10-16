import discord
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay, Separator
import aiosqlite
from datetime import datetime, timedelta
from utils.Tools import *
import random

# Colors
SUCCESS_COLOR = 0x00ff88
ERROR_COLOR = 0xff0033
INFO_COLOR = 0x2f3136
WARNING_COLOR = 0xffaa00

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.initialize_db())

    async def initialize_db(self):
        self.db = await aiosqlite.connect('db/economy.db')
        
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                guild_id INTEGER,
                user_id INTEGER,
                wallet INTEGER DEFAULT 0,
                bank INTEGER DEFAULT 0,
                bank_limit INTEGER DEFAULT 5000,
                PRIMARY KEY (guild_id, user_id)
            )
        ''')
        
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS shop_items (
                guild_id INTEGER,
                item_name TEXT,
                item_price INTEGER,
                item_description TEXT,
                PRIMARY KEY (guild_id, item_name)
            )
        ''')
        
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS user_inventory (
                guild_id INTEGER,
                user_id INTEGER,
                item_name TEXT,
                quantity INTEGER DEFAULT 1,
                PRIMARY KEY (guild_id, user_id, item_name)
            )
        ''')
        
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS cooldowns (
                guild_id INTEGER,
                user_id INTEGER,
                command TEXT,
                last_used TIMESTAMP,
                PRIMARY KEY (guild_id, user_id, command)
            )
        ''')
        
        await self.db.commit()

    async def get_user(self, guild_id, user_id):
        async with self.db.execute(
            "SELECT wallet, bank, bank_limit FROM users WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        ) as cursor:
            result = await cursor.fetchone()
            if not result:
                await self.db.execute(
                    "INSERT INTO users (guild_id, user_id) VALUES (?, ?)",
                    (guild_id, user_id)
                )
                await self.db.commit()
                return (0, 0, 5000)
            return result

    async def update_wallet(self, guild_id, user_id, amount):
        await self.db.execute(
            "UPDATE users SET wallet = wallet + ? WHERE guild_id = ? AND user_id = ?",
            (amount, guild_id, user_id)
        )
        await self.db.commit()

    async def update_bank(self, guild_id, user_id, amount):
        await self.db.execute(
            "UPDATE users SET bank = bank + ? WHERE guild_id = ? AND user_id = ?",
            (amount, guild_id, user_id)
        )
        await self.db.commit()

    async def check_cooldown(self, guild_id, user_id, command, cooldown_seconds):
        async with self.db.execute(
            "SELECT last_used FROM cooldowns WHERE guild_id = ? AND user_id = ? AND command = ?",
            (guild_id, user_id, command)
        ) as cursor:
            result = await cursor.fetchone()
            if result:
                last_used = datetime.fromisoformat(result[0])
                time_passed = (datetime.now() - last_used).total_seconds()
                if time_passed < cooldown_seconds:
                    return False, cooldown_seconds - time_passed
        
        await self.db.execute(
            "INSERT OR REPLACE INTO cooldowns (guild_id, user_id, command, last_used) VALUES (?, ?, ?, ?)",
            (guild_id, user_id, command, datetime.now())
        )
        await self.db.commit()
        return True, 0

    def create_response(self, title: str, description: str = "", color: int = INFO_COLOR):
        """Helper to create Component V2 responses"""
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay(f"## {title}"))
        if description:
            container.add_item(Separator())
            container.add_item(TextDisplay(description))
        view.add_item(container)
        return view

    @commands.group(name="economy", invoke_without_command=True, aliases=['eco', 'econ'])
    @blacklist_check()
    @ignore_check()
    async def economy(self, ctx: commands.Context):
        """Economy system"""
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)

    @economy.command(name="balance", aliases=['bal', 'money'])
    @blacklist_check()
    @ignore_check()
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
        """Check your or someone's balance"""
        member = member or ctx.author
        wallet, bank, bank_limit = await self.get_user(ctx.guild.id, member.id)
        
        total = wallet + bank
        view = self.create_response(
            f"💰 {member.display_name}'s Balance",
            f"💵 **Wallet:** {wallet:,} coins\n"
            f"🏦 **Bank:** {bank:,}/{bank_limit:,} coins\n"
            f"💎 **Net Worth:** {total:,} coins",
            INFO_COLOR
        )
        await ctx.send(view=view)

    @economy.command(name="daily")
    @blacklist_check()
    @ignore_check()
    async def daily(self, ctx: commands.Context):
        """Claim your daily reward"""
        can_claim, remaining = await self.check_cooldown(ctx.guild.id, ctx.author.id, "daily", 86400)
        
        if not can_claim:
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            view = self.create_response(
                "⏳ Cooldown Active",
                f"You already claimed your daily reward! Come back in **{hours}h {minutes}m**",
                WARNING_COLOR
            )
            return await ctx.send(view=view)
        
        reward = random.randint(100, 500)
        await self.update_wallet(ctx.guild.id, ctx.author.id, reward)
        
        view = self.create_response(
            "✅ Daily Reward Claimed",
            f"You received **{reward:,}** coins!",
            SUCCESS_COLOR
        )
        await ctx.send(view=view)

    @economy.command(name="hourly")
    @blacklist_check()
    @ignore_check()
    async def hourly(self, ctx: commands.Context):
        """Claim your hourly reward"""
        can_claim, remaining = await self.check_cooldown(ctx.guild.id, ctx.author.id, "hourly", 3600)
        
        if not can_claim:
            minutes = int(remaining // 60)
            view = self.create_response(
                "⏳ Cooldown Active",
                f"You already claimed your hourly reward! Come back in **{minutes}m**",
                WARNING_COLOR
            )
            return await ctx.send(view=view)
        
        reward = random.randint(50, 150)
        await self.update_wallet(ctx.guild.id, ctx.author.id, reward)
        
        view = self.create_response(
            "✅ Hourly Reward Claimed",
            f"You received **{reward:,}** coins!",
            SUCCESS_COLOR
        )
        await ctx.send(view=view)

    @economy.command(name="weekly")
    @blacklist_check()
    @ignore_check()
    async def weekly(self, ctx: commands.Context):
        """Claim your weekly reward"""
        can_claim, remaining = await self.check_cooldown(ctx.guild.id, ctx.author.id, "weekly", 604800)
        
        if not can_claim:
            days = int(remaining // 86400)
            hours = int((remaining % 86400) // 3600)
            view = self.create_response(
                "⏳ Cooldown Active",
                f"You already claimed your weekly reward! Come back in **{days}d {hours}h**",
                WARNING_COLOR
            )
            return await ctx.send(view=view)
        
        reward = random.randint(1000, 3000)
        await self.update_wallet(ctx.guild.id, ctx.author.id, reward)
        
        view = self.create_response(
            "✅ Weekly Reward Claimed",
            f"You received **{reward:,}** coins!",
            SUCCESS_COLOR
        )
        await ctx.send(view=view)

    @economy.command(name="work")
    @blacklist_check()
    @ignore_check()
    async def work(self, ctx: commands.Context):
        """Work to earn money"""
        can_work, remaining = await self.check_cooldown(ctx.guild.id, ctx.author.id, "work", 1800)
        
        if not can_work:
            minutes = int(remaining // 60)
            view = self.create_response(
                "😴 You're Tired",
                f"Rest for **{minutes}m** before working again",
                WARNING_COLOR
            )
            return await ctx.send(view=view)
        
        jobs = ["programmer", "designer", "chef", "teacher", "doctor", "engineer", "artist", "musician"]
        job = random.choice(jobs)
        reward = random.randint(100, 300)
        await self.update_wallet(ctx.guild.id, ctx.author.id, reward)
        
        view = self.create_response(
            "💼 Work Completed",
            f"You worked as a **{job}** and earned **{reward:,}** coins!",
            SUCCESS_COLOR
        )
        await ctx.send(view=view)

    @economy.command(name="beg")
    @blacklist_check()
    @ignore_check()
    async def beg(self, ctx: commands.Context):
        """Beg for money"""
        can_beg, remaining = await self.check_cooldown(ctx.guild.id, ctx.author.id, "beg", 60)
        
        if not can_beg:
            seconds = int(remaining)
            view = self.create_response(
                "⏳ Cooldown Active",
                f"Wait **{seconds}s** before begging again",
                WARNING_COLOR
            )
            return await ctx.send(view=view)
        
        if random.random() < 0.3:
            view = self.create_response(
                "😢 No Luck",
                "No one gave you anything. Better luck next time!",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        reward = random.randint(10, 50)
        await self.update_wallet(ctx.guild.id, ctx.author.id, reward)
        
        messages = [
            f"A kind stranger gave you **{reward:,}** coins!",
            f"Someone felt generous and donated **{reward:,}** coins!",
            f"You found **{reward:,}** coins on the ground!"
        ]
        
        view = self.create_response(
            "🙏 Begging Success",
            random.choice(messages),
            SUCCESS_COLOR
        )
        await ctx.send(view=view)

    @economy.command(name="crime")
    @blacklist_check()
    @ignore_check()
    async def crime(self, ctx: commands.Context):
        """Commit a crime (risky but rewarding)"""
        can_crime, remaining = await self.check_cooldown(ctx.guild.id, ctx.author.id, "crime", 7200)
        
        if not can_crime:
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            view = self.create_response(
                "⏳ Cooldown Active",
                f"Wait **{hours}h {minutes}m** before committing another crime",
                WARNING_COLOR
            )
            return await ctx.send(view=view)
        
        crimes = ["robbed a bank", "stole a car", "hacked a company", "smuggled goods", "pickpocketed someone"]
        crime_type = random.choice(crimes)
        
        if random.random() < 0.4:
            fine = random.randint(200, 500)
            await self.update_wallet(ctx.guild.id, ctx.author.id, -fine)
            view = self.create_response(
                "🚔 Crime Failed",
                f"You got caught trying to {crime_type} and paid a fine of **{fine:,}** coins!",
                ERROR_COLOR
            )
        else:
            reward = random.randint(300, 800)
            await self.update_wallet(ctx.guild.id, ctx.author.id, reward)
            view = self.create_response(
                "💰 Crime Successful",
                f"You successfully {crime_type} and earned **{reward:,}** coins!",
                SUCCESS_COLOR
            )
        
        await ctx.send(view=view)

    @economy.command(name="deposit", aliases=['dep'])
    @blacklist_check()
    @ignore_check()
    async def deposit(self, ctx: commands.Context, amount: str):
        """Deposit money to your bank"""
        wallet, bank, bank_limit = await self.get_user(ctx.guild.id, ctx.author.id)
        
        if amount.lower() == "all":
            amount = wallet
        else:
            try:
                amount = int(amount)
            except:
                view = self.create_response(
                    "❌ Invalid Amount",
                    "Please enter a valid number",
                    ERROR_COLOR
                )
                return await ctx.send(view=view)
        
        if amount <= 0:
            view = self.create_response(
                "❌ Invalid Amount",
                "Amount must be positive",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        if amount > wallet:
            view = self.create_response(
                "❌ Insufficient Funds",
                f"You only have **{wallet:,}** coins in your wallet",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        if bank + amount > bank_limit:
            view = self.create_response(
                "❌ Bank Limit Exceeded",
                f"Your bank can only hold **{bank_limit:,}** coins. Deposit less or upgrade your bank",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        await self.update_wallet(ctx.guild.id, ctx.author.id, -amount)
        await self.update_bank(ctx.guild.id, ctx.author.id, amount)
        
        view = self.create_response(
            "✅ Deposit Successful",
            f"Deposited **{amount:,}** coins to your bank",
            SUCCESS_COLOR
        )
        await ctx.send(view=view)

    @economy.command(name="withdraw", aliases=['with'])
    @blacklist_check()
    @ignore_check()
    async def withdraw(self, ctx: commands.Context, amount: str):
        """Withdraw money from your bank"""
        wallet, bank, bank_limit = await self.get_user(ctx.guild.id, ctx.author.id)
        
        if amount.lower() == "all":
            amount = bank
        else:
            try:
                amount = int(amount)
            except:
                view = self.create_response(
                    "❌ Invalid Amount",
                    "Please enter a valid number",
                    ERROR_COLOR
                )
                return await ctx.send(view=view)
        
        if amount <= 0:
            view = self.create_response(
                "❌ Invalid Amount",
                "Amount must be positive",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        if amount > bank:
            view = self.create_response(
                "❌ Insufficient Funds",
                f"You only have **{bank:,}** coins in your bank",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        await self.update_bank(ctx.guild.id, ctx.author.id, -amount)
        await self.update_wallet(ctx.guild.id, ctx.author.id, amount)
        
        view = self.create_response(
            "✅ Withdrawal Successful",
            f"Withdrew **{amount:,}** coins from your bank",
            SUCCESS_COLOR
        )
        await ctx.send(view=view)

    @economy.command(name="pay", aliases=['give', 'transfer'])
    @blacklist_check()
    @ignore_check()
    async def pay(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Pay another user"""
        if member == ctx.author:
            view = self.create_response(
                "❌ Cannot Pay Yourself",
                "You cannot pay yourself",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        if member.bot:
            view = self.create_response(
                "❌ Cannot Pay Bots",
                "You cannot pay bots",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        wallet, bank, bank_limit = await self.get_user(ctx.guild.id, ctx.author.id)
        
        if amount <= 0:
            view = self.create_response(
                "❌ Invalid Amount",
                "Amount must be positive",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        if amount > wallet:
            view = self.create_response(
                "❌ Insufficient Funds",
                f"You only have **{wallet:,}** coins in your wallet",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        await self.update_wallet(ctx.guild.id, ctx.author.id, -amount)
        await self.update_wallet(ctx.guild.id, member.id, amount)
        
        view = self.create_response(
            "✅ Payment Sent",
            f"You gave **{amount:,}** coins to {member.name}",
            SUCCESS_COLOR
        )
        await ctx.send(view=view)

    @economy.command(name="rob", aliases=['steal'])
    @blacklist_check()
    @ignore_check()
    async def rob(self, ctx: commands.Context, member: discord.Member):
        """Rob another user"""
        if member == ctx.author:
            view = self.create_response(
                "❌ Cannot Rob Yourself",
                "You cannot rob yourself",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        if member.bot:
            view = self.create_response(
                "❌ Cannot Rob Bots",
                "You cannot rob bots",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        can_rob, remaining = await self.check_cooldown(ctx.guild.id, ctx.author.id, "rob", 14400)
        
        if not can_rob:
            hours = int(remaining // 3600)
            view = self.create_response(
                "⏳ Cooldown Active",
                f"Wait **{hours}h** before robbing again",
                WARNING_COLOR
            )
            return await ctx.send(view=view)
        
        target_wallet, _, _ = await self.get_user(ctx.guild.id, member.id)
        
        if target_wallet < 100:
            view = self.create_response(
                "❌ Target Too Poor",
                f"{member.name} doesn't have enough money to rob",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        if random.random() < 0.5:
            fine = random.randint(100, 300)
            await self.update_wallet(ctx.guild.id, ctx.author.id, -fine)
            view = self.create_response(
                "🚔 Rob Failed",
                f"You got caught trying to rob {member.name} and paid a fine of **{fine:,}** coins!",
                ERROR_COLOR
            )
        else:
            stolen = int(target_wallet * random.uniform(0.1, 0.3))
            await self.update_wallet(ctx.guild.id, member.id, -stolen)
            await self.update_wallet(ctx.guild.id, ctx.author.id, stolen)
            view = self.create_response(
                "💰 Rob Successful",
                f"You stole **{stolen:,}** coins from {member.name}!",
                SUCCESS_COLOR
            )
        
        await ctx.send(view=view)

    @economy.command(name="leaderboard", aliases=['lb', 'rich', 'top'])
    @blacklist_check()
    @ignore_check()
    async def leaderboard(self, ctx: commands.Context):
        """View the richest users"""
        async with self.db.execute(
            "SELECT user_id, wallet, bank FROM users WHERE guild_id = ? ORDER BY (wallet + bank) DESC LIMIT 10",
            (ctx.guild.id,)
        ) as cursor:
            results = await cursor.fetchall()
        
        if not results:
            view = self.create_response(
                "📊 Leaderboard",
                "No economy data available yet",
                INFO_COLOR
            )
            return await ctx.send(view=view)
        
        description = ""
        for idx, (user_id, wallet, bank) in enumerate(results, 1):
            user = ctx.guild.get_member(user_id)
            if user:
                total = wallet + bank
                medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"**{idx}.**"
                description += f"{medal} {user.name} - **{total:,}** coins\n"
        
        view = self.create_response(
            "💰 Economy Leaderboard",
            description,
            INFO_COLOR
        )
        await ctx.send(view=view)

    @economy.command(name="shop", aliases=['store'])
    @blacklist_check()
    @ignore_check()
    async def shop(self, ctx: commands.Context):
        """View the shop"""
        async with self.db.execute(
            "SELECT item_name, item_price, item_description FROM shop_items WHERE guild_id = ?",
            (ctx.guild.id,)
        ) as cursor:
            items = await cursor.fetchall()
        
        if not items:
            view = self.create_response(
                "🛒 Shop",
                "The shop is empty",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        description = ""
        for item_name, price, desc in items:
            description += f"**{item_name}** - {price:,} coins\n{desc}\n\n"
        
        view = self.create_response(
            "🛒 Shop",
            description + "-# Use `/economy buy <item>` to purchase",
            INFO_COLOR
        )
        await ctx.send(view=view)

    @economy.command(name="buy")
    @blacklist_check()
    @ignore_check()
    async def buy(self, ctx: commands.Context, *, item_name: str):
        """Buy an item from the shop"""
        async with self.db.execute(
            "SELECT item_price FROM shop_items WHERE guild_id = ? AND LOWER(item_name) = LOWER(?)",
            (ctx.guild.id, item_name)
        ) as cursor:
            result = await cursor.fetchone()
        
        if not result:
            view = self.create_response(
                "❌ Item Not Found",
                f"Item **{item_name}** not found in shop",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        price = result[0]
        wallet, bank, bank_limit = await self.get_user(ctx.guild.id, ctx.author.id)
        
        if wallet < price:
            view = self.create_response(
                "❌ Insufficient Funds",
                f"You need **{price:,}** coins but only have **{wallet:,}** coins",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        await self.update_wallet(ctx.guild.id, ctx.author.id, -price)
        
        async with self.db.execute(
            "SELECT quantity FROM user_inventory WHERE guild_id = ? AND user_id = ? AND item_name = ?",
            (ctx.guild.id, ctx.author.id, item_name)
        ) as cursor:
            inv_result = await cursor.fetchone()
        
        if inv_result:
            await self.db.execute(
                "UPDATE user_inventory SET quantity = quantity + 1 WHERE guild_id = ? AND user_id = ? AND item_name = ?",
                (ctx.guild.id, ctx.author.id, item_name)
            )
        else:
            await self.db.execute(
                "INSERT INTO user_inventory (guild_id, user_id, item_name, quantity) VALUES (?, ?, ?, 1)",
                (ctx.guild.id, ctx.author.id, item_name)
            )
        
        await self.db.commit()
        
        view = self.create_response(
            "✅ Purchase Successful",
            f"You bought **{item_name}** for **{price:,}** coins",
            SUCCESS_COLOR
        )
        await ctx.send(view=view)

    @economy.command(name="inventory", aliases=['inv'])
    @blacklist_check()
    @ignore_check()
    async def inventory(self, ctx: commands.Context, member: discord.Member = None):
        """View your or someone's inventory"""
        member = member or ctx.author
        
        async with self.db.execute(
            "SELECT item_name, quantity FROM user_inventory WHERE guild_id = ? AND user_id = ?",
            (ctx.guild.id, member.id)
        ) as cursor:
            items = await cursor.fetchall()
        
        if not items:
            view = self.create_response(
                "🎒 Inventory",
                f"{member.name}'s inventory is empty",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        description = ""
        for item_name, quantity in items:
            description += f"**{item_name}** x{quantity}\n"
        
        view = self.create_response(
            f"🎒 {member.display_name}'s Inventory",
            description,
            INFO_COLOR
        )
        await ctx.send(view=view)

    @economy.command(name="additem")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def additem(self, ctx: commands.Context, price: int, *, name_and_desc: str):
        """Add an item to the shop (Admin only) Format: price name | description"""
        if " | " not in name_and_desc:
            view = self.create_response(
                "❌ Invalid Format",
                "Format: `economy additem <price> <name> | <description>`",
                ERROR_COLOR
            )
            return await ctx.send(view=view)
        
        item_name, item_desc = name_and_desc.split(" | ", 1)
        
        await self.db.execute(
            "INSERT OR REPLACE INTO shop_items (guild_id, item_name, item_price, item_description) VALUES (?, ?, ?, ?)",
            (ctx.guild.id, item_name.strip(), price, item_desc.strip())
        )
        await self.db.commit()
        
        view = self.create_response(
            "✅ Item Added",
            f"Added **{item_name}** to shop for **{price:,}** coins",
            SUCCESS_COLOR
        )
        await ctx.send(view=view)

    @economy.command(name="deleteitem")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def deleteitem(self, ctx: commands.Context, *, item_name: str):
        """Remove an item from the shop (Admin only)"""
        await self.db.execute(
            "DELETE FROM shop_items WHERE guild_id = ? AND LOWER(item_name) = LOWER(?)",
            (ctx.guild.id, item_name)
        )
        await self.db.commit()
        
        view = self.create_response(
            "✅ Item Removed",
            f"Removed **{item_name}** from shop",
            SUCCESS_COLOR
        )
        await ctx.send(view=view)

    @economy.command(name="addmoney")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def addmoney(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Add money to a user (Admin only)"""
        await self.update_wallet(ctx.guild.id, member.id, amount)
        
        view = self.create_response(
            "✅ Money Added",
            f"Added **{amount:,}** coins to {member.name}'s wallet",
            SUCCESS_COLOR
        )
        await ctx.send(view=view)

    @economy.command(name="removemoney")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def removemoney(self, ctx: commands.Context, member: discord.Member, amount: int):
        """Remove money from a user (Admin only)"""
        await self.update_wallet(ctx.guild.id, member.id, -amount)
        
        view = self.create_response(
            "✅ Money Removed",
            f"Removed **{amount:,}** coins from {member.name}'s wallet",
            SUCCESS_COLOR
        )
        await ctx.send(view=view)

async def setup(bot):
    await bot.add_cog(Economy(bot))
