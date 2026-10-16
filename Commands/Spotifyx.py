import discord, wavelink
from discord import app_commands
from discord.ext import commands
from spotipy import Spotify
from .Music import same_voice
from spotipy.oauth2 import SpotifyClientCredentials
from typing import Optional
from datetime import datetime
from Views.SpotifyView import SpotifyAuthView, SpotifyPlaylistView
from motor.motor_asyncio import AsyncIOMotorClient
from Config.Config import MONGO_URI, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
import logging
from discord.ui import LayoutView, Container, TextDisplay, Separator, ActionRow, Button, Select, Thumbnail, Section

# Configure logging
logger = logging.getLogger(__name__)

# Constants
SPOTIFY_GREEN = 0x1DB954
SPOTIFY_ICON = "https://cdn.discordapp.com/attachments/1317376605647142945/1317505937837396039/2841a42e18acbd5a5c17900195a0b531.webp"

# MongoDB setup
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["ArgoBotV2"]["SpotifyDB"]

def truncate_string(text: str, length: int = 40) -> str:
    """Truncate string to specified length with ellipsis"""
    return text[:length - 3] + "..." if len(text) > length else text

class Spotifyx(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 3.0, commands.BucketType.user)

        # Verify Spotify credentials on startup
        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            logger.error("Spotify credentials not configured properly")
        else:
            logger.info("Spotify credentials loaded successfully")

    async def cog_check(self, ctx):
        bucket = self.cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(bucket, retry_after, commands.BucketType.user)
        return True

    @commands.hybrid_group(name="spotify")
    async def spotify(self, ctx: commands.Context):
        """Spotify integration commands"""
        if ctx.invoked_subcommand is None:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## Spotify Commands"))
            container.add_item(Separator())
            
            prefix = ctx.prefix
            commands_list = [
                ("spotify auth", "Connect or disconnect your Spotify account"),
                ("spotify profile", "View your Spotify profile"),
                ("spotify playlist", "Browse and play your playlists"),
                ("spotify searchartist", "Search and play artist's top tracks"),
                ("spotify searchalbum", "Search and play albums")
            ]
            
            desc = "\n".join(f"`{prefix}{cmd}` • {desc}" for cmd, desc in commands_list)
            container.add_item(TextDisplay(desc))
            container.add_item(Separator())
            container.add_item(TextDisplay("-# Use the commands above to control your Spotify integration"))
            
            view.add_item(container)
            await ctx.send(view=view)

    @spotify.command(name="auth")
    async def spotify_auth(self, ctx: commands.Context):
        """Connect or disconnect your Spotify account"""
        await ctx.defer()
        try:
            view = SpotifyAuthView(ctx)
            await ctx.send(view=view)
            await view.wait()
        except Exception as e:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ Error: {str(e)}"))
            view.add_item(container)
            await ctx.send(view=view)

    @spotify.command(name="profile")
    async def spotify_profile(self, ctx: commands.Context):
        """View your Spotify profile information"""
        await ctx.defer()
        try:
            data = await db.find_one({"user_id": ctx.author.id})
            if not data:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("## Not Connected"))
                container.add_item(Separator())
                container.add_item(TextDisplay(f"❌ Your Spotify account is not connected\nUse `{ctx.prefix}spotify auth` to connect"))
                view.add_item(container)
                await ctx.send(view=view)
                return

            sp = Spotify(auth_manager=SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            ))

            user_id = data["url"].split("/")[-1]
            user = sp.user(user_id)
            playlists = sp.user_playlists(user['id']) 
            total_tracks = sum(playlist['tracks']['total'] for playlist in playlists['items'])

            view = LayoutView()
            container = Container()
            
            desc = (
                f"**Display Name:** {user['display_name']}\n"
                f"**Followers:** {user.get('followers', {}).get('total', 0):,}\n"
                f"**Public Playlists:** {playlists['total']}\n"
                f"**Total Tracks:** {total_tracks:,}\n"
                f"**Profile:** [Open in Spotify]({data['url']})"
            )
            
            thumb_url = user['images'][0]['url'] if user['images'] else None
            if thumb_url:
                thumb = Thumbnail(thumb_url)
                section = Section(TextDisplay(desc), accessory=thumb)
                container.add_item(section)
            else:
                container.add_item(TextDisplay(f"### {user['display_name']}'s Profile"))
                container.add_item(TextDisplay(desc))
            
            container.add_item(Separator())
            container.add_item(TextDisplay(f"Connected since: {data.get('updated_at', datetime.utcnow())}"))
            
            view.add_item(container)
            await ctx.send(view=view)
        except Exception as e:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ Error fetching profile: {str(e)}"))
            view.add_item(container)
            await ctx.send(view=view)

    @spotify.command(name="playlist")
    async def spotify_playlist(self, ctx: commands.Context):
        """Browse and play your Spotify playlists"""
        await ctx.defer()
        try:
            data = await db.find_one({"user_id": ctx.author.id})

            if not data:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("## Not Connected"))
                container.add_item(Separator())
                container.add_item(TextDisplay(f"❌ Your Spotify account is not connected\nUse `{ctx.prefix}spotify auth` to connect"))
                view.add_item(container)
                await ctx.send(view=view)
                return

            sp = Spotify(auth_manager=SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            ))

            user_id = data["url"].split("/")[-1] 
            user = sp.user(user_id)
            playlists = sp.user_playlists(user['id']) 
          

            if not playlists['items']:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("## No Playlists Found"))
                container.add_item(Separator())
                container.add_item(TextDisplay("You don't have any public playlists."))
                view.add_item(container)
                await ctx.send(view=view)
                return

            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## Select a Playlist"))
            container.add_item(Separator())
            container.add_item(TextDisplay("Choose a playlist from the dropdown menu below"))
            
            row = ActionRow()
            select = Select(
                placeholder="Select a playlist",
                min_values=1,
                max_values=1
            )

            for playlist in playlists['items']:
                select.add_option(
                    label=truncate_string(playlist['name'], 100),
                    value=playlist['id'],
                    description=f"{playlist['tracks']['total']} tracks"
                )
            
            row.add_item(select)
            container.add_item(row)
            view.add_item(container)

            async def select_callback(interaction: discord.Interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message(
                        "❌ Only the command author can use this menu",
                        ephemeral=True
                    )
                    return

                playlist_id = select.values[0]
                playlist = sp.playlist(playlist_id)
                if playlist is None:
                    return 
                tracks = playlist['tracks']['items']

                track_count = len(tracks)
                total_duration = sum(
                    track['track']['duration_ms'] for track in tracks if track['track']
                ) / 1000 / 60  # Convert to minutes

                desc = (
                    f"**Tracks:** {track_count}\n"
                    f"**Duration:** {total_duration:.1f} minutes\n"
                    f"**Created by:** {playlist['owner']['display_name']}\n\n"
                    "Use the buttons below to play or view tracks"
                )
                
                track_names = []
                for track in tracks:
                    if not track['track']:
                        continue
                    track_name = track['track']['name']
                    artists = ", ".join(artist['name'] for artist in track['track']['artists'])
                    track_names.append(f"{track_name} - {artists}")

                playlist_view = SpotifyPlaylistView(
                    ctx=ctx,
                    tracks=playlist['external_urls']['spotify'],
                    track_names=track_names
                )
                
                # We need to recreate the LayoutView for the playlist info
                pv_view = LayoutView()
                pv_container = Container()
                
                thumb_url = playlist['images'][0]['url'] if playlist['images'] else SPOTIFY_ICON
                thumb = Thumbnail(thumb_url)
                section = Section(TextDisplay(desc), accessory=thumb)
                pv_container.add_item(TextDisplay(f"### {playlist['name']}"))
                pv_container.add_item(section)
                
                # Add buttons from SpotifyPlaylistView
                # Since SpotifyPlaylistView is a LayoutView, we can just use it?
                # But we want to show the info AND the buttons.
                # SpotifyPlaylistView has buttons in its __init__.
                # If we add info container now, it will be below buttons.
                # We want info above buttons.
                
                # Let's reconstruct playlist_view manually here or modify SpotifyPlaylistView to accept info.
                # I'll just add the info container to playlist_view and accept it might be below buttons?
                # No, that's bad UX.
                
                # I'll create a new LayoutView, add info container, then add the buttons row from playlist_view?
                # No, playlist_view has the logic.
                
                # I'll just use playlist_view and add the info container FIRST.
                # But playlist_view.__init__ adds buttons.
                
                # I'll modify SpotifyPlaylistView in Views/SpotifyView.py? No, I already edited it.
                
                # I'll just define the buttons here and use a custom view or just use the logic from SpotifyPlaylistView.
                # Actually, I can just clear items from playlist_view and re-add them in correct order?
                # playlist_view.children is a list of items.
                
                # Let's just create a new view here that has the logic.
                # It's easier to just copy the logic since it's short.
                
                # Actually, I'll just use SpotifyPlaylistView and add the info container.
                # LayoutView items are rendered in order.
                # If I want info first, I should have added it first.
                
                # I'll just make a new class `PlaylistInfoView` inheriting from `SpotifyPlaylistView`?
                # No.
                
                # I'll just add the info container to `playlist_view` and then move it to index 0.
                # `playlist_view.children` is the list of items (Containers).
                # `playlist_view.children.insert(0, pv_container)`
                
                playlist_view.children.insert(0, pv_container)

                await interaction.response.edit_message(
                    view=playlist_view
                )

            select.callback = select_callback
            
            await ctx.send(view=view)
            await view.wait()

        except Exception as e:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ Error: {str(e)}"))
            view.add_item(container)
            await ctx.send(view=view)

    @spotify.command(name="searchartist")
    @same_voice()
    async def spotify_searchartist(self, ctx: commands.Context, *, artist_name: str):
        """Search and play music from a Spotify artist"""
        await ctx.defer()
        if not ctx.author.voice:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ You must be in a voice channel"))
            view.add_item(container)
            await ctx.send(view=view)
            return

        player: wavelink.Player = ctx.guild.voice_client
        if not player:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("❌ I'm not connected to a voice channel"))
            view.add_item(container)
            await ctx.send(view=view)
            return

        try:
            sp = Spotify(auth_manager=SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            ))

            results = sp.search(q=artist_name, type="artist", limit=10)
            if not results['artists']['items']:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay(f"❌ No artists found matching '{artist_name}'"))
                view.add_item(container)
                await ctx.send(view=view)
                return

            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"## Search Results for '{artist_name}'"))
            container.add_item(Separator())
            
            artist_name_and_followers = [f"<:melodic_spotify:1307005968525164554> [{artist['name']}](https://discord.gg/melodic) - Total Followers: {artist['followers']['total']}" for artist in results['artists']['items']]
            container.add_item(TextDisplay("\n".join(artist_name_and_followers)))
            
            row = ActionRow()
            select = Select(
                placeholder="Select an artist",
                min_values=1,
                max_values=1
            )

            for artist in results['artists']['items']:
                select.add_option(
                    label=truncate_string(artist['name'], 100),
                    value=artist['id'],
                    description=f"{artist['followers']['total']:,} followers",
                    emoji="<a:Arziyaan_Music:1442615980365709624>"
                )

            row.add_item(select)
            container.add_item(row)
            view.add_item(container)

            async def select_callback(interaction: discord.Interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message(
                        "❌ Only the command author can use this menu",
                        ephemeral=True
                    )
                    return

                artist_id = select.values[0]
                artist = sp.artist(artist_id)
                top_tracks = sp.artist_top_tracks(artist_id)

                tracks = await wavelink.Playable.search(artist['external_urls']['spotify'])

                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("## Added to Queue"))
                container.add_item(Separator())

                if isinstance(tracks, wavelink.Playlist):
                    tracks.track_extras(ctx=ctx)
                    await player.queue.put_wait(tracks)
                    container.add_item(TextDisplay(f"✅ Added {len(tracks)} tracks from **{artist['name']}**"))
                else:
                    track = tracks[0]
                    track.ctx = ctx
                    await player.queue.put_wait(track)
                    container.add_item(TextDisplay(f"✅ Added **{track.title}** from **{artist['name']}**"))
                
                view.add_item(container)

                if not player.current:
                    await player.play(player.queue.get())

                await interaction.response.edit_message(view=view)

            select.callback = select_callback
            await ctx.send(view=view)
            await view.wait()

        except Exception as e:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"❌ Error: {str(e)}"))
            view.add_item(container)
            await ctx.send(view=view)

    @spotify.command(name="searchalbum")
    @same_voice()
    async def spotify_searchalbum(self, ctx: commands.Context, *, album_name: str):
        """Search and play music from a Spotify album"""
        await ctx.defer()
        try:
            if not ctx.author.voice:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("### You are not connected to a voice channel"))
                view.add_item(container)
                await ctx.send(view=view)
                return

            plax: wavelink.Player = ctx.guild.voice_client
            if not plax:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("### I am not connected to a voice channel"))
                view.add_item(container)
                await ctx.send(view=view)
                return

            sp = Spotify(auth_manager=SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            ))

            result = sp.search(q=album_name, type="album", limit=10)
            if not result['albums']['items']:
                view = LayoutView()
                container = Container()
                container.add_item(TextDisplay("### No albums found"))
                view.add_item(container)
                await ctx.send(view=view)
                return

            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("### Select an album from the dropdown menu"))
            
            album_name_and_tracks = [
                f"<:melodic_spotify:1307005968525164554> [{album['name']}](https://discord.gg/melodic) - Total Tracks: {album['total_tracks']}"
                for album in result['albums']['items']
            ]
            container.add_item(TextDisplay("\n".join(album_name_and_tracks)))
            
            row = ActionRow()
            options = [
                discord.SelectOption(
                    label=rx['name'][:100], 
                    value=rx['id'],
                    description=f"Total Tracks: {rx['total_tracks']}", 
                    emoji="<:melodic_spotify:1307005968525164554>"
                ) for rx in result['albums']['items']
            ]

            drop = Select(
                placeholder="Select an album",
                min_values=1,
                max_values=1,
                options=options
            )
            
            row.add_item(drop)
            container.add_item(row)
            view.add_item(container)

            async def callback(interaction: discord.Interaction):
                if interaction.user != ctx.author:
                    return await interaction.response.send_message(
                        "Only the command author can use this", 
                        ephemeral=True
                    )

                try:
                    album_id = drop.values[0]
                    if album_id.startswith("Total Tracks:"):
                        await interaction.response.send_message("Album not found.")
                        return

                    album = sp.album(album_id)
                    top_tracks = sp.album_tracks(album_id)

                    player: wavelink.Player = interaction.guild.voice_client
                    tracks = await wavelink.Playable.search(album['external_urls']['spotify'])

                    if not tracks:
                        await interaction.response.send_message("No tracks found.")
                        return

                    view = LayoutView()
                    container = Container()
                    
                    thumb_url = album['images'][0]['url']
                    thumb = Thumbnail(thumb_url)
                    
                    if isinstance(tracks, wavelink.Playlist):
                        tracks.track_extras(ctx=ctx)
                        await player.queue.put_wait(tracks)
                        section = Section(TextDisplay(f"Added **{len(tracks)}** tracks from **{album['name']}** to the queue"), accessory=thumb)
                        container.add_item(TextDisplay("### Enqueued Album"))
                        container.add_item(section)
                    else:
                        track = tracks[0]
                        track.ctx = ctx
                        await player.queue.put_wait(track)
                        section = Section(TextDisplay(f"Added **{track.title}** to the queue"), accessory=thumb)
                        container.add_item(TextDisplay("### Enqueued Track"))
                        container.add_item(section)
                    
                    view.add_item(container)
                    await interaction.response.send_message(view=view)

                    if not player.current:
                        next_track = player.queue.get()
                        await player.play(next_track)

                    await interaction.message.delete()

                except Exception as e:
                    await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)

            drop.callback = callback
            
            msg = await ctx.send(view=view)
            await view.wait()
            try:
                await msg.delete()
            except:
                pass

        except Exception as e:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay(f"Error: {str(e)}"))
            view.add_item(container)
            await ctx.send(view=view)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Spotifyx(bot))