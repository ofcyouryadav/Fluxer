import discord
from discord.ext import commands
import json
import os
from discord.ui import Button, View
from utils.Tools import *

color = 0x2f3136


class Starboard(commands.Cog):
    """Starboard system"""

    def __init__(self, bot):
        self.bot = bot
        self.color = color
        self.load_starboard_data()

    def help_custom(self):
        emoji = '<:nexus_ColouredStar:1149251932779712563>'
        label = "Starboard"
        description = "Shows You Starboard Commands."
        return emoji, label, description

    def load_starboard_data(self):
        if os.path.exists("starboard_data.json"):
            with open("starboard_data.json", "r") as file:
                self.starboard_data = json.load(file)
        else:
            self.starboard_data = {}

    def save_starboard_data(self):
        with open("starboard_data.json", "w") as file:
            json.dump(self.starboard_data, file, indent=4)

    def get_starboard_config(self, guild_id):
        if guild_id not in self.starboard_data:
            self.starboard_data[guild_id] = {
                "starboard_channel_id": None,
                "starboard_limit": 5,
                "starboard_locked": False
            }
        return self.starboard_data[guild_id]

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild_id = str(payload.guild_id)
        starboard_config = self.get_starboard_config(guild_id)
        starboard_channel_id = starboard_config.get("starboard_channel_id")
        starboard_limit = starboard_config.get("starboard_limit")
        starboard_locked = starboard_config.get("starboard_locked")

        if not starboard_channel_id or starboard_locked:
            return

        starboard_channel = self.bot.get_channel(starboard_channel_id)
        if not starboard_channel:
            return

        message_id = payload.message_id
        channel_id = payload.channel_id

        if payload.emoji.name == "⭐":
            channel = self.bot.get_channel(channel_id)
            message = await channel.fetch_message(message_id)
            reactions = message.reactions

            for reaction in reactions:
                if str(reaction.emoji) == "⭐" and reaction.count == starboard_limit:
                    author = message.author
                    message_link = f'https://discord.com/channels/{payload.guild_id}/{channel_id}/{message_id}'
                    message_link1 = f'https://discord.com/channels/{payload.guild_id}/{channel_id}'
                    
                    button = Button(label="Go to original message", url=message_link)
                    view = View()
                    view.add_item(button)

                    starboard_embed = discord.Embed(color=self.color)

                    if message.content:
                        starboard_embed.description = message.content

                    if message.attachments:
                        image_url = message.attachments[0].url
                        starboard_embed.set_image(url=image_url)

                    starboard_embed.set_footer(text=f"{message.created_at.month}/{message.created_at.day}/{message.created_at.year}")
                    starboard_embed.timestamp = discord.utils.utcnow()

                    if message.reference:
                        try:
                            replied_message = await channel.fetch_message(message.reference.message_id)
                            replied_author = replied_message.author
                            replied_author_mention = replied_author.name if replied_author else "Unknown User"
                            starboard_embed.add_field(name="Replying to...", value=replied_author_mention, inline=False)
                        except:
                            pass

                    starboard_embed.set_author(name=author.name, icon_url=author.avatar.url if author.avatar else author.default_avatar.url)
                    await starboard_channel.send(f"⭐ **{reaction.count}** {message_link1}", embed=starboard_embed, view=view)

    @commands.group(
        name="starboard",
        help="Sets up the starboard for this server.",
        aliases=['sb'],
        invoke_without_command=True
    )
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def starboard(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @starboard.command(name="info", help="Shows starboard configuration")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def info(self, ctx):
        guild_id = str(ctx.guild.id)
        starboard_config = self.get_starboard_config(guild_id)
        starboard_channel_id = starboard_config.get("starboard_channel_id")
        starboard_limit = starboard_config.get("starboard_limit")
        starboard_locked = starboard_config.get("starboard_locked")

        channel_mention = f"<#{starboard_channel_id}>" if starboard_channel_id else "Not set"
        locked_status = "Locked" if starboard_locked else "Unlocked"

        embed = discord.Embed(title="Starboard Settings", color=self.color)
        embed.add_field(name="Channel:", value=f"{channel_mention}", inline=False)
        embed.add_field(name="Limit:", value=f">>> {starboard_limit}", inline=False)
        embed.add_field(name="Status:", value=f">>> {locked_status}", inline=False)

        await ctx.send(embed=embed)

    @starboard.command(name="limit", help="Set the starboard reaction limit")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def limit(self, ctx, limit: int):
        guild_id = str(ctx.guild.id)
        starboard_config = self.get_starboard_config(guild_id)
        starboard_config["starboard_limit"] = limit
        self.save_starboard_data()

        embed = discord.Embed(
            description=f"<:Nexus_tick:1144687280540369018> | Successfully set the Starboard limit to: {limit}",
            color=self.color
        )
        await ctx.send(embed=embed)

    @starboard.command(name="lock", help="Lock the starboard")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def lock(self, ctx):
        guild_id = str(ctx.guild.id)
        starboard_config = self.get_starboard_config(guild_id)
        starboard_config["starboard_locked"] = True
        self.save_starboard_data()

        embed = discord.Embed(
            description=f"<:Nexus_tick:1144687280540369018> | Successfully Starboard locked",
            color=self.color
        )
        await ctx.send(embed=embed)

    @starboard.command(name="unlock", help="Unlock the starboard")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def unlock(self, ctx):
        guild_id = str(ctx.guild.id)
        starboard_config = self.get_starboard_config(guild_id)
        starboard_config["starboard_locked"] = False
        self.save_starboard_data()

        embed = discord.Embed(
            description=f"<:Nexus_tick:1144687280540369018> | Successfully Starboard unlocked",
            color=self.color
        )
        await ctx.send(embed=embed)

    @starboard.command(name="setup", help="Setup starboard channel")
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        starboard_config = self.get_starboard_config(guild_id)
        starboard_config["starboard_channel_id"] = channel.id
        self.save_starboard_data()

        embed = discord.Embed(
            description=f"<:Nexus_tick:1144687280540369018> | Successfully Starboard channel set to {channel.name}",
            color=self.color
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Starboard(bot))
