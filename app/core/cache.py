import functools
import hashlib
import json
from collections.abc import Callable
from typing import Any

from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings

# ── Пул соединений и клиент (один на весь процесс) ───────────────────────────
_pool: ConnectionPool | None = None
_redis: Redis | None = None


PROJECTS_KPI_KEY = "projects:kpi"
PROJECTS_RECENT_KEY = "projects:recent"
PROJECTS_LIST_KEY = "projects:list"


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
    global _redis
    if _redis is None:
        _redis = Redis(connection_pool=get_pool())
    return _redis


# ── Низкоуровневые хелперы ────────────────────────────────────────────────────

async def cache_get(key: str) -> Any | None:
    raw = await get_redis().get(key)
    return json.loads(raw) if raw else None


async def cache_set(key: str, value: Any, ttl: int = settings.CACHE_TTL) -> None:
    await get_redis().set(key, json.dumps(value, default=str), ex=ttl)


async def cache_delete(*keys: str) -> None:
    if keys:
        await get_redis().delete(*keys)


async def cache_delete_pattern(pattern: str) -> None:
    """Удаляет все ключи по паттерну (через SCAN, не KEYS)."""
    r = get_redis()
    cursor = 0
    while True:
        cursor, keys = await r.scan(cursor, match=pattern, count=100)
        if keys:
            await r.delete(*keys)
        if cursor == 0:
            break


# ── Namespace хелперы ─────────────────────────────────────────────────────────

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
    """Детерминированный хэш query-параметров для ключа кэша.
    MD5 используется только как быстрая хэш-функция, не для криптографии."""
    raw = json.dumps(kwargs, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()[:12]


# ── Декоратор для кэширования сервисных функций ───────────────────────────────

def cached(
    key_fn: Callable[..., str],
    ttl: int = settings.CACHE_TTL,
    schema=None,
):
    """
    Обёртка для кэширования результатов сервисных функций в Redis.

    Параметры:
        key_fn: функция, принимающая те же args/kwargs, что и целевая функция,
                и возвращающая строковый ключ кэша.
        ttl:    время жизни кэша в секундах.
        schema: Pydantic-модель для десериализации при cache-hit.
                Если передана — возвращает model_validate(hit) вместо raw dict.

    Пример:
        @cached(
            key_fn=lambda db, project_id: rpi_stats_key(project_id),
            schema=RPIStatsOut,
        )
        async def get_stats(db, project_id): ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            key = key_fn(*args, **kwargs)
            hit = await cache_get(key)
            if hit is not None:
                return schema.model_validate(hit) if schema else hit

            result = await func(*args, **kwargs)
            serializable = (
                result.model_dump() if hasattr(result, "model_dump") else result
            )
            await cache_set(key, serializable, ttl)
            return result

        return wrapper

    return decorator
