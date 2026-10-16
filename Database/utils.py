import logging
from typing import Dict, List, Any, Optional
import asyncio
from .connection import DatabaseConnection
import time
from cachetools import TTLCache

logger = logging.getLogger(__name__)

class CacheManager:
    """Centralized cache management with TTLCache"""

    def __init__(self):
        self._caches = {
            'prefix': TTLCache(maxsize=1000, ttl=3600),  # 1 hour TTL
            'dj_role': TTLCache(maxsize=1000, ttl=600),  # 10 minutes TTL
            'guild_config': TTLCache(maxsize=500, ttl=1800),  # 30 minutes TTL
            'playlists': TTLCache(maxsize=200, ttl=300),  # 5 minutes TTL
            'spotify': TTLCache(maxsize=200, ttl=1800),  # 30 minutes TTL
           
        }
        self._locks = {cache_name: asyncio.Lock() for cache_name in self._caches}
        self.last_cleanup = time.time()
        self.cleanup_interval = 3600  # Cleanup every hour

    async def get(self, cache_name: str, key: str) -> Optional[Any]:
        """Get value from cache with proper locking"""
        if cache_name not in self._caches:
            logger.debug(f"Cache {cache_name} not found")
            return None

        async with self._locks[cache_name]:
            try:
                return self._caches[cache_name].get(key)
            except Exception as e:
                logger.error(f"Error getting value from cache {cache_name}: {e}")
                return None

    async def set(self, cache_name: str, key: str, value: Any, **kwargs) -> bool:
        """Set value in cache with proper locking"""
        if cache_name not in self._caches:
            logger.debug(f"Cache {cache_name} not found")
            return False

        async with self._locks[cache_name]:
            try:
                self._caches[cache_name][key] = value
                return True
            except Exception as e:
                logger.error(f"Error setting value in cache {cache_name}: {e}")
                return False

    async def delete(self, cache_name: str, key: str) -> bool:
        """Delete value from cache with proper locking"""
        if cache_name not in self._caches:
            logger.debug(f"Cache {cache_name} not found")
            return False

        async with self._locks[cache_name]:
            try:
                self._caches[cache_name].pop(key, None)
                return True
            except Exception as e:
                logger.error(f"Error deleting value from cache {cache_name}: {e}")
                return False

    async def cleanup(self) -> None:
        """Cleanup expired cache entries"""
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            for cache_name, cache in self._caches.items():
                async with self._locks[cache_name]:
                    try:
                        cache.expire()
                        logger.debug(f"Cleaned up expired entries in {cache_name} cache")
                    except Exception as e:
                        logger.error(f"Error cleaning up cache {cache_name}: {e}")
            self.last_cleanup = current_time
            logger.info("Cache cleanup completed")

# Global cache manager instance
cache_manager = CacheManager()

class DatabaseMetrics:
    """Database metrics tracking with performance monitoring"""

    def __init__(self):
        self.operation_counts = {}
        self.error_counts = {}
        self.average_response_times = {}
        self.error_types = {}
        self.slow_queries = []
        self.last_cleanup = time.time()
        self.cleanup_interval = 3600  # Cleanup old metrics every hour

    async def record_operation(self, operation_name: str, response_time: float, success: bool) -> None:
        """Record metrics with enhanced error tracking and cleanup"""
        try:
            current_time = time.time()
            if current_time - self.last_cleanup > self.cleanup_interval:
                await self._cleanup_old_metrics()
                self.last_cleanup = current_time

            if operation_name not in self.operation_counts:
                self.operation_counts[operation_name] = 0
                self.error_counts[operation_name] = 0
                self.average_response_times[operation_name] = 0
                self.error_types[operation_name] = {}

            self.operation_counts[operation_name] += 1
            if not success:
                self.error_counts[operation_name] += 1

            # Update average response time with weighted moving average
            current_avg = self.average_response_times[operation_name]
            weight = 0.7  # Give more weight to recent operations
            self.average_response_times[operation_name] = (
                current_avg * (1 - weight) + response_time * weight
            )

            # Track slow queries (>100ms)
            if response_time > 0.1:
                self.slow_queries.append({
                    'operation': operation_name,
                    'response_time': response_time,
                    'timestamp': current_time
                })
        except Exception as e:
            logger.error(f"Error recording operation metrics: {e}")

    async def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics data"""
        try:
            current_time = time.time()
            # Remove slow queries older than 24 hours
            self.slow_queries = [
                query for query in self.slow_queries
                if current_time - query['timestamp'] < 86400
            ]
            logger.info("Metrics cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during metrics cleanup: {e}")

    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get current metrics with enhanced statistics"""
        try:
            metrics = {}
            for operation in self.operation_counts:
                total_calls = self.operation_counts[operation]
                error_count = self.error_counts[operation]
                success_rate = ((total_calls - error_count) / total_calls * 100
                                if total_calls > 0 else 0)

                metrics[operation] = {
                    'total_calls': total_calls,
                    'error_count': error_count,
                    'average_response_time': round(
                        self.average_response_times[operation], 3),
                    'success_rate': round(success_rate, 2),
                    'error_types': self.error_types.get(operation, {}),
                }
            return metrics
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}

# Global instance for metrics
db_metrics = DatabaseMetrics()

async def initialize_database() -> bool:
    """Initialize SQLite database with proper tables and indexes"""
    try:
        db = await DatabaseConnection.get_instance()
        if not db:
            logger.error("Failed to get database instance")
            return False

        # Initialize tables using the schema definitions
        from .schemas import initialize_database as init_schema
        success = await init_schema(db)

        if success:
            logger.info("Database initialization completed successfully")
            return True
        else:
            logger.error("Database initialization failed")
            return False

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

async def check_database_health() -> Dict[str, bool]:
    """Check the health of database connection"""
    try:
        db = await DatabaseConnection.get_instance()
        health_status = {'connection': False}

        # Check if we can execute a simple query
        try:
            async with db.transaction():
                await db.execute("SELECT 1")
                health_status['connection'] = True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            health_status['connection'] = False

        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {'connection': False}