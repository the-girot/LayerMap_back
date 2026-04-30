# Кэширование (Redis)

> Прослойка Redis для кэширования сервисных данных с паттерновой инвалидацией и декоратором для функций.

## Расположение в репозитории

| Путь | Назначение |
|------|-----------|
| `app/core/cache.py` | Пул соединений, низкоуровневые хелперы, namespace-функции, декоратор `cached` |

## Как устроено

### Архитектура

```
ConnectionPool (один на процесс)
       │
    Redis (один на процесс)
       │
  ┌────┴────┐
cache_get() cache_set()
cache_delete() cache_delete_pattern()
       │
  cached(key_fn, ttl, schema) — декоратор сервисных функций
```

### Пул и клиент

```python
_pool = ConnectionPool.from_url(settings.REDIS_URL, max_connections=200)
_redis = Redis(connection_pool=_pool)
```

- **Один пул** на весь процесс (синглтон через `get_pool()`)
- **Один клиент** на весь процесс (`get_redis()`)
- **decode_responses=True** — строки автоматически декодируются из bytes

### Ключи кэша (namespace)

| Функция | Ключ | Пример |
|---------|------|--------|
| `project_key(id)` | `project:{id}:{suffix}` | `project:5:sources` |
| `rpi_list_key(id, hash)` | `project:{id}:rpi:list:{hash}` | `project:5:rpi:list:a1b2c3d4e5f6` |
| `rpi_stats_key(id)` | `project:{id}:rpi:stats` | `project:5:rpi:stats` |
| `sources_key(id)` | `project:{id}:sources` | `project:5:sources` |
| `mapping_tables_key(id)` | `project:{id}:mapping_tables` | `project:5:mapping_tables` |
| **Константы** | | |
| `PROJECTS_KPI_KEY` | `projects:kpi` | |
| `PROJECTS_RECENT_KEY` | `projects:recent` | |
| `PROJECTS_LIST_KEY` | `projects:list` | |

### Инвалидация

- `cache_delete(*keys)` — удаление конкретных ключей
- `cache_delete_pattern(pattern)` — сканирование и удаление по паттерну (с защитой от бесконечного цикла: max 1000 итераций)
- Инвалидация на мутациях: сервисы вызывают `cache_delete` после create/update/delete

### Декоратор `cached`

```python
def cached(key_fn, ttl=300, schema=None):
    # key_fn(*args, **kwargs) → строка-ключ
    # Если schema задана — Pydantic-валидация при hit'е
    # Если None — возвращается сырой dict/list
```

## Ключевые сущности

- **`_pool` / `_redis`** — глобальные синглтоны
- **`cache_get`, `cache_set`, `cache_delete`, `cache_delete_pattern`** — низкоуровневые операции
- **`hash_params(**kwargs)`** — детерминированный MD5-хэш параметров запроса для ключа
- **`cached(key_fn, ttl, schema)`** — декоратор для сервисных функций
- **`close_redis()`** — graceful shutdown

## Как использовать / запустить

```bash
# Redis поднимается через docker-compose
docker compose up -d redis
```

В тестах Redis мокируется автоматически (см. фикстуру `auto_mock_redis`), если не указан `@pytest.mark.use_real_redis`.

## Связи с другими доменами

- [config.md](config.md) — `settings.REDIS_URL`, `settings.CACHE_TTL`, `settings.REDIS_MAX_CONNECTIONS`
- [projects.md](projects.md) — сервисы проектов используют кэш
- [sources.md](sources.md) — сервисы источников используют кэш
- [rpi_mappings.md](rpi_mappings.md) — сервисы RPI используют кэш

## Нюансы и ограничения

- MD5 используется **только как быстрая хэш-функция** для ключей, не для криптографии
- `_to_serializable()` преобразует Pydantic-модели в dict через `model_dump()`
- Декоратор `cached` не поддерживает инвалидацию по зависимым ключам — инвалидация ручная в сервисах
- `REDIS_MAX_CONNECTIONS: 200` — пул соединений, а не максимум одновременных клиентов
