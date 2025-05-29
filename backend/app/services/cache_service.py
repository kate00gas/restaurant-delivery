

import redis.asyncio as redis
import json
from typing import Optional, Any
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self, redis_url: str):
        try:
            self.redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
            logger.info(f"Redis client initialized for URL: {redis_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            self.redis_client = None # Не падать, если Redis недоступен

    async def connect(self):
        if self.redis_client:
            try:
                await self.redis_client.ping()
                logger.info("Successfully connected to Redis.")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                # self.redis_client = None # Можно отключить, если соединение не удалось

    async def disconnect(self):
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed.")

    async def get(self, key: str) -> Optional[Any]:
        if not self.redis_client:
            return None
        try:
            value = await self.redis_client.get(key)
            if value:
                try:
                    # Пытаемся десериализовать JSON
                    return json.loads(value)
                except json.JSONDecodeError:
                    # Если не JSON, возвращаем как строку
                    return value
            return None
        except Exception as e:
            logger.error(f"Error getting key {key} from Redis: {e}")
            return None

    async def set(self, key: str, value: Any, expire: int = 3600): # expire в секундах (1 час по умолчанию)
        if not self.redis_client:
            return
        try:
            # Сериализуем в JSON, если это dict или list
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value)
            else:
                value_str = str(value) # Преобразуем в строку, если не dict/list

            await self.redis_client.set(key, value_str, ex=expire)
        except Exception as e:
            logger.error(f"Error setting key {key} in Redis: {e}")

    async def delete(self, key: str):
        if not self.redis_client:
            return
        try:
            await self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting key {key} from Redis: {e}")

    async def clear_cache_for_restaurant(self, restaurant_id: str):
        """Очистка кэша, связанного с рестораном (пример)."""
        keys_to_delete = [
            f"restaurant:{restaurant_id}",
            f"restaurant:{restaurant_id}:menu"
        ]
        for key in keys_to_delete:
            await self.delete(key)
        logger.info(f"Cleared cache for restaurant {restaurant_id}")



# Создаем экземпляр сервиса
cache_service = CacheService(settings.REDIS_URL)

# Функции-обертки для использования в Depends (опционально)
# def get_cache_service() -> CacheService:
#    return cache_service