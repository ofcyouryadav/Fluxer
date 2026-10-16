import discord
from discord.ext import commands, tasks
from discord.ui import LayoutView, Container, TextDisplay, Separator, ActionRow, Button
from typing import Optional
from datetime import datetime, timezone, timedelta
import random
import asyncio

COLOR = 0x2f3136
SUCCESS_COLOR = 0x00ff88
ERROR_COLOR = 0xff0033
GIVEAWAY_COLOR = 0xff69b4

class Giveaway(commands.Cog):
    """Giveaway management system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.color = COLOR
        self.giveaways_collection = bot.db["giveaways"]
        self.check_giveaways.start()
    
    async def cog_unload(self):
        self.check_giveaways.cancel()
    
    @tasks.loop(seconds=30)
    async def check_giveaways(self):
        """Check for ended giveaways and pick winners"""
        now = datetime.now(timezone.utc)
        
        # Find ended giveaways (not paused)
        ended = await self.giveaways_collection.find({
            "ended": False,
            "paused": {"$ne": True},
            "end_time": {"$lte": now}
        }).to_list(None)
        
        for giveaway in ended:
            try:
                guild = self.bot.get_guild(giveaway["guild_id"])
                if not guild:
                    continue
                
                channel = guild.get_channel(giveaway["channel_id"])
                if not channel:
                    continue
                
                try:
                    message = await channel.fetch_message(giveaway["message_id"])
                except:
                    continue
                
                # Pick winners
                participants = giveaway.get("participants", [])
                winners_count = giveaway.get("winners", 1)
                
                if len(participants) < winners_count:
                    winners = participants
                else:
                    winners = random.sample(participants, winners_count)
                
                # Update database
                await self.giveaways_collection.update_one(
                    {"_id": giveaway["_id"]},
                    {"$set": {"ended": True, "winners": winners}}
                )
                
                # Announce winners
                if winners:
                    winners_mentions = " ".join([f"<@{w}>" for w in winners])
                    
                    view = LayoutView()
                    container = Container()
                    
                    container.add_item(TextDisplay("## 🎉 Giveaway Ended!"))
                    container.add_item(Separator())
                    
                    desc = f"**Prize:** {giveaway['prize']}\n"
                    desc += f"**Winners:** {winners_mentions}\n"
                    desc += f"**Participants:** {len(participants)}"
                    
                    container.add_item(TextDisplay(desc))
                    container.add_item(Separator())
                    container.add_item(TextDisplay(f"-# Hosted by <@{giveaway['host_id']}>"))
                    
                    view.add_item(container)
                    
                    await channel.send(view=view)
                    
                    # Send DMs to winners
                    for winner_id in winners:
                        try:
                            winner = self.bot.get_user(winner_id)
                            if winner:
                                win_view = LayoutView()
                                win_container = Container()
                                win_container.add_item(TextDisplay("## 🏆 You Won!"))
                                win_container.add_item(Separator())
                                win_container.add_item(TextDisplay(
                                    f"🎉 Congratulations! You won the giveaway!\n\n"
                                    f"**Prize:** {giveaway['prize']}\n"
                                    f"**Server:** {guild.name}\n\n"
                                    f"Contact the server admins to claim your prize!"
                                ))
                                win_view.add_item(win_container)
                                await winner.send(view=win_view)
                        except discord.Forbidden:
                            pass
                        except Exception as e:
                            print(f"Error sending winner DM: {e}")
                    
                    # Edit original message
                    try:
                        ended_view = LayoutView()
                        ended_container = Container()
                        
                        ended_container.add_item(TextDisplay("## 🎉 GIVEAWAY ENDED"))
                        ended_container.add_item(Separator())
                        
                        ended_desc = f"**Prize:** {giveaway['prize']}\n"
                        ended_desc += f"**Winners:** {winners_mentions}\n"
                        ended_desc += f"**Ended:** <t:{int(now.timestamp())}:R>"
                        
                        ended_container.add_item(TextDisplay(ended_desc))
                        ended_view.add_item(ended_container)
                        
                        await message.edit(view=ended_view)
                    except:
                        pass
                else:
                    view = LayoutView()
                    container = Container()
                    container.add_item(TextDisplay("## 😢 Giveaway Ended"))
                    container.add_item(Separator())
                    container.add_item(TextDisplay(f"**Prize:** {giveaway['prize']}\n\nNo valid participants!"))
                    view.add_item(container)
                    
                    await channel.send(view=view)
                    
            except Exception as e:
                print(f"Error ending giveaway: {e}")
    
    @check_giveaways.before_loop
    async def before_check_giveaways(self):
        await self.bot.wait_until_ready()
    
    @commands.hybrid_command(name="gstart", aliases=["giveaway"])
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def gstart(self, ctx, duration: str, winners: int, *, prize: str):
        """Start a giveaway (e.g., /gstart 1h 1 Nitro)
        
        Duration formats: 30s, 5m, 2h, 1d
        """
        # Parse duration
        try:
            time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
            unit = duration[-1]
            value = int(duration[:-1])
            
            if unit not in time_units:
                raise ValueError()
            
            seconds = value * time_units[unit]
            end_time = datetime.now(timezone.utc) + timedelta(seconds=seconds)
            
        except:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ **Invalid Duration**\n\nUse format: 30s, 5m, 2h, 1d"))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        if winners < 1 or winners > 20:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ **Invalid Winners Count**\n\nMust be between 1 and 20."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        # Create giveaway message
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## 🎉 GIVEAWAY! 🎉"))
        container.add_item(Separator())
        
        desc = f"**Prize:** {prize}\n"
        desc += f"**Winners:** {winners}\n"
        desc += f"**Ends:** <t:{int(end_time.timestamp())}:R>\n"
        desc += f"**Hosted by:** {ctx.author.name}\n\n"
        desc += "Click the button below to enter!"
        
        container.add_item(TextDisplay(desc))
        
        # Add join button
        button_row = ActionRow()
        join_button = Button(
            style=discord.ButtonStyle.green,
            label="Join Giveaway",
            emoji="🎉",
            custom_id=f"giveaway_join_{ctx.message.id if hasattr(ctx, 'message') else int(end_time.timestamp())}"
        )
        
        async def join_callback(interaction):
            await self.handle_join(interaction)
        
        join_button.callback = join_callback
        button_row.add_item(join_button)
        container.add_item(button_row)
        
        view.add_item(container)
        
        message = await ctx.send(view=view)
        
        # Save to database
        await self.giveaways_collection.insert_one({
            "guild_id": ctx.guild.id,
            "channel_id": ctx.channel.id,
            "message_id": message.id,
            "host_id": ctx.author.id,
            "prize": prize,
            "winners": winners,
            "end_time": end_time,
            "participants": [],
            "ended": False,
            "created_at": datetime.now(timezone.utc)
        })
        
        # Confirmation
        confirm_view = LayoutView()
        confirm_container = Container()
        confirm_container.add_item(TextDisplay(f"✅ Giveaway started! Ends <t:{int(end_time.timestamp())}:R>"))
        confirm_view.add_item(confirm_container)
        await ctx.reply(view=confirm_view, ephemeral=True)
    
    async def handle_join(self, interaction: discord.Interaction):
        """Handle giveaway join button press"""
        try:
            # Find giveaway
            giveaway = await self.giveaways_collection.find_one({
                "message_id": interaction.message.id,
                "ended": False
            })
            
            if not giveaway:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("❌ This giveaway has ended or doesn't exist."))
                view.add_item(container)
                return await interaction.response.send_message(view=view, ephemeral=True)
            
            user_id = interaction.user.id
            participants = giveaway.get("participants", [])
            
            if user_id in participants:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("❌ You're already entered in this giveaway!"))
                view.add_item(container)
                return await interaction.response.send_message(view=view, ephemeral=True)
            
            # Add participant
            await self.giveaways_collection.update_one(
                {"_id": giveaway["_id"]},
                {"$push": {"participants": user_id}}
            )
            
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"✅ You've entered the giveaway!\n\n**Prize:** {giveaway['prize']}"))
            view.add_item(container)
            await interaction.response.send_message(view=view, ephemeral=True)
            
            # Send DM notification
            try:
                dm_view = LayoutView()
                dm_container = Container()
                dm_container.add_item(TextDisplay("## 🎉 Thanks for Participating!"))
                dm_container.add_item(Separator())
                dm_container.add_item(TextDisplay(
                    f"**Server:** {interaction.guild.name}\n\n"
                    f"**Prize:** {giveaway['prize']}\n"
                    f"**Ends:** <t:{int(giveaway['end_time'].timestamp())}:R>\n\n"
                    f"Good luck! 🍀"
                ))
                dm_view.add_item(dm_container)
                await interaction.user.send(view=dm_view)
            except discord.Forbidden:
                pass
        except Exception as e:
            print(f"Error in handle_join: {e}")
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle giveaway join button"""
        if not interaction.data or not interaction.data.get("custom_id", "").startswith("giveaway_join"):
            return
        await self.handle_join(interaction)
    
    @commands.hybrid_command(name="gend")
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def gend(self, ctx, message_id: str):
        """End a giveaway early by message ID"""
        try:
            msg_id = int(message_id)
        except:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Invalid message ID."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        giveaway = await self.giveaways_collection.find_one({
            "message_id": msg_id,
            "guild_id": ctx.guild.id,
            "ended": False
        })
        
        if not giveaway:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ No active giveaway found with that ID."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        # End it immediately
        await self.giveaways_collection.update_one(
            {"_id": giveaway["_id"]},
            {"$set": {"end_time": datetime.now(timezone.utc)}}
        )
        
        view = LayoutView()
        container = Container()
        container.add_item(TextDisplay("✅ Giveaway will be ended in the next check cycle (within 30 seconds)."))
        view.add_item(container)
        await ctx.reply(view=view)
    
    @commands.hybrid_command(name="greroll")
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def greroll(self, ctx, message_id: str):
        """Reroll a giveaway winner by message ID"""
        try:
            msg_id = int(message_id)
        except:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ Invalid message ID."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        giveaway = await self.giveaways_collection.find_one({
            "message_id": msg_id,
            "guild_id": ctx.guild.id,
            "ended": True
        })
        
        if not giveaway:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ No ended giveaway found with that ID."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        participants = giveaway.get("participants", [])
        if not participants:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ No participants to reroll."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        # Pick new winners
        winners_count = giveaway.get("winners", 1)
        if len(participants) < winners_count:
            new_winners = participants
        else:
            new_winners = random.sample(participants, winners_count)
        
        winners_mentions = " ".join([f"<@{w}>" for w in new_winners])
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay("## 🎉 Giveaway Rerolled!"))
        container.add_item(Separator())
        
        desc = f"**Prize:** {giveaway['prize']}\n"
        desc += f"**New Winners:** {winners_mentions}"
        
        container.add_item(TextDisplay(desc))
        
        view.add_item(container)
        
        await ctx.send(view=view)
    
    @commands.hybrid_command(name="glist")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def glist(self, ctx):
        """List all active giveaways in this server"""
        giveaways = await self.giveaways_collection.find({
            "guild_id": ctx.guild.id,
            "ended": False
        }).to_list(None)
        
        if not giveaways:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## 🎁 No Active Giveaways\n\nThere are no active giveaways in this server."))
            view.add_item(container)
            return await ctx.reply(view=view)
        
        view = LayoutView()
        container = Container()
        
        container.add_item(TextDisplay(f"## 🎁 Active Giveaways - {ctx.guild.name}"))
        container.add_item(Separator())
        
        giveaway_list = []
        for i, g in enumerate(giveaways, 1):
            channel = ctx.guild.get_channel(g["channel_id"])
            channel_mention = channel.name if channel else "Unknown"
            
            end_timestamp = int(g["end_time"].timestamp())
            participants = len(g.get("participants", []))
            status = "⏸️ Paused" if g.get("paused", False) else "✅ Active"
            
            giveaway_list.append(
                f"`{i}.` **{g['prize']}** - {status}\n"
                f"   Channel: {channel_mention} | Ends: <t:{end_timestamp}:R>\n"
                f"   Winners: {g['winners']} | Participants: {participants}\n"
                f"   Message ID: `{g['message_id']}`"
            )
        
        container.add_item(TextDisplay("\n\n".join(giveaway_list)))
        container.add_item(Separator())
        container.add_item(TextDisplay(f"-# Total: {len(giveaways)} active giveaways"))
        
        view.add_item(container)
        await ctx.reply(view=view)

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
