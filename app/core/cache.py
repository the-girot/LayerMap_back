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
            max_connections=settings.REDIS_MAX_CONNECTIONS,
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
    r = get_redis()
    cursor = 0
    iterations = 0
    max_iterations = 1000  # защита от бесконечного цикла
    while iterations < max_iterations:
        cursor, keys = await r.scan(cursor, match=pattern, count=100)
        if keys:
            await r.delete(*keys)
        if cursor == 0:
            break
        iterations += 1


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


def dwh_tables_key(project_id: int) -> str:
    return f"project:{project_id}:dwh_tables"


def dwh_table_key(project_id: int, table_id: int) -> str:
    return f"project:{project_id}:dwh_table:{table_id}"


def dwh_columns_key(table_id: int) -> str:
    return f"dwh_columns:{table_id}"


def dwh_column_key(table_id: int, column_id: int) -> str:
    return f"dwh_column:{table_id}:{column_id}"


def layer_mappings_key(project_id: int) -> str:
    return f"project:{project_id}:layer_mappings"


def layer_mapping_key(project_id: int, mapping_id: int) -> str:
    return f"project:{project_id}:layer_mapping:{mapping_id}"


def lineage_key(project_id: int) -> str:
    return f"project:{project_id}:lineage"


def hash_params(**kwargs) -> str:
    """Детерминированный хэш query-параметров для ключа кэша.
    MD5 используется только как быстрая хэш-функция, не для криптографии."""
    raw = json.dumps(kwargs, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()[:12]


# ── Декоратор для кэширования сервисных функций ───────────────────────────────
def _to_serializable(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, list):
        return [_to_serializable(i) for i in obj]
    return obj


async def close_redis() -> None:
    global _redis, _pool
    if _redis is not None:
        await _redis.aclose()
        _redis = None
    if _pool is not None:
        await _pool.aclose()
        _pool = None


def cached(
    key_fn: Callable[..., str],
    ttl: int = settings.CACHE_TTL,
    schema=None,
):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            key = key_fn(*args, **kwargs)
            hit = await cache_get(key)
            if hit is not None:
                if schema is None:
                    return hit
                if isinstance(hit, list):
                    return [schema.model_validate(item) for item in hit]
                return schema.model_validate(hit)

            result = await func(*args, **kwargs)
            await cache_set(key, _to_serializable(result), ttl)
            return result

        return wrapper

    return decorator
