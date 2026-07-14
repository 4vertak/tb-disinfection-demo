"""Redis клиент для JWT blacklist и кэширования."""
import os
import redis
import logging
from functools import lru_cache
from typing import Optional, Set
import time

logger = logging.getLogger(__name__)

# Локальный LRU-кэш для fallback при недоступности Redis
# Хранит последние 1000 отозванных токенов в памяти процесса
_local_blacklist_cache: Set[str] = set()
_local_cache_max_size = 1000
_local_cache_last_sync = 0
_local_cache_sync_interval = 60  # синхронизация каждые 60 секунд


@lru_cache(maxsize=1)
def get_redis_client() -> Optional[redis.Redis]:
    """
    Получить Redis клиент (singleton).
    
    Returns:
        redis.Redis: Redis клиент или None если Redis недоступен
    """
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    try:
        client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True
        )
        # Проверяем соединение
        client.ping()
        logger.info(f"Redis connection established: {redis_url}")
        return client
    except redis.ConnectionError as e:
        logger.error(f"Redis connection failed: {e}. Using local fallback cache.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error connecting to Redis: {e}")
        return None


def is_redis_available() -> bool:
    """Проверить доступность Redis."""
    client = get_redis_client()
    return client is not None


def add_to_blacklist(jti: str, expires_at: Optional[int] = None) -> bool:
    """
    Добавить токен в blacklist.
    
    Args:
        jti: JWT ID токена
        expires_at: Время истечения токена (Unix timestamp)
        
    Returns:
        bool: True если успешно добавлен
    """
    client = get_redis_client()
    
    if client is not None:
        try:
            key = f"blocklist:{jti}"
            if expires_at:
                # Устанавливаем TTL до времени истечения токена
                ttl = expires_at - int(time.time())
                if ttl > 0:
                    client.setex(key, ttl, "revoked")
                else:
                    client.set(key, "revoked")
            else:
                client.set(key, "revoked")
            
            # Также добавляем в локальный кэш для fallback
            _add_to_local_cache(jti)
            return True
        except Exception as e:
            logger.error(f"Failed to add token to Redis blacklist: {e}")
            # Fallback на локальный кэш
            _add_to_local_cache(jti)
            return False
    else:
        # Redis недоступен, используем только локальный кэш
        logger.warning("Redis unavailable, adding token to local cache only")
        _add_to_local_cache(jti)
        return True


def _add_to_local_cache(jti: str) -> None:
    """Добавить токен в локальный LRU-кэш."""
    global _local_blacklist_cache
    
    # Если кэш переполнен, удаляем самые старые записи
    if len(_local_blacklist_cache) >= _local_cache_max_size:
        # Удаляем 10% самых старых записей
        to_remove = list(_local_blacklist_cache)[:int(_local_cache_max_size * 0.1)]
        _local_blacklist_cache -= set(to_remove)
    
    _local_blacklist_cache.add(jti)


def _sync_local_cache_from_redis() -> None:
    """Синхронизировать локальный кэш с Redis (загрузить последние отозванные токены)."""
    global _local_cache_last_sync
    
    current_time = int(time.time())
    if current_time - _local_cache_last_sync < _local_cache_sync_interval:
        return  # Еще рано синхронизировать
    
    client = get_redis_client()
    if client is None:
        return
    
    try:
        # Получаем все ключи из blacklist
        keys = client.keys("blocklist:*")
        jtis = [key.split(":")[1] for key in keys if ":" in key]
        
        # Обновляем локальный кэш
        global _local_blacklist_cache
        _local_blacklist_cache = set(jtis[-_local_cache_max_size:])  # Последние N токенов
        _local_cache_last_sync = current_time
        
        logger.info(f"Synced {len(_local_blacklist_cache)} tokens to local cache")
    except Exception as e:
        logger.error(f"Failed to sync local cache from Redis: {e}")


def check_if_token_revoked(jwt_header: dict, jwt_payload: dict) -> bool:
    """
    Проверить, отозван ли токен через Redis blacklist.
    
    Реализует Fail-Closed стратегию: при недоступности Redis использует локальный кэш.
    Если токен найден в локальном кэше, он считается отозванным даже без Redis.
    
    Args:
        jwt_header: Заголовок JWT токена
        jwt_payload: Payload JWT токена
        
    Returns:
        bool: True если токен отозван, False если действителен
    """
    jti = jwt_payload.get('jti')
    if not jti:
        logger.warning("JWT token missing 'jti' claim")
        return True  # Fail-Closed: отклоняем токен без JTI
    
    client = get_redis_client()
    
    # Попытка 1: Проверка через Redis
    if client is not None:
        try:
            token_in_blacklist = client.get(f"blocklist:{jti}")
            is_revoked = token_in_blacklist is not None
            
            if is_revoked:
                # Также добавляем в локальный кэш для быстрого доступа
                _add_to_local_cache(jti)
            
            return is_revoked
        except Exception as e:
            logger.error(f"Error checking token in Redis: {e}. Falling back to local cache.")
    
    # Попытка 2: Fallback на локальный кэш (Fail-Closed)
    # Синхронизируем локальный кэш с Redis, если возможно
    _sync_local_cache_from_redis()
    
    # Проверяем локальный кэш
    is_revoked = jti in _local_blacklist_cache
    
    if is_revoked:
        logger.warning(f"Token {jti} found in local blacklist cache (Redis unavailable)")
    else:
        # Если Redis недоступен и токена нет в локальном кэше,
        # мы не можем гарантировать безопасность - отклоняем токен (Fail-Closed)
        logger.warning(
            f"Redis unavailable and token {jti} not in local cache. "
            f"Rejecting token for security (Fail-Closed policy)."
        )
        return True  # Fail-Closed: отклоняем токен
    
    return is_revoked


def cleanup_expired_tokens() -> int:
    """
    Очистить истекшие токены из blacklist.
    
    Returns:
        int: Количество удаленных токенов
    """
    client = get_redis_client()
    if client is None:
        return 0
    
    try:
        # Redis автоматически удаляет истекшие ключи через TTL
        # Эта функция может быть использована для принудительной очистки
        keys = client.keys("blocklist:*")
        deleted = 0
        
        for key in keys:
            ttl = client.ttl(key)
            if ttl == -2:  # Ключ истек
                client.delete(key)
                deleted += 1
        
        logger.info(f"Cleaned up {deleted} expired tokens from blacklist")
        return deleted
    except Exception as e:
        logger.error(f"Failed to cleanup expired tokens: {e}")
        return 0