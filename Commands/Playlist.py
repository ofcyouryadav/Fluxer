import discord
from discord.ext import commands
from discord.ext.commands import Cog
import wavelink
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from .Music import same_voice
from datetime import datetime
from Views.paginator import Paginator
from Views.paginators import DescriptionEmbedPaginator
from typing import List 
from discord import app_commands
# MongoDB Configuration
MONGO_URI = "mongodb+srv://fluxer8585:fluxer8585@fluxer.3izoeeq.mongodb.net/?appName=Fluxer"
mongo_client = AsyncIOMotorClient(MONGO_URI)
dbx = mongo_client["ArgoBotV2"]
playlist_db = dbx["PlaylistDB"]
shared_playlist_db = dbx["SharedPlaylistDB"]

async def embedx(text):
    from discord.ui import LayoutView, Container, TextDisplay, Separator
    color = 0x2f3136
    view = LayoutView()
    container = Container()
    container.add_item(TextDisplay(f"## {text}"))
    view.add_item(container)
    return view

class PlaylistCommands(Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.color = 0x2f3136
        self.cooldown = commands.CooldownMapping.from_cooldown(1, 3.0, commands.BucketType.user)

    async def cog_check(self, ctx):
        bucket = self.cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(bucket, retry_after, commands.BucketType.user)
        return True

    async def playlist_autocomplete(self, interaction: discord.Interaction, name) -> list[app_commands.Choice[str]]:
        # Optimized with caching
        cache_key = f"playlists:{interaction.user.id}"
        playlists = await cache_manager.get('playlists', cache_key)
        if playlists is None:
            playlists = await playlist_db.find({"user_id": interaction.user.id}).to_list(length=None)
            await cache_manager.set('playlists', cache_key, playlists, ttl=300)  # Cache for 5 minutes
        return [app_commands.Choice(name=playlist["name"], value=playlist["name"]) for playlist in playlists]

    @commands.hybrid_group(name="playlist", description="Playlist management commands")
    async def playlist(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            from discord.ui import LayoutView, Container, TextDisplay, Separator, Thumbnail, Section
            view = LayoutView()
            container = Container()
            
            container.add_item(TextDisplay("## Playlist Commands"))
            container.add_item(Separator())
            
            prefix = ctx.prefix
            description = (
                "**Create and manage your playlists effortlessly with the following commands:**\n\n"
                f"**1. Playlist Creation & Deletion**\n"
                f"• `{prefix}playlist create` - Create a new playlist.\n"
                f"• `{prefix}playlist delete` - Delete an existing playlist.\n\n"
                f"**2. Track Management**\n"
                f"• `{prefix}playlist add` - Add the current track to a playlist.\n"
                f"• `{prefix}playlist remove` - Remove a track from a playlist.\n\n"
                f"**3. Playlist Viewing & Loading**\n"
                f"• `{prefix}playlist list` - Display all your playlists.\n"
                f"• `{prefix}playlist view` - View tracks in a specific playlist.\n"
                f"• `{prefix}playlist load` - Load and play a playlist.\n"
                f"• `{prefix}playlist save` - Save a playlist to your account.\n"
              #  f"**4. Saving & Sharing**\n"
            #    f"• `{prefix}playlist save` - Save the current queue as a playlist.\n"#
                #f"• `{prefix}share` - Share a playlist with another user.\n"
            #    f"• `{prefix}shared` - View playlists shared with you.\n"
            #    f"• `{prefix}unshare` - Revoke sharing access for a playlist."
            )
            
            thumb = Thumbnail(ctx.author.display_avatar.url if ctx.author.display_avatar else ctx.author.default_avatar.url)
            section = Section(TextDisplay(description), accessory=thumb)
            container.add_item(section)
            
            view.add_item(container)
            await ctx.send(view=view)

    # Add owner check helper method
    async def _check_playlist_access(self, ctx: commands.Context, playlist_name: str, check_owner: bool = False):
        """Check if user has access to a playlist with caching"""
        # Check owned playlists first with caching
        cache_key = f"playlist:{ctx.author.id}:{playlist_name}"
        playlist = await cache_manager.get('playlist', cache_key)
        if playlist is None:
            playlist = await playlist_db.find_one({"user_id": ctx.author.id, "name": playlist_name})
            await cache_manager.set('playlist', cache_key, playlist or {}, ttl=300)  # Cache for 5 minutes

        if playlist:
            return playlist, True  # Return playlist and is_owner flag

        # If not found and we need owner access, return None
        if check_owner:
            return None, False

        # Check shared playlists with caching
        shared_cache_key = f"shared_playlist:{ctx.author.id}:{playlist_name}"
        shared = await cache_manager.get('shared_playlist', shared_cache_key)
        if shared is None:
            shared = await shared_playlist_db.find_one({
                "shared_with": ctx.author.id,
                "playlist_name": playlist_name
            })
            await cache_manager.set('shared_playlist', shared_cache_key, shared or {}, ttl=300)

        if shared:
            playlist_cache_key = f"playlist_id:{shared['playlist_id']}"
            playlist = await cache_manager.get('playlist', playlist_cache_key)
            if playlist is None:
                playlist = await playlist_db.find_one({"_id": shared["playlist_id"]})
                await cache_manager.set('playlist', playlist_cache_key, playlist or {}, ttl=300)
            return playlist, False

        return None, False

    @playlist.command(name="add", description="Add current track to a playlist")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @same_voice()
    async def playlist_add(self, ctx: commands.Context, name: str):
        """Add the current track to a playlist"""
        try:
            vc: wavelink.Player = ctx.voice_client
            if not vc or not vc.current:
                return await ctx.send(embed=await embedx("No track is currently playing."))

            track = vc.current
            track_data = {
                "title": track.title,
                "uri": track.uri,
                "author": track.author,
                "length": track.length
            }

            # Update playlist with new track
            result = await playlist_db.update_one(
                {"user_id": ctx.author.id, "name": name},
                {
                    "$push": {"tracks": track_data},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

            if result.modified_count == 0:
                return await ctx.send(embed=await embedx(f"Playlist '{name}' not found."))

            await ctx.send(embed=await embedx(f"Added '{track.title}' to playlist: {name}"))

        except Exception as e:
            await ctx.send(embed=await embedx(f"An error occurred: {str(e)}"))

    @playlist.command(name="remove", description="Remove a track from a playlist")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def playlist_remove(self, ctx: commands.Context, name: str, index: int):
        """Remove a track from a playlist by its index"""
        try:
            # Get playlist
            playlist = await playlist_db.find_one({"user_id": ctx.author.id, "name": name})
            if not playlist:
                return await ctx.send(embed=await embedx(f"Playlist '{name}' not found."))

            tracks = playlist.get("tracks", [])
            if not 1 <= index <= len(tracks):
                return await ctx.send(embed=await embedx(f"Invalid track index. Please use a number between 1 and {len(tracks)}."))

            # Remove track and update playlist
            removed_track = tracks.pop(index - 1)
            await playlist_db.update_one(
                {"user_id": ctx.author.id, "name": name},
                {
                    "$set": {
                        "tracks": tracks,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            await ctx.send(embed=await embedx(f"Removed '{removed_track['title']}' from playlist: {name}"))

        except Exception as e:
            await ctx.send(embed=await embedx(f"An error occurred: {str(e)}"))

    @playlist.command(name="view", description="View tracks in a playlist")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def playlist_view(self, ctx: commands.Context, name: str):
        """View all tracks in a playlist with caching"""
        try:
            # Use cached playlist access
            playlist, is_owner = await self._check_playlist_access(ctx, name)
            if not playlist:
                return await ctx.send(embed=await embedx(f"Playlist '{name}' not found."))

            tracks = playlist.get("tracks", [])
            if not tracks:
                return await ctx.send(embed=await embedx("This playlist is empty."))

            entries = []
            for i, track in enumerate(tracks, 1):
                duration = f"{track['length'] // 60}:{track['length'] % 60:02d}"
                entries.append(f"`{i}.` [{track['title']}]({track['uri']}) - `{duration}`")

            paginator = Paginator(
                ctx=ctx,
                source=DescriptionEmbedPaginator(
                    entries=entries,
                    title=f"Playlist: {name}",
                    per_page=10
                )
            )
            await paginator.paginate()

        except Exception as e:
            await ctx.send(embed=await embedx(f"An error occurred: {str(e)}"))

    @playlist.command(name="create", description="Create a new playlist")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def playlist_create(self, ctx: commands.Context, name: str):
        """Create a new playlist"""
        try:
            # Check if playlist already exists
            existing = await playlist_db.find_one({"user_id": ctx.author.id, "name": name})
            if existing:
                return await ctx.send(embed=await embedx("A playlist with that name already exists."))

            playlist_data = {
                "user_id": ctx.author.id,
                "name": name,
                "tracks": [],
                "created_at": datetime.utcnow()
            }
            await playlist_db.insert_one(playlist_data)
            await ctx.send(embed=await embedx(f"Created playlist: {name}"))

        except Exception as e:
            await ctx.send(embed=await embedx(f"An error occurred: {str(e)}"))

    @playlist.command(name="save", description="Save current queue as a playlist")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @same_voice()
    async def playlist_save(self, ctx: commands.Context, name: str):
        """Save the current queue as a playlist"""
        try:
            vc: wavelink.Player = ctx.voice_client
            if not vc or not vc.queue:
                return await ctx.send(embed=await embedx("No tracks in queue to save."))

            # Get all tracks from queue
            tracks = []
            if vc.current:
                tracks.append({
                    "title": vc.current.title,
                    "uri": vc.current.uri,
                    "author": vc.current.author,
                    "length": vc.current.length
                })

            for track in vc.queue:
                tracks.append({
                    "title": track.title,
                    "uri": track.uri,
                    "author": track.author,
                    "length": track.length
                })

            # Update or create playlist
            await playlist_db.update_one(
                {"user_id": ctx.author.id, "name": name},
                {"$set": {
                    "tracks": tracks,
                    "updated_at": datetime.utcnow()
                }},
                upsert=True
            )

            await ctx.send(embed=await embedx(f"Saved {len(tracks)} tracks to playlist: {name}"))

        except Exception as e:
            await ctx.send(embed=await embedx(f"An error occurred: {str(e)}"))

    @playlist.command(name="addqueue", description="Add current queue to a playlist")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @same_voice()
    async def playlist_addqueue(self, ctx: commands.Context, name: str):
        """Add all tracks from current queue to a playlist"""
        try:
            vc: wavelink.Player = ctx.voice_client
            if not vc or not vc.queue:
                return await ctx.send(embed=await embedx("No tracks in queue to add."))

            # Get all tracks from queue
            tracks = []
            if vc.current:
                tracks.append({
                    "title": vc.current.title,
                    "uri": vc.current.uri,
                    "author": vc.current.author,
                    "length": vc.current.length
                })

            for track in vc.queue:
                tracks.append({
                    "title": track.title,
                    "uri": track.uri,
                    "author": track.author,
                    "length": track.length
                })

            # Update playlist with new tracks
            result = await playlist_db.update_one(
                {"user_id": ctx.author.id, "name": name},
                {
                    "$push": {"tracks": {"$each": tracks}},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

            if result.modified_count == 0:
                return await ctx.send(embed=await embedx(f"Playlist '{name}' not found."))

            await ctx.send(embed=await embedx(f"Added {len(tracks)} tracks to playlist: {name}"))

        except Exception as e:
            await ctx.send(embed=await embedx(f"An error occurred: {str(e)}"))

    @playlist.command(name="addcurrent", description="Add current track to a playlist")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @same_voice()
    async def playlist_addcurrent(self, ctx: commands.Context, name: str):
        """Add currently playing track to a playlist"""
        try:
            vc: wavelink.Player = ctx.voice_client
            if not vc or not vc.current:
                return await ctx.send(embed=await embedx("No track is currently playing."))

            track = vc.current
            track_data = {
                "title": track.title,
                "uri": track.uri,
                "author": track.author,
                "length": track.length
            }

            # Update playlist with new track
            result = await playlist_db.update_one(
                {"user_id": ctx.author.id, "name": name},
                {
                    "$push": {"tracks": track_data},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )

            if result.modified_count == 0:
                return await ctx.send(embed=await embedx(f"Playlist '{name}' not found."))

            await ctx.send(embed=await embedx(f"Added '{track.title}' to playlist: {name}"))

        except Exception as e:
            await ctx.send(embed=await embedx(f"An error occurred: {str(e)}"))

    @playlist.command(name="removeduplicates", description="Remove duplicate tracks from a playlist")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def playlist_removeduplicates(self, ctx: commands.Context, name: str):
        """Remove duplicate tracks from a playlist"""
        try:
            # Get playlist
            playlist = await playlist_db.find_one({"user_id": ctx.author.id, "name": name})
            if not playlist:
                return await ctx.send(embed=await embedx(f"Playlist '{name}' not found."))

            tracks = playlist.get("tracks", [])
            if not tracks:
                return await ctx.send(embed=await embedx("This playlist is empty."))

            # Remove duplicates while preserving order
            seen = set()
            unique_tracks = []
            duplicates = 0

            for track in tracks:
                track_key = (track["title"], track["uri"])
                if track_key not in seen:
                    seen.add(track_key)
                    unique_tracks.append(track)
                else:
                    duplicates += 1

            if duplicates == 0:
                return await ctx.send(embed=await embedx("No duplicate tracks found in the playlist."))

            # Update playlist with unique tracks
            await playlist_db.update_one(
                {"user_id": ctx.author.id, "name": name},
                {
                    "$set": {
                        "tracks": unique_tracks,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            await ctx.send(embed=await embedx(f"Removed {duplicates} duplicate tracks from playlist: {name}"))

        except Exception as e:
            await ctx.send(embed=await embedx(f"An error occurred: {str(e)}"))

    @playlist.command(name="removetrack", description="Remove a specific track from a playlist by URI")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def playlist_removetrack(self, ctx: commands.Context, name: str, *, track_uri: str):
        """Remove a specific track from a playlist by its URI"""
        try:
            # Check if user owns the playlist
            playlist, is_owner = await self._check_playlist_access(ctx, name, check_owner=True)
            if not playlist:
                return await ctx.send(embed=await embedx("Playlist not found or you don't have permission to modify it."))

            tracks = playlist.get("tracks", [])
            if not tracks:
                return await ctx.send(embed=await embedx("This playlist is empty."))

            # Find and remove track by URI
            original_length = len(tracks)
            tracks = [track for track in tracks if track["uri"] != track_uri]

            if len(tracks) == original_length:
                return await ctx.send(embed=await embedx("Track not found in the playlist."))

            # Update playlist without the removed track
            await playlist_db.update_one(
                {"user_id": ctx.author.id, "name": name},
                {
                    "$set": {
                        "tracks": tracks,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            await ctx.send(embed=await embedx(f"Removed track from playlist: {name}"))

        except Exception as e:
            await ctx.send(embed=await embedx(f"An error occurred: {str(e)}"))

    @playlist.command(name="rename", description="Rename a playlist")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def playlist_rename(self, ctx: commands.Context, old_name: str, new_name: str):
        """Rename an existing playlist"""
        try:
            # Check if old playlist exists
            old_playlist = await playlist_db.find_one({"user_id": ctx.author.id, "name": old_name})
            if not old_playlist:
                return await ctx.send(embed=await embedx(f"Playlist '{old_name}' not found."))

            # Check if new name already exists
            existing = await playlist_db.find_one({"user_id": ctx.author.id, "name": new_name})
            if existing:
                return await ctx.send(embed=await embedx(f"A playlist named '{new_name}' already exists."))

            # Update playlist name
            await playlist_db.update_one(
                {"user_id": ctx.author.id, "name": old_name},
                {
                    "$set": {
                        "name": new_name,
                        "updated_at": datetime.utcnow()
                    }
                }
            )

            # Update any shared playlist references
            await shared_playlist_db.update_many(
                {"playlist_id": str(old_playlist["_id"])},
                {"$set": {"playlist_name": new_name}}
            )

            await ctx.send(embed=await embedx(f"Renamed playlist from '{old_name}' to '{new_name}'"))

        except Exception as e:
            await ctx.send(embed=await embedx(f"An error occurred: {str(e)}"))

    @playlist.command(name="load", description="Load and play a playlist")
    @app_commands.describe(name="The name of the playlist to load")
    @app_commands.autocomplete(name=playlist_autocomplete)
    @commands.cooldown(1, 5, commands.BucketType.user)
    @same_voice()
    async def playlist_load(self, ctx: commands.Context, name: str):
        """Load and play a playlist with optimized loading"""
        try:
            vc: wavelink.Player = ctx.voice_client
            if not vc:
                return await ctx.send(embed=await embedx("Bot is not connected to a voice channel."))

            # Check playlist access (cached)
            playlist, is_owner = await self._check_playlist_access(ctx, name)
            if not playlist:
                return await ctx.send(embed=await embedx("Playlist not found or you don't have access to it."))

            tracks = playlist.get("tracks", [])
            if not tracks:
                return await ctx.send(embed=await embedx("Playlist is empty."))

            # Batch load tracks for better performance
            loaded_tracks = 0
            search_tasks = []

            # Create search tasks for all tracks
            for track_data in tracks:
                search_tasks.append(wavelink.Playable.search(track_data["uri"]))

            # Execute searches concurrently with semaphore to avoid overwhelming
            semaphore = asyncio.Semaphore(5)  # Limit concurrent searches
            async def search_with_limit(uri):
                async with semaphore:
                    try:
                        searched = await wavelink.Playable.search(uri)
                        return searched[0] if searched else None
                    except:
                        return None

            # Process in batches
            batch_size = 10
            for i in range(0, len(tracks), batch_size):
                batch_uris = [tracks[j]["uri"] for j in range(i, min(i + batch_size, len(tracks)))]
                results = await asyncio.gather(*[search_with_limit(uri) for uri in batch_uris], return_exceptions=True)

                for result in results:
                    if isinstance(result, wavelink.Playable):
                        await vc.queue.put_wait(result)
                        loaded_tracks += 1

            if loaded_tracks > 0:
                if not vc.current:
                    await vc.play(vc.queue.get())
                    vc.ctx = ctx
                await ctx.send(embed=await embedx(f"Loaded {loaded_tracks} tracks from {'your' if is_owner else 'shared'} playlist: {name}"))
            else:
                await ctx.send(embed=await embedx("Failed to load any tracks from the playlist."))

        except Exception as e:
            await ctx.send(embed=await embedx(f"An error occurred: {str(e)}"))

    @playlist.command(name="list", description="List all your playlists")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def playlist_list(self, ctx: commands.Context):
        """List all your playlists with caching"""
        try:
            # Use cached playlists from autocomplete
            cache_key = f"playlists:{ctx.author.id}"
            playlists = await cache_manager.get('playlists', cache_key)
            if playlists is None:
                playlists = await playlist_db.find({"user_id": ctx.author.id}).to_list(length=None)
                await cache_manager.set('playlists', cache_key, playlists, ttl=300)

            if not playlists:
                return await ctx.send(embed=await embedx("You don't have any playlists."))

            entries = []
            for i, playlist in enumerate(playlists, 1):
                track_count = len(playlist.get("tracks", []))
                created_at = playlist.get("created_at", datetime.utcnow()).strftime("%Y-%m-%d")
                entries.append(f"`{i}.` **{playlist['name']}** - {track_count} tracks (Created: {created_at})")

            paginator = Paginator(
                ctx=ctx,
                source=DescriptionEmbedPaginator(
                    entries=entries,
                    title="Your Playlists",
                    per_page=10
                )
            )
            await paginator.paginate()

        except Exception as e:
            await ctx.send(embed=await embedx(f"An error occurred: {str(e)}"))

    @playlist.command(name="delete", description="Delete a playlist")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def playlist_delete(self, ctx: commands.Context, name: str):
        """Delete a playlist"""
        try:
            result = await playlist_db.delete_one({"user_id": ctx.author.id, "name": name})
            if result.deleted_count > 0:
                await ctx.send(embed=await embedx(f"Deleted playlist: {name}"))
            else:
                await ctx.send(embed=await embedx("Playlist not found."))

        except Exception as e:
            await ctx.send(embed=await embedx(f"An error occurred: {str(e)}"))


    
        
                

 
            
           
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PlaylistCommands(bot))