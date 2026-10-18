import discord
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay, Separator, MediaGallery
import db.boost as boost_db

SUCCESS_COLOR = 0x00ff00

class BoostEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Detect when a member boosts the server"""
        try:
            before_boosting = before.premium_since is None
            after_boosting = after.premium_since is not None
            
            if before_boosting and after_boosting:
                config = await boost_db.get_config(after.guild.id)
                
                if not config or not config.get("enabled", 1):
                    return
                
                channel = after.guild.get_channel(config.get("channel_id"))
                
                if not channel:
                    return
                
                message_text = config.get("message") or "🚀 {user} just boosted **{server}**! Thank you for your support! 💎"
                embed_title = config.get("embed_title") or "🚀 Server Boosted!"
                embed_description = config.get("embed_description") or "Thank you {user} for boosting **{server}**! 💎\n\nWe now have **{boostcount}** boosts at level **{boostlevel}**!"
                embed_footer = config.get("embed_footer") or "Boost #{boostcount}"
                
                replacements = {
                    "{user}": after.name,
                    "{username}": after.name,
                    "{server}": after.guild.name,
                    "{boostcount}": str(after.guild.premium_subscription_count),
                    "{boostlevel}": str(after.guild.premium_tier)
                }
                
                for old, new in replacements.items():
                    if message_text:
                        message_text = message_text.replace(old, new)
                    if embed_title:
                        embed_title = embed_title.replace(old, new)
                    if embed_description:
                        embed_description = embed_description.replace(old, new)
                    if embed_footer:
                        embed_footer = embed_footer.replace(old, new)
                
                if config.get("embed_enabled", 1):
                    view = LayoutView()
                    container = Container()
                    
                    container.add_item(TextDisplay(f"## {embed_title}"))
                    container.add_item(Separator())
                    container.add_item(TextDisplay(embed_description))
                    
                    thumbnail = config.get("embed_thumbnail", "user_avatar")
                    if thumbnail == "user_avatar" and after.avatar:
                        container.add_item(Separator())
                        gallery = MediaGallery()
                        gallery.add_item(media=after.avatar.url)
                        container.add_item(gallery)
                    elif thumbnail == "server_icon" and after.guild.icon:
                        container.add_item(Separator())
                        gallery = MediaGallery()
                        gallery.add_item(media=after.guild.icon.url)
                        container.add_item(gallery)
                    
                    embed_image = config.get("embed_image")
                    if embed_image:
                        container.add_item(Separator())
                        gallery = MediaGallery()
                        gallery.add_item(media=embed_image)
                        container.add_item(gallery)
                    
                    container.add_item(Separator())
                    container.add_item(TextDisplay(f"*{embed_footer}*"))
                    
                    view.add_item(container)
                    await channel.send(view=view)
                else:
                    message_text = message_text or f"🚀 {after.name} just boosted **{after.guild.name}**!"
                    await channel.send(message_text)
                    
        except Exception as e:
            print(f"Error in boost event: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(BoostEvents(bot))
