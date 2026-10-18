import discord
from discord.ext import commands
from discord.ui import Modal, View, Button, LayoutView, Container, TextDisplay, Separator, ActionRow
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from typing import Optional
from datetime import datetime
import wavelink
from .paginators import DescriptionEmbedPaginator
from .paginator import Paginator
from Config.Config import MONGO_URI, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from motor.motor_asyncio import AsyncIOMotorClient
import logging

# Constants
SPOTIFY_GREEN = 0x1DB954
SPOTIFY_ICON = "https://cdn.discordapp.com/attachments/1317376605647142945/1317505937837396039/2841a42e18acbd5a5c17900195a0b531.webp"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB setup with error handling
try:
    logger.info("Attempting to connect to MongoDB...")
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client["ArgoBotV2"]["SpotifyDB"]
    logger.info("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"MongoDB connection error: {str(e)}")
    db = None

class SpotifyAuthModal(Modal):
    def __init__(self):
        super().__init__(title="Spotify Authentication")
        self.add_item(
            discord.ui.TextInput(
                label="Spotify Profile URL",
                placeholder="https://open.spotify.com/user/youruserid",
                required=True,
                min_length=30,
                max_length=100
            )
        )

    async def on_submit(self, interaction: discord.Interaction):
        url = self.children[0].value.strip()

        try:
            if db is None:
                raise ValueError("Database connection is not available. Please try again later.")

            # Check if Spotify credentials are configured
            if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
                logger.error("Spotify credentials not configured")
                raise ValueError("Spotify API credentials are not properly configured. Please try again later.")

            # Validate URL format
            if not url.startswith("https://open.spotify.com/user/"):
                raise ValueError("Invalid Spotify profile URL. Please provide a valid URL starting with 'https://open.spotify.com/user/'")

            user_id = url.split("/")[-1].split("?")[0]  # Remove any query parameters

            # Initialize Spotify client
            try:
                logger.info("Initializing Spotify client...")
                sp = Spotify(auth_manager=SpotifyClientCredentials(
                    client_id=SPOTIFY_CLIENT_ID,
                    client_secret=SPOTIFY_CLIENT_SECRET
                ))
                logger.info("Spotify client initialized successfully")
            except Exception as e:
                logger.error(f"Spotify client initialization failed: {str(e)}")
                raise ValueError("Failed to initialize Spotify client. Please verify your credentials.")

            # Verify user exists
            try:
                logger.info(f"Looking up Spotify user: {user_id}")
                user = sp.user(user_id)
                logger.info("Successfully found Spotify user")
            except Exception as e:
                logger.error(f"Spotify user lookup failed: {str(e)}")
                raise ValueError("Could not find Spotify user with this profile URL. Please verify the URL and try again.")

            # Store in database
            try:
                logger.info(f"Storing user data for Discord user: {interaction.user.id}")
                await db.update_one(
                    {"user_id": interaction.user.id},
                    {"$set": {
                        "url": url,
                        "display_name": user['display_name'],
                        "updated_at": datetime.utcnow()
                    
                    
                    }},
                    upsert=True
                )
                logger.info("Successfully stored user data")
            except Exception as e:
                logger.error(f"Database update failed: {str(e)}")
                raise ValueError("Failed to save your Spotify profile. Please try again later.")

            # Success response
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## Successfully Connected!"))
            container.add_item(Separator())
            container.add_item(TextDisplay(
                f"✅ Logged in as **{user['display_name']}**\n\n"
                "You can now use Spotify features like:\n"
                "• Playing playlists\n"
                "• Viewing track info\n"
                "• Managing favorites"
            ))
            container.add_item(Separator())
            container.add_item(TextDisplay("-# Use /spotify or /help spotify to see available commands"))
            view.add_item(container)

            await interaction.response.send_message(view=view, ephemeral=True)
            logger.info(f"Successfully connected Spotify for user: {interaction.user.id}")

        except ValueError as e:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ {str(e)}"))
            view.add_item(container)
            await interaction.response.send_message(view=view, ephemeral=True)
        except Exception as e:
            logger.error(f"Unexpected error during Spotify auth: {str(e)}")
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ An unexpected error occurred. Please try again later."))
            view.add_item(container)
            await interaction.response.send_message(view=view, ephemeral=True)

class DisconnectView(LayoutView):
    def __init__(self, ctx, user_data):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.user_data = user_data
        
        container = Container()
        container.add_item(TextDisplay("## Disconnect Spotify"))
        container.add_item(Separator())
        container.add_item(TextDisplay(
            f"You are currently connected as **{user_data.get('display_name', 'Unknown')}**.\n"
            "Are you sure you want to disconnect?"
        ))
        
        row = ActionRow()
        
        confirm_btn = Button(label="Confirm Disconnect", style=discord.ButtonStyle.red)
        async def confirm_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("❌ Only the command author can use this button", ephemeral=True)
            
            try:
                await db.delete_one({"user_id": interaction.user.id})
                
                c = Container()
                c.add_item(TextDisplay("## Successfully Disconnected"))
                c.add_item(Separator())
                c.add_item(TextDisplay("✅ Your Spotify account has been disconnected"))
                
                v = LayoutView()
                v.add_item(c)
                await interaction.response.edit_message(view=v)
            except Exception as e:
                await interaction.response.send_message(f"❌ Error disconnecting: {str(e)}", ephemeral=True)
        
        confirm_btn.callback = confirm_callback
        row.add_item(confirm_btn)
        
        cancel_btn = Button(label="Cancel", style=discord.ButtonStyle.grey)
        async def cancel_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("❌ Only the command author can use this button", ephemeral=True)
            
            c = Container()
            c.add_item(TextDisplay("## Disconnection Cancelled"))
            c.add_item(Separator())
            c.add_item(TextDisplay("Operation cancelled. Your account remains connected."))
            
            v = LayoutView()
            v.add_item(c)
            await interaction.response.edit_message(view=v)
            
        cancel_btn.callback = cancel_callback
        row.add_item(cancel_btn)
        
        container.add_item(row)
        self.add_item(container)


class SpotifyAuthView(LayoutView):
    def __init__(self, ctx):
        super().__init__(timeout=180)
        self.ctx = ctx
        
        container = Container()
        
        container.add_item(TextDisplay("## Spotify Authentication"))
        container.add_item(Separator())
        container.add_item(TextDisplay(
            "Connect your Spotify account to use features like:\n"
            "• Playing your playlists\n"
            "• Viewing track information\n"
            "• Searching artists and albums"
        ))
        container.add_item(Separator())
        
        row = ActionRow()
        
        connect_btn = Button(label="Connect Spotify", style=discord.ButtonStyle.green, emoji="<a:Arziyaan_Music:1442615980365709624>")
        connect_btn.callback = self.connect
        row.add_item(connect_btn)
        
        profile_btn = Button(label="View Profile", style=discord.ButtonStyle.gray, emoji="👤")
        profile_btn.callback = self.view_profile
        row.add_item(profile_btn)
        
        container.add_item(row)
        self.add_item(container)

    async def connect(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Only the command author can use this button", ephemeral=True)

        try:
            # Check if already connected
            user_data = await db.find_one({"user_id": interaction.user.id}) if db is not None else None
            if user_data:
                view = DisconnectView(self.ctx, user_data)
                await interaction.response.send_message(view=view, ephemeral=True)
                return

            # Show connection modal if not connected
            modal = SpotifyAuthModal()
            await interaction.response.send_modal(modal)

        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

    async def view_profile(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Only the command author can use this button", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        try:
            user_data = await db.find_one({"user_id": interaction.user.id}) if db is not None else None
            if not user_data:
                return await interaction.followup.send("❌ You're not connected to Spotify yet.", ephemeral=True)

            sp = Spotify(auth_manager=SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            ))

            user_id = user_data["url"].split("/")[-1]
            user = sp.user(user_id)
            if not user:
                return await interaction.followup.send("Failed to fetch user profile.", ephemeral=True)
            playlists = sp.user_playlists(user['id']) 
            total_tracks = sum(playlist['tracks']['total'] for playlist in playlists['items'])

            view = LayoutView()
            container = Container()
            
            from discord.ui import Thumbnail, Section
            
            desc = (
                f"**Followers:** {user.get('followers', {}).get('total', 0):,}\n"
                f"**Public Playlists:** {len(playlists)}\n"
                f"**Total Tracks:** {total_tracks:,}\n"
                f"**Profile URL:** [Open in Spotify]({user_data['url']})"
            )
            
            thumb_url = user['images'][0]['url'] if user['images'] else None
            if thumb_url:
                thumb = Thumbnail(thumb_url)
                section = Section(TextDisplay(desc), accessory=thumb)
                container.add_item(section)
            else:
                container.add_item(TextDisplay(desc))
                
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Connected since: {user_data.get('updated_at', datetime.utcnow())}"))
            
            view.add_item(container)
            await interaction.followup.send(view=view, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ Error fetching profile: {str(e)}", ephemeral=True)


class SpotifyPlaylistView(LayoutView):
    def __init__(self, ctx, tracks, track_names):
        super().__init__()
        self.ctx = ctx
        self.tracks = tracks
        self.track_names = track_names
        
        container = Container()
        
        row = ActionRow()
        
        play_btn = Button(label="Play All", style=discord.ButtonStyle.green, emoji="▶️")
        play_btn.callback = self.play_tracks
        row.add_item(play_btn)
        
        view_btn = Button(label="View Tracks", style=discord.ButtonStyle.gray, emoji="📋")
        view_btn.callback = self.view_tracks
        row.add_item(view_btn)
        
        container.add_item(row)
        self.add_item(container)

    async def play_tracks(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Only the command author can use this button", ephemeral=True)

        if not interaction.user.voice:
            return await interaction.response.send_message("❌ You must be in a voice channel to play music", ephemeral=True)

        player: wavelink.Player = interaction.guild.voice_client
        if not player:
            return await interaction.response.send_message("❌ I'm not connected to a voice channel", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        try:
            tracks = await wavelink.Playable.search(self.tracks)
            
            view = LayoutView()
            container = Container()
            
            if isinstance(tracks, wavelink.Playlist):
                tracks.track_extras(ctx=self.ctx)
                await player.queue.put_wait(tracks)
                container.add_item(TextDisplay(f"✅ Added {len(tracks)} tracks to the queue"))
            else:
                track = tracks[0]
                track.ctx = self.ctx
                await player.queue.put_wait(track)
                container.add_item(TextDisplay("✅ Added track to the queue"))
            
            view.add_item(container)

            if not player.current:
                await player.play(player.queue.get())

            await interaction.followup.send(view=view, ephemeral=True)
            try:
                await interaction.message.delete()
            except:
                pass

        except Exception as e:
            await interaction.followup.send(f"❌ Error playing tracks: {str(e)}", ephemeral=True)

    async def view_tracks(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Only the command author can use this button", ephemeral=True)

        entries = [f"`{i+1}.` {name}" for i, name in enumerate(self.track_names)]

        paginator = Paginator(
            ctx=self.ctx,
            source=DescriptionEmbedPaginator(
                entries=entries,
                title="Playlist Tracks",
                author=self.ctx.author.name,
                author_icon=self.ctx.author.display_avatar.url if self.ctx.author.display_avatar else None,
                color=SPOTIFY_GREEN,
                per_page=10
            )
        )

        await paginator.paginate()
        try:
            await interaction.message.delete()
        except:
            pass