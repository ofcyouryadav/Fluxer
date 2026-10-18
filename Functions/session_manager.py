import aiohttp
import logging
import asyncio
from typing import Optional, Dict
from functools import wraps

logger = logging.getLogger(__name__)

class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, aiohttp.ClientSession] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._initialized = False
        logger.info("\x1b[38;5;197m[Session]\x1b[0m Session manager initialized")

    async def init(self):
        """Initialize the session manager"""
        if self._initialized:
            return
        self._initialized = True
        logger.info("\x1b[38;5;197m[Session]\x1b[0m Session manager started")

    async def cleanup(self):
        """Cleanup all sessions"""
        for name, session in self._sessions.items():
            try:
                if not session.closed:
                    await session.close()
                    logger.info(f"\x1b[38;5;197m[Session]\x1b[0m Closed session: {name}")
            except Exception as e:
                logger.error(f"\x1b[38;5;197m[Session Error]\x1b[0m Error closing session {name}: {e}")
        self._sessions.clear()
        self._locks.clear()
        self._initialized = False

    async def get_session(self, name: str = "default") -> aiohttp.ClientSession:
        """Get or create a session"""
        if not self._initialized:
            await self.init()

        if name not in self._locks:
            self._locks[name] = asyncio.Lock()

        async with self._locks[name]:
            if name not in self._sessions or self._sessions[name].closed:
                self._sessions[name] = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={"User-Agent": "MelodicBot/1.0"}
                )
                logger.debug(f"\x1b[38;5;197m[Session]\x1b[0m Created new session: {name}")
            return self._sessions[name]

    def get_active_sessions(self) -> Dict[str, bool]:
        """Get status of all sessions"""
        return {name: not session.closed for name, session in self._sessions.items()}

# Create global session manager instance
session_manager = SessionManager()

def require_session(func):
    """Decorator to ensure a session is available"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        session = await session_manager.get_session()
        return await func(*args, session=session, **kwargs)
    return wrapper
