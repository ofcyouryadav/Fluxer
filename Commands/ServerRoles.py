import discord
from discord.ext import commands
from utils.Tools import *

color = 0x2f3136


class ServerRoles(commands.Cog):
    """Server role management"""

    def __init__(self, bot):
        self.bot = bot
        self.color = color

    def help_custom(self):
        emoji = '<:ayden_server:1136705394908082276>'
        label = "Server"
        description = "Shows You Server Commands."
        return emoji, label, description

    async def add_role(self, *, role: int, member: discord.Member):
        if member.guild.me.guild_permissions.manage_roles:
            role = discord.Object(id=int(role))
            await member.add_roles(role, reason="Server Role Added")

    async def remove_role(self, *, role: int, member: discord.Member):
        if member.guild.me.guild_permissions.manage_roles:
            role = discord.Object(id=int(role))
            await member.remove_roles(role, reason="Server Role Removed")

    @commands.command(
        name="srstaff",
        description="Gives the staff role to the user.",
        aliases=['serverstaff'],
        help="Gives the staff role to the user."
    )
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def _staff(self, ctx, member: discord.Member):
        if data := getConfig(ctx.guild.id):
            lol = data['reqrole']
            own = data['staff']
            role = ctx.guild.get_role(own)
            
            if data["reqrole"] is not None:
                req = ctx.guild.get_role(lol)
                if ctx.author == ctx.guild.owner or req in ctx.author.roles:
                    if data["staff"] is not None:
                        if role not in member.roles:
                            await self.add_role(role=own, member=member)
                            hacker = discord.Embed(
                                description=f"<:Nexus_tick:1144687280540369018> | Successfully Given <@&{own}> To {member.name}",
                                color=self.color
                            )
                            hacker.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                            await ctx.send(embed=hacker)
                        elif role in member.roles:
                            await self.remove_role(role=own, member=member)
                            hacker6 = discord.Embed(
                                description=f"<:Nexus_tick:1144687280540369018> | Successfully Removed <@&{own}> From {member.name}",
                                color=self.color
                            )
                            hacker6.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                            await ctx.send(embed=hacker6)
                    else:
                        hacker1 = discord.Embed(
                            description=f"<:Nexus_cross:1144687282176147629> | Staff role is not setuped in {ctx.guild.name}",
                            color=self.color
                        )
                        hacker1.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                        await ctx.send(embed=hacker1)
                else:
                    hacker3 = discord.Embed(
                        description=f"<:Nexus_cross:1144687282176147629> | You need {req.name} to run this command.",
                        color=self.color
                    )
                    hacker3.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                    await ctx.send(embed=hacker3)
            else:
                hacker4 = discord.Embed(
                    description=f"<:Nexus_cross:1144687282176147629> | Req role is not setuped in {ctx.guild.name}",
                    color=self.color
                )
                hacker4.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                await ctx.send(embed=hacker4)

    @commands.command(
        name="srgirl",
        description="Gives the girl role to the user.",
        aliases=['servergirl', 'cuties'],
        help="Gives the girl role to the user."
    )
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def _girl(self, ctx, member: discord.Member):
        if data := getConfig(ctx.guild.id):
            lol = data['reqrole']
            own = data['girl']
            role = ctx.guild.get_role(own)
            
            if data["reqrole"] is not None:
                req = ctx.guild.get_role(lol)
                if ctx.author == ctx.guild.owner or req in ctx.author.roles:
                    if data["girl"] is not None:
                        if role not in member.roles:
                            await self.add_role(role=own, member=member)
                            hacker = discord.Embed(
                                description=f"<:Nexus_tick:1144687280540369018> | Successfully Given <@&{own}> To {member.name}",
                                color=self.color
                            )
                            hacker.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                            await ctx.send(embed=hacker)
                        elif role in member.roles:
                            await self.remove_role(role=own, member=member)
                            hacker6 = discord.Embed(
                                description=f"<:Nexus_tick:1144687280540369018> | Successfully Removed <@&{own}> From {member.name}",
                                color=self.color
                            )
                            hacker6.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                            await ctx.send(embed=hacker6)
                    else:
                        hacker1 = discord.Embed(
                            description=f"<:Nexus_cross:1144687282176147629> | Girl role is not setuped in {ctx.guild.name}",
                            color=self.color
                        )
                        hacker1.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                        await ctx.send(embed=hacker1)
                else:
                    hacker3 = discord.Embed(
                        description=f"<:Nexus_cross:1144687282176147629> | You need {req.name} to run this command.",
                        color=self.color
                    )
                    hacker3.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                    await ctx.send(embed=hacker3)
            else:
                hacker4 = discord.Embed(
                    description=f"<:Nexus_cross:1144687282176147629> | Req role is not setuped in {ctx.guild.name}",
                    color=self.color
                )
                hacker4.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                await ctx.send(embed=hacker4)

    @commands.command(
        name="srvip",
        description="Gives the vip role to the user.",
        aliases=['servervip'],
        help="Gives the vip role to the user."
    )
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def _vip(self, ctx, member: discord.Member):
        if data := getConfig(ctx.guild.id):
            lol = data['reqrole']
            own = data['vip']
            role = ctx.guild.get_role(own)
            
            if data["reqrole"] is not None:
                req = ctx.guild.get_role(lol)
                if ctx.author == ctx.guild.owner or req in ctx.author.roles:
                    if data["vip"] is not None:
                        if role not in member.roles:
                            await self.add_role(role=own, member=member)
                            hacker = discord.Embed(
                                description=f"<:Nexus_tick:1144687280540369018> | Successfully Given <@&{own}> To {member.name}",
                                color=self.color
                            )
                            hacker.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                            await ctx.send(embed=hacker)
                        elif role in member.roles:
                            await self.remove_role(role=own, member=member)
                            hacker6 = discord.Embed(
                                description=f"<:Nexus_tick:1144687280540369018> | Successfully Removed <@&{own}> From {member.name}",
                                color=self.color
                            )
                            hacker6.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                            await ctx.send(embed=hacker6)
                    else:
                        hacker1 = discord.Embed(
                            description=f"<:Nexus_cross:1144687282176147629> | Vip role is not setuped in {ctx.guild.name}",
                            color=self.color
                        )
                        hacker1.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                        await ctx.send(embed=hacker1)
                else:
                    hacker3 = discord.Embed(
                        description=f"<:Nexus_cross:1144687282176147629> | You need {req.name} to run this command.",
                        color=self.color
                    )
                    hacker3.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                    await ctx.send(embed=hacker3)
            else:
                hacker4 = discord.Embed(
                    description=f"<:Nexus_cross:1144687282176147629> | Req role is not setuped in {ctx.guild.name}",
                    color=self.color
                )
                hacker4.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                await ctx.send(embed=hacker4)

    @commands.command(
        name="srguest",
        description="Gives the guest role to the user.",
        aliases=['serverguest'],
        help="Gives the guest role to the user."
    )
    @blacklist_check()
    @ignore_check()
    @commands.has_permissions(administrator=True)
    async def _guest(self, ctx, member: discord.Member):
        if data := getConfig(ctx.guild.id):
            lol = data['reqrole']
            own = data['guest']
            role = ctx.guild.get_role(own)
            
            if data["reqrole"] is not None:
                req = ctx.guild.get_role(lol)
                if ctx.author == ctx.guild.owner or req in ctx.author.roles:
                    if data["guest"] is not None:
                        if role not in member.roles:
                            await self.add_role(role=own, member=member)
                            hacker = discord.Embed(
                                description=f"<:Nexus_tick:1144687280540369018> | Successfully Given <@&{own}> To {member.name}",
                                color=self.color
                            )
                            hacker.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                            await ctx.send(embed=hacker)
                        elif role in member.roles:
                            await self.remove_role(role=own, member=member)
                            hacker6 = discord.Embed(
                                description=f"<:Nexus_tick:1144687280540369018> | Successfully Removed <@&{own}> From {member.name}",
                                color=self.color
                            )
                            hacker6.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                            await ctx.send(embed=hacker6)
                    else:
                        hacker1 = discord.Embed(
                            description=f"<:Nexus_cross:1144687282176147629> | Guest role is not setuped in {ctx.guild.name}",
                            color=self.color
                        )
                        hacker1.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                        await ctx.send(embed=hacker1)
                else:
                    hacker3 = discord.Embed(
                        description=f"<:Nexus_cross:1144687282176147629> | You need {req.name} to run this command.",
                        color=self.color
                    )
                    hacker3.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                    await ctx.send(embed=hacker3)
            else:
                hacker4 = discord.Embed(
                    description=f"<:Nexus_cross:1144687282176147629> | Req role is not setuped in {ctx.guild.name}",
                    color=self.color
                )
                hacker4.set_author(name=f"{ctx.author}", icon_url=f"{ctx.author.avatar}")
                await ctx.send(embed=hacker4)


async def setup(bot):
    await bot.add_cog(ServerRoles(bot))
