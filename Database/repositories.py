"""
This file has been deprecated as the MongoDB implementation has been replaced with SQLite.
Please use the individual repository files in the repositories/ directory instead.
"""

# This file is kept as a placeholder to document the migration from MongoDB to SQLite.
# All functionality has been moved to individual repository files:
# - channel_repository.py
# - dj_role_repository.py
# - prefix_repository.py
# - playlist_repository.py
# - settings_repository.py

from typing import Optional, List, Union, Dict, Any, TypedDict
from datetime import datetime

# These type definitions are kept for reference
class PlaylistTrack(TypedDict):
    name: str
    url: str
    duration: int
    added_at: datetime

class Playlist(TypedDict):
    guild_id: int
    user_id: int
    name: str
    tracks: List[PlaylistTrack]
    created_at: datetime
    updated_at: datetime