import json
import logging
from typing import Any, Optional, Union, List, Dict
import aioredis
import pickle
from datetime import timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis cache and pub/sub manager"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        self.is_connected = False
        self.redis_url = settings.REDIS_URL
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = aioredis.from_url(
                self.redis_url,
                encoding='utf-8',
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            
            # Test connection
            await self.redis.ping()
            self.is_connected = True
            logger.info(f"Connected to Redis at {self.redis_url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.is_connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.pubsub:
            await self.pubsub.close()
        
        if self.redis:
            await self.redis.close()
        
        self.is_connected = False
        logger.info("Disconnected from Redis")
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in Redis with optional TTL"""
        if not self.is_connected:
            logger.warning("Redis not connected, skipping set operation")
            return False
        
        try:
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = str(value)
            
            if ttl:
                await self.redis.setex(key, ttl, serialized_value)
            else:
                await self.redis.set(key, serialized_value)
            
            logger.debug(f"Set Redis key: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting Redis key {key}: {e}")
            return False
    
    async def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """Get a value from Redis"""
        if not self.is_connected:
            logger.warning("Redis not connected, skipping get operation")
            return None
        
        try:
            value = await self.redis.get(key)
            
            if value is None:
                return None
            
            if deserialize:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            else:
                return value
                
        except Exception as e:
            logger.error(f"Error getting Redis key {key}: {e}")
            return None
    
    async def delete(self, *keys: str) -> int:
        """Delete keys from Redis"""
        if not self.is_connected:
            return 0
        
        try:
            deleted = await self.redis.delete(*keys)
            logger.debug(f"Deleted {deleted} Redis keys")
            return deleted
        except Exception as e:
            logger.error(f"Error deleting Redis keys: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self.is_connected:
            return False
        
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.error(f"Error checking Redis key existence: {e}")
            return False
    
    async def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a Redis key"""
        if not self.is_connected:
            return None
        
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing Redis key {key}: {e}")
            return None
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key"""
        if not self.is_connected:
            return False
        
        try:
            return await self.redis.expire(key, seconds)
        except Exception as e:
            logger.error(f"Error setting expiration for Redis key {key}: {e}")
            return False
    
    # Cache-specific methods
    async def cache_vulnerability(self, vuln_id: str, data: Dict[str, Any], ttl: int = None):
        """Cache vulnerability data"""
        if ttl is None:
            ttl = settings.CACHE_TTL_VULNERABILITIES
        
        cache_key = f"vuln:{vuln_id}"
        await self.set(cache_key, data, ttl)
    
    async def get_cached_vulnerability(self, vuln_id: str) -> Optional[Dict[str, Any]]:
        """Get cached vulnerability data"""
        cache_key = f"vuln:{vuln_id}"
        return await self.get(cache_key)
    
    async def cache_api_response(self, endpoint: str, params: str, data: Any, ttl: int = None):
        """Cache API response"""
        if ttl is None:
            ttl = settings.CACHE_TTL_API_RESPONSES
        
        cache_key = f"api:{endpoint}:{hash(params)}"
        await self.set(cache_key, data, ttl)
    
    async def get_cached_api_response(self, endpoint: str, params: str) -> Optional[Any]:
        """Get cached API response"""
        cache_key = f"api:{endpoint}:{hash(params)}"
        return await self.get(cache_key)
    
    async def cache_statistics(self, stats_type: str, data: Dict[str, Any], ttl: int = None):
        """Cache statistics data"""
        if ttl is None:
            ttl = settings.CACHE_TTL_STATISTICS
        
        cache_key = f"stats:{stats_type}"
        await self.set(cache_key, data, ttl)
    
    async def get_cached_statistics(self, stats_type: str) -> Optional[Dict[str, Any]]:
        """Get cached statistics"""
        cache_key = f"stats:{stats_type}"
        return await self.get(cache_key)
    
    # Rate limiting
    async def rate_limit_check(self, key: str, limit: int, window_seconds: int) -> bool:
        """Check if rate limit is exceeded"""
        if not self.is_connected:
            return True  # Allow if Redis is down
        
        try:
            pipe = self.redis.pipeline()
            current_time = int(await self.redis.time()[0])
            
            # Use sliding window rate limiting
            window_start = current_time - window_seconds
            
            # Remove old entries
            await pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            current_requests = await pipe.zcard(key)
            
            if current_requests >= limit:
                return False
            
            # Add current request
            await pipe.zadd(key, {str(current_time): current_time})
            await pipe.expire(key, window_seconds)
            await pipe.execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Allow on error
    
    # Pub/Sub methods
    async def publish(self, channel: str, message: Dict[str, Any]):
        """Publish message to Redis channel"""
        if not self.is_connected:
            return
        
        try:
            serialized_message = json.dumps(message, default=str)
            await self.redis.publish(channel, serialized_message)
            logger.debug(f"Published to channel {channel}")
        except Exception as e:
            logger.error(f"Error publishing to channel {channel}: {e}")
    
    async def subscribe(self, *channels: str):
        """Subscribe to Redis channels"""
        if not self.is_connected:
            return None
        
        try:
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe(*channels)
            logger.info(f"Subscribed to channels: {channels}")
            return self.pubsub
        except Exception as e:
            logger.error(f"Error subscribing to channels: {e}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """Check Redis health"""
        return {
            "connected": self.is_connected,
            "redis_url": self.redis_url.split('@')[-1] if '@' in self.redis_url else self.redis_url  # Hide credentials
        }


# Global Redis manager instance
redis_manager = RedisManager()