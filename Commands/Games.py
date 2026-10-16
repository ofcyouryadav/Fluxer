import discord
from discord.ext import commands
from discord import ui
from discord.ui import LayoutView, Container, TextDisplay, Separator
import random
import asyncio
from utils.Tools import blacklist_check, ignore_check

try:
    import discord_games as games
    from discord_games import button_games as btn
    GAMES_AVAILABLE = True
except ImportError:
    GAMES_AVAILABLE = False

color = 0x2f3136


class Timer:
    """Simple timer for tracking time"""
    def __init__(self):
        self.start_time = None
        self.total_time = 0
    
    def __enter__(self):
        self.start_time = asyncio.get_event_loop().time()
        return self
    
    def __exit__(self, *args):
        self.total_time = asyncio.get_event_loop().time() - self.start_time


class Games(commands.Cog):
    """Fun game commands"""

    def __init__(self, bot):
        self.bot = bot
        self.color = color

    @commands.command(
        name="akinator",
        help="Play akinator game with bot",
        aliases=["aki"]
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def akinator(self, ctx):
        """Play Akinator game"""
        if not GAMES_AVAILABLE:
            return await ctx.send("Game library not available. Please install discord-games.")
        
        game = btn.BetaAkinator()
        await game.start(ctx, timeout=None)

    @commands.command(
        name="chess",
        help="Play Chess Game with another player"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def chess(self, ctx, player: discord.Member):
        """Play Chess game"""
        if not GAMES_AVAILABLE:
            return await ctx.send("Game library not available. Please install discord-games.")
        
        if player == ctx.author:
            return await ctx.send("You cannot play against yourself!")
        if player.bot:
            return await ctx.send("You cannot play with bots!")
        
        game = btn.BetaChess(white=ctx.author, black=player)
        await game.start(ctx)

    @commands.command(
        name="hangman",
        help="Play hangman with bot"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def hangman(self, ctx):
        """Play Hangman game"""
        if not GAMES_AVAILABLE:
            return await ctx.send("Game library not available. Please install discord-games.")
        
        game = games.Hangman()
        await game.start(ctx)

    @commands.command(
        name="typerace",
        help="Check who is fast in typing",
        aliases=["tr", "typeracer"]
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def typerace(self, ctx):
        """Play Type Race game"""
        if not GAMES_AVAILABLE:
            return await ctx.send("Game library not available. Please install discord-games.")
        
        game = games.TypeRacer()
        await game.start(ctx, timeout=60)

    @commands.command(
        name="rps",
        help="Play Rock Paper Scissors",
        aliases=["rockpaperscissors"]
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def rps(self, ctx, player: discord.Member = None):
        """Play Rock Paper Scissors"""
        if not GAMES_AVAILABLE:
            return await ctx.send("Game library not available. Please install discord-games.")
        
        game = btn.BetaRockPaperScissors(player)
        await game.start(ctx, timeout=120)

    @commands.command(
        name="tic-tac-toe",
        help="Play tic-tac-toe game",
        aliases=["ttt", "tictactoe"]
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def tictactoe(self, ctx, player: discord.Member):
        """Play Tic Tac Toe"""
        if not GAMES_AVAILABLE:
            return await ctx.send("Game library not available. Please install discord-games.")
        
        if player == ctx.author:
            return await ctx.send("You cannot play against yourself!")
        if player.bot:
            return await ctx.send("You cannot play with bots!")
        
        game = btn.BetaTictactoe(cross=ctx.author, circle=player)
        await game.start(ctx, timeout=30)

    @commands.command(
        name="wordle",
        help="Play Wordle game"
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def wordle(self, ctx):
        """Play Wordle"""
        if not GAMES_AVAILABLE:
            return await ctx.send("Game library not available. Please install discord-games.")
        
        game = games.Wordle()
        await game.start(ctx, timeout=120)

    @commands.command(
        name="2048",
        help="Play 2048 game",
        aliases=["twenty48"]
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def twenty_forty_eight(self, ctx):
        """Play 2048"""
        if not GAMES_AVAILABLE:
            return await ctx.send("Game library not available. Please install discord-games.")
        
        game = btn.BetaTwenty48()
        await game.start(ctx, win_at=2048)

    @commands.command(
        name="memory-game",
        help="How strong is your memory?",
        aliases=["memory"]
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def memory_game(self, ctx):
        """Play Memory Game"""
        if not GAMES_AVAILABLE:
            return await ctx.send("Game library not available. Please install discord-games.")
        
        game = btn.MemoryGame()
        await game.start(ctx)

    @commands.command(
        name="number-slider",
        help="Slide numbers with bot",
        aliases=["slider"]
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def number_slider(self, ctx):
        """Play Number Slider"""
        if not GAMES_AVAILABLE:
            return await ctx.send("Game library not available. Please install discord-games.")
        
        game = btn.NumberSlider()
        await game.start(ctx)

    @commands.command(
        name="battleship",
        help="Enjoy the fight between battle ships",
        aliases=["battle-ship"]
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def battleship(self, ctx, player: discord.Member):
        """Play Battleship"""
        if not GAMES_AVAILABLE:
            return await ctx.send("Game library not available. Please install discord-games.")
        
        if player == ctx.author:
            return await ctx.send("You cannot play against yourself!")
        if player.bot:
            return await ctx.send("You cannot play with bots!")
        
        game = btn.BetaBattleShip(player1=ctx.author, player2=player)
        await game.start(ctx)

    @commands.command(
        name="country-guesser",
        help="Guess name of the country",
        aliases=["guess", "guesser", "countryguesser"]
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def country_guesser(self, ctx):
        """Play Country Guesser"""
        if not GAMES_AVAILABLE:
            return await ctx.send("Game library not available. Please install discord-games.")
        
        game = games.CountryGuesser(is_flags=True, hints=2)
        await game.start(ctx)

    @commands.command(name="reaction", help="Test your reaction speed")
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def reaction(self, ctx):
        """Reaction speed test game"""
        emoji = ["🍪", "🎉", "🧋", "🍒", "🍑"]
        random_emoji = random.choice(emoji)
        random.shuffle(emoji)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## Reaction Time Test"))
        container.add_item(Separator())
        container.add_item(TextDisplay("After 1-15 seconds I will reveal the emoji.\nBe ready to click it!"))
        
        view.add_item(container)
        first = await ctx.send(view=view)
        
        for react in emoji:
            await first.add_reaction(react)
        
        await asyncio.sleep(2.5)
        
        # Update message to get ready
        container = Container()
        container.add_item(TextDisplay("## Get Ready!"))
        container.add_item(Separator())
        container.add_item(TextDisplay("⚡ Prepare yourself..."))
        view2 = LayoutView()
        view2.add_item(container)
        await first.edit(view=view2)
        
        await asyncio.sleep(random.randint(1, 15))
        
        # Show the emoji to click
        container = Container()
        container.add_item(TextDisplay(f"## GET THE {random_emoji} EMOJI!"))
        container.add_item(Separator())
        container.add_item(TextDisplay("🏃 Click it now!"))
        view3 = LayoutView()
        view3.add_item(container)
        await first.edit(view=view3)

        def check(reaction, user):
            return (reaction.message.id == first.id and 
                    str(reaction.emoji) == random_emoji and 
                    user != self.bot.user)

        try:
            with Timer() as timer:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=15)
        except asyncio.TimeoutError:
            container = Container()
            container.add_item(TextDisplay("## Timeout!"))
            container.add_item(Separator())
            container.add_item(TextDisplay("⏰ Time ran out! No one got it in time."))
            view4 = LayoutView()
            view4.add_item(container)
            await first.edit(view=view4)
        else:
            if str(reaction.emoji) == random_emoji:
                gettime = timer.total_time * 1000
                total_second = f"**{gettime:.2f}ms**"
                if gettime > 1000:
                    gettime = gettime / 1000
                    total_second = f"**{gettime:.2f}s**"
                
                container = Container()
                container.add_item(TextDisplay("## Winner! 🏆"))
                container.add_item(Separator())
                container.add_item(TextDisplay(f"{user.name} got the {random_emoji} in {total_second}!"))
                view5 = LayoutView()
                view5.add_item(container)
                await first.edit(view=view5)


async def setup(bot):
    await bot.add_cog(Games(bot))
