# Тестирование

> Многоуровневое тестирование: unit, integration, security, performance, contract. Pytest + httpx + fakeredis.

## Расположение в репозитории

| Путь | Назначение |
|------|-----------|
| `tests/` | Все тестовые файлы (14 файлов) |
| `tests/conftest.py` | Фикстуры pytest (engine, db, client, auth, redis mock) |
| `tests/factories.py` | Фабрики тестовых данных |
| `auto_test.py` | Скрипт автозапуска всех тестов с генерацией отчёта |
| `test_results/` | Результаты прогона тестов |
| `pyproject.toml` | Конфигурация pytest (asyncio_mode, timeout) |

## Как устроено

### Тестовые файлы и покрытие

| Файл | Строк | Тип | Что тестирует |
|------|-------|-----|--------------|
| `test_health.py` | 10 | Smoke | GET /health возвращает 200 |
| `test_projects_api.py` | 76 | CRUD | Базовые CRUD проектов + unique constraint |
| `test_sources_api.py` | 48 | CRUD | Базовые CRUD источников + 404 для чужого проекта |
| `test_source_tables_api.py` | 79 | CRUD | Базовые CRUD таблиц и колонок |
| `test_rpi_mappings_api.py` | 111 | CRUD | Базовые CRUD RPI + фильтры + stats |
| `test_functional_enhanced.py` | 999 | Functional | Edge cases, граничные значения, спецсимволы, пагинация, бизнес-логика |
| `test_security_api.py` | 470 | Security | OWASP Top 10: auth, authorization, SSRF, CORS, rate limiting |
| `test_performance_api.py` | 493 | Performance | Load (50 concurrent), stress (200), scalability, endurance, spike |
| `test_contract.py` | 667 | Contract | Pydantic-схемы, структура ответов, обратная совместимость |
| `test_validation.py` | 48 | Unit | Валидация формул (is_calculated → formula required) |
| `test_cache.py` | 17 | Integration | Проверка кэширования списка проектов |
| `test_errors.py` | 20 | Error | 404 и 422 ответы |
| `test_integration.py` | 564 | Integration | Redis (с `use_real_redis`), БД (транзакции, constraints, cascade), auth, OpenAPI |

### Фикстуры

```python
# conftest.py — основные фикстуры
engine              # session-scoped AsyncEngine, create_all
db_session          # function-scoped AsyncSession
clean_tables        # autouse: truncates all tables, inserts test superuser
override_db         # autouse: overrides FastAPI get_db dependency
auto_mock_redis     # autouse: mocks Redis (cache_get, cache_set, cache_delete, cache_delete_pattern)
authenticated       # создаёт пользователя в БД, мокает зависимости
client              # httpx.AsyncClient с ASGITransport
auth_client         # клиент с JWT-логином
```

### Redis Mock

По умолчанию Redis мокируется (`auto_mock_redis`). Для тестов с реальным Redis — маркер:

```python
@pytest.mark.use_real_redis
async def test_cache_invalidation():
    ...
```

### Запуск

```bash
# Все тесты
pytest

# С coverage
pytest --cov=app --cov-report=term-missing

# Конкретный файл
pytest tests/test_projects_api.py -v --tb=short

# Параллельный запуск
pytest -n auto

# Только performance тесты
pytest tests/test_performance_api.py -v

# Только security тесты
pytest tests/test_security_api.py -v

# Через auto_test.py (с генерацией отчёта)
python auto_test.py
```

### CI/CD (GitHub Actions)

`.github/workflows/api-testing.yml` — 4 джобы:

1. **test** — ruff lint/format + все тесты с pytest-cov → Codecov
2. **api-documentation** — валидация OpenAPI схемы
3. **security-scan** — Bandit + Safety
4. **deploy** — на main, после всех джоб

## Ключевые сущности

- **`factories.py`** — `create_project`, `create_source`, `create_source_table`, `create_source_column`, `create_rpi`
- **`auto_mock_redis`** — автоподмена Redis-функций на mock
- **`auth_client`** — pre-authenticated HTTP-клиент
- **`use_real_redis`** — pytest маркер для интеграционных тестов

## Связи с другими доменами

- Все домены: проект покрыт тестами всех уровней
- [infrastructure.md](infrastructure.md) — CI/CD джобы для тестов

## Нюансы и ограничения

- `auto_mock_redis` мокает 4 функции: `cache_get`, `cache_set`, `cache_delete`, `cache_delete_pattern`
- `test_mapping_tables_api.py` упоминается в `auto_test.py`, но **файла не существует** (ошибка в скрипте)
- Performance-тесты имеют хардкоднутые пороги (avg < 1s, success > 80%) — могут флакать на слабых машинах
- `conftest` устанавливает `DATABASE_URL` и `REDIS_URL` через monkeypatch окружения
- Интеграционные тесты с `use_real_redis` требуют запущенного Redis
