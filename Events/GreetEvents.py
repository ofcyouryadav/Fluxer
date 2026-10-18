import discord
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay, Separator, MediaGallery
import db.greet as greet_db

SUCCESS_COLOR = 0x00ff00

class GreetEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("[Cog] GreetEvents cog initialized")
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Send welcome message when a member joins"""
        try:
            config = await greet_db.get_config(member.guild.id)
            
            if not config or not config.get("enabled", 1):
                return
            
            channel = member.guild.get_channel(config.get("channel_id"))
            
            if not channel:
                return
            
            message_text = config.get("message") or "Welcome {user} to **{server}**!"
            embed_title = config.get("embed_title") or "Welcome!"
            embed_description = config.get("embed_description") or "Welcome {user} to **{server}**! 🎉"
            embed_footer = config.get("embed_footer") or "Member #{membercount}"
            
            replacements = {
                "{user}": member.name,
                "{username}": member.name,
                "{server}": member.guild.name,
                "{membercount}": str(member.guild.member_count)
            }
            
            if message_text:
                for old, new in replacements.items():
                    message_text = message_text.replace(old, new)
            if embed_title:
                for old, new in replacements.items():
                    embed_title = embed_title.replace(old, new)
            if embed_description:
                for old, new in replacements.items():
                    embed_description = embed_description.replace(old, new)
            if embed_footer:
                for old, new in replacements.items():
                    embed_footer = embed_footer.replace(old, new)
            
            if config.get("embed_enabled", 1):
                view = LayoutView()
                container = Container()
                
                container.add_item(TextDisplay(f"## {embed_title}"))
                container.add_item(Separator())
                container.add_item(TextDisplay(embed_description))
                
                thumbnail = config.get("embed_thumbnail", "user_avatar")
                if thumbnail == "user_avatar" and member.avatar:
                    container.add_item(Separator())
                    gallery = MediaGallery()
                    gallery.add_item(media=member.avatar.url)
                    container.add_item(gallery)
                elif thumbnail == "server_icon" and member.guild.icon:
                    container.add_item(Separator())
                    gallery = MediaGallery()
                    gallery.add_item(media=member.guild.icon.url)
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
                message_text = message_text or f"Welcome {member.name} to **{member.guild.name}**!"
                await channel.send(message_text)
        
        except Exception as e:
            print(f"Error sending greet message: {e}")

async def setup(bot):
    await bot.add_cog(GreetEvents(bot))
