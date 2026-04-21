import json
import functools
import hashlib
from typing import Any, Callable, Optional
from redis.asyncio import Redis, ConnectionPool
from app.core.config import settings

# ── Пул соединений (один на весь процесс) ─────────────────────
_pool: Optional[ConnectionPool] = None

def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=20,
            decode_responses=True,
        )
    return _pool

def get_redis() -> Redis:
    return Redis(connection_pool=get_pool())


# ── Низкоуровневые хелперы ─────────────────────────────────────
async def cache_get(key: str) -> Any | None:
    async with get_redis() as r:
        raw = await r.get(key)
        return json.loads(raw) if raw else None

async def cache_set(key: str, value: Any, ttl: int = settings.CACHE_TTL) -> None:
    async with get_redis() as r:
        await r.set(key, json.dumps(value, default=str), ex=ttl)

async def cache_delete(*keys: str) -> None:
    async with get_redis() as r:
        if keys:
            await r.delete(*keys)

async def cache_delete_pattern(pattern: str) -> None:
    """Удаляет все ключи по паттерну (через SCAN, не KEYS)."""
    async with get_redis() as r:
        cursor = 0
        while True:
            cursor, keys = await r.scan(cursor, match=pattern, count=100)
            if keys:
                await r.delete(*keys)
            if cursor == 0:
                break


# ── Namespace хелперы ──────────────────────────────────────────
def project_key(project_id: int, suffix: str = "") -> str:
    return f"project:{project_id}{(':' + suffix) if suffix else ''}"

def rpi_list_key(project_id: int, params_hash: str) -> str:
    return f"project:{project_id}:rpi:list:{params_hash}"

def rpi_stats_key(project_id: int) -> str:
    return f"project:{project_id}:rpi:stats"

def sources_key(project_id: int) -> str:
    return f"project:{project_id}:sources"

def mapping_tables_key(project_id: int) -> str:
    return f"project:{project_id}:mapping_tables"

def hash_params(**kwargs) -> str:
    """Детерминированный хэш query-параметров для ключа кэша."""
    raw = json.dumps(kwargs, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()[:12]


# ── Декоратор для кэширования сервисных функций ────────────────
def cached(key_fn: Callable[..., str], ttl: int = settings.CACHE_TTL):
    """
    Использование:
        @cached(key_fn=lambda project_id, **_: rpi_stats_key(project_id))
        async def get_stats(db, project_id): ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            key = key_fn(*args, **kwargs)
            hit = await cache_get(key)
            if hit is not None:
                return hit
            result = await func(*args, **kwargs)
            # Pydantic модели → dict перед сериализацией
            serializable = result.model_dump() if hasattr(result, "model_dump") else result
            await cache_set(key, serializable, ttl)
            return result
        return wrapper
    return decorator