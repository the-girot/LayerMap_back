# Project Overview

## Purpose
LayerMap API — это бэкенд-сервис для управления маппингом показателей (RPI Mappings) между источниками данных и объектами бизнес-модели. API поддерживает CRUD-операции для проектов, источников данных, таблиц маппинга с колонками, и карточек показателей. Целевые потребители — frontend-приложения (SPA) и внутренние инструменты аналитики.

## Directory Structure
```
app/
├── core/
│   ├── cache.py       # Redis-кэш (ключи, TTL, декоратор @cached)
│   ├── config.py      # Настройки через pydantic-settings (.env)
│   ├── dependencies.py # FastAPI Depends (DBSession, ValidProject, Pagination)
│   ├── middleware.py  # Кастомный CORS middleware
│   └── utils.py       # Обработка IntegrityError → 409
├── models/            # SQLAlchemy ORM-модели
│   ├── project.py
│   ├── source.py
│   ├── mapping_table.py
│   └── rpi_mapping.py
├── routers/           # API роуты (FastAPI APIRouter)
│   ├── projects.py
│   ├── sources.py
│   ├── mapping_tables.py
│   └── rpi_mappings.py
├── schemas/           # Pydantic v2 схемы (request/response)
│   ├── project.py
│   ├── source.py
│   ├── mapping_table.py
│   └── rpi_mapping.py
└── services/          # Бизнес-логика (CRUD, фильтры, кэш)
    ├── projects.py
    ├── sources.py
    ├── mapping_tables.py
    └── rpi_mappings.py

alembic/               # Миграции SQLAlchemy
├── env.py
└── versions/
    ├── 94aca1390145_init.py
    ├── 35bc1c36160b_unique_proj_name.py
    └── 001_fix_measurement_type_enum.py

tests/                 # Pytest-тесты
```

## Routers & Endpoints

### Projects (`/projects`)
| Method | Path | Описание |
|--------|------|----------|
| GET | `/` | Список проектов (фильтры: status, search, пагинация, сортировка) |
| GET | `/{project_id}` | Детали проекта |
| POST | `/` | Создание проекта |
| PATCH | `/{project_id}` | Частичное обновление |
| DELETE | `/{project_id}` | Удаление проекта |
| GET | `/kpi` | KPI: total, active, draft, archived |
| GET | `/recent` | Последние N проектов (по updated_at) |

### Sources (`/projects/{project_id}/sources`)
| Method | Path | Описание |
|--------|------|----------|
| GET | `/` | Список источников проекта |
| GET | `/{source_id}` | Детали источника |
| POST | `/` | Создание источника |
| PATCH | `/{source_id}` | Обновление источника |
| DELETE | `/{source_id}` | Удаление источника |

### Mapping Tables (`/projects/{project_id}/mapping-tables`)
| Method | Path | Описание |
|--------|------|----------|
| GET | `/` | Список таблиц маппинга |
| GET | `/{table_id}` | Детали таблицы (включая columns) |
| POST | `/` | Создание таблицы |
| PATCH | `/{table_id}` | Обновление таблицы |
| DELETE | `/{table_id}` | Удаление таблицы |
| GET | `/{table_id}/columns` | Список колонок таблицы |
| GET | `/{table_id}/columns/{column_id}` | Детали колонки |
| POST | `/{table_id}/columns` | Создание колонки |
| PATCH | `/{table_id}/columns/{column_id}` | Обновление колонки |
| DELETE | `/{table_id}/columns/{column_id}` | Удаление колонки |

### RPI Mappings (`/projects/{project_id}/rpi-mappings`)
| Method | Path | Описание |
|--------|------|----------|
| GET | `/stats` | Статистика по статусам (total, approved, in_review, draft) |
| GET | `/` | Список карточек (фильтры: status, ownership, measurement_type, is_calculated, search; пагинация skip/limit) |
| GET | `/{rpi_id}` | Детали карточки |
| POST | `/` | Создание карточки |
| PATCH | `/{rpi_id}` | Обновление карточки |
| DELETE | `/{rpi_id}` | Удаление карточки |

## Pydantic Schemas

### Project
- `ProjectBase`: name, description, status (draft по умолчанию)
- `ProjectCreate`: наследует ProjectBase
- `ProjectUpdate`: все поля optional (PATCH)
- `ProjectOut`: ProjectBase + id, created_at, updated_at
- `ProjectKPIOut`: total, active, draft, archived
- `ProjectSummaryOut`: id, name, status, updated_at

### Source
- `SourceBase`: name, description, type (DB), row_count (0), mapping_table_id, last_updated
- `SourceCreate`: наследует SourceBase
- `SourceUpdate`: все поля optional
- `SourceOut`: SourceBase + id, project_id, created_at

### MappingTable
- `MappingTableBase`: name, description, source_id
- `MappingTableCreate`: наследует MappingTableBase
- `MappingTableUpdate`: все поля optional
- `MappingTableOut`: MappingTableBase + id, project_id, created_at, updated_at, columns[]

### MappingColumn
- `MappingColumnBase`: name, type (dimension), data_type, description, is_calculated (False), formula
- `MappingColumnCreate`: наследует MappingColumnBase
- `MappingColumnUpdate`: все поля optional
- `MappingColumnOut`: MappingColumnBase + id, mapping_table_id, created_at

### RPIMapping
- `RPIMappingBase`: ownership, status (draft), block, measurement_type, is_calculated (False), formula, measurement, measurement_description, source_report, object_field, source_column_id, date_added, date_removed, comment, verification_file
- `RPIMappingCreate`: наследует RPIMappingBase
- `RPIMappingUpdate`: measurement, object_field, measurement_type (optional)
- `RPIMappingOut`: RPIMappingBase + id, number, project_id, created_at, updated_at
- `RPIStatsOut`: total, approved, in_review, draft

**Сопоставление с DB-моделями:**
- Все схемы соответствуют ORM-моделям, за исключением `RPIMappingUpdate`, который не включает все поля (только изменяемые через PATCH)
- Валидация формулы при `is_calculated=true` реализована через `@model_validator(mode="after")` в схемах [`mapping_table.py`](app/schemas/mapping_table.py:17) и [`rpi_mapping.py`](app/schemas/rpi_mapping.py:60)

## SQLAlchemy Models

### Project
```python
class Project(Base):
    __tablename__ = "projects"
    id: int (PK)
    name: str (unique, not null)
    description: str | None
    status: ProjectStatus (active|draft|archived)
    created_at: datetime
    updated_at: datetime
    sources: list[Source]
    mapping_tables: list[MappingTable]
    rpi_mappings: list[RPIMapping]
```

### Source
```python
class Source(Base):
    __tablename__ = "sources"
    id: int (PK)
    project_id: int (FK → projects.id, CASCADE)
    mapping_table_id: int | None (FK → mapping_tables.id, SET NULL)
    name: str (not null)
    description: str | None
    type: SourceType (API|DB|FILE|STREAM)
    row_count: int
    last_updated: datetime | None
    created_at: datetime
    project: Project
    mapping_table: MappingTable | None
```

### MappingTable
```python
class MappingTable(Base):
    __tablename__ = "mapping_tables"
    id: int (PK)
    project_id: int (FK → projects.id, CASCADE)
    source_id: int | None (FK → sources.id, SET NULL)
    name: str (not null)
    description: str | None
    created_at: datetime
    updated_at: datetime
    project: Project
    columns: list[MappingColumn]
```

### MappingColumn
```python
class MappingColumn(Base):
    __tablename__ = "mapping_columns"
    id: int (PK)
    mapping_table_id: int (FK → mapping_tables.id, CASCADE)
    name: str (not null)
    type: ColumnType (dimension|metric)
    data_type: str (not null)
    description: str | None
    is_calculated: bool
    formula: str | None
    created_at: datetime
    mapping_table: MappingTable
    rpi_mappings: list[RPIMapping]
```

### RPIMapping
```python
class RPIMapping(Base):
    __tablename__ = "rpi_mappings"
    id: int (PK)
    number: int | None
    project_id: int (FK → projects.id, CASCADE)
    source_column_id: int | None (FK → mapping_columns.id, SET NULL)
    ownership: str | None
    status: RPIStatus (approved|in_review|draft)
    block: str | None
    measurement_type: MeasurementType (dimension|metric)
    is_calculated: bool
    formula: str | None
    measurement: str (not null)
    measurement_description: str | None
    source_report: str | None
    object_field: str (not null)
    date_added: date | None
    date_removed: date | None
    comment: str | None
    verification_file: str | None
    created_at: datetime
    updated_at: datetime
    project: Project
    source_column: MappingColumn | None
    
    __table_args__ = (
        CheckConstraint(
            "(is_calculated = TRUE AND formula IS NOT NULL) OR (is_calculated = FALSE)",
            name="chk_formula",
        ),
    )
```

## Alembic Migrations
- **Текущая ревизия:** `001_fix_measurement_type` (последняя в `alembic/versions/`)
- **Цепочка миграций:**
  1. `94aca1390145_init.py` — первоначальная схема (projects, sources, mapping_tables, mapping_columns, rpi_mappings)
  2. `35bc1c36160b_unique_proj_name.py` — добавлен уникальный constraint на `projects.name`, изменены server_default для `is_calculated` и `row_count`
  3. `001_fix_measurement_type_enum.py` — конвертация enum `measurement_type` из `('Измерение', 'Метрика')` в `('dimension', 'metric')`

**Статус:** Миграции соответствуют моделям. Enum `measurement_type` в модели использует `dimension|metric`, что согласуется с последней миграцией.

## Business Logic

### Projects
- **CRUD:** [`app/services/projects.py`](app/services/projects.py:178-297)
- **Фильтрация/поиск:** `get_filtered_list()` — по status, search (ILIKE), пагинация, сортировка по updated_at
- **KPI:** `get_kpi()` — агрегация COUNT по статусам
- **Recent:** `get_recent()` — последние N по updated_at (кэшируется для limit=5)

### Sources
- **CRUD:** [`app/services/sources.py`](app/services/sources.py:51-104)
- **Кэш:** список и детали по ключу `project:{project_id}:sources`

### Mapping Tables + Columns
- **CRUD таблиц:** [`app/services/mapping_tables.py`](app/services/mapping_tables.py:75-132)
- **CRUD колонок:** `create_column()`, `update_column()`, `delete_column()`
- **Кэш:** таблицы по `project:{project_id}:mapping_tables`, колонки по `mapping_table:{table_id}:columns`

### RPI Mappings
- **CRUD:** [`app/services/rpi_mappings.py`](app/services/rpi_mappings.py:128-180)
- **Фильтры:** status, ownership, measurement_type, is_calculated, search (по measurement, object_field, ownership)
- **Пагинация:** skip/limit
- **Stats:** `get_stats()` — агрегатный запрос с GROUP BY status
- **Кэш:** список с хэшированием параметров, stats по ключу `project:{project_id}:rpi:stats` (TTL=120)

## Dependency Injection
- **DB Session:** `DBSession = Annotated[AsyncSession, Depends(get_db)]` ([`app/core/dependencies.py`](app/core/dependencies.py:12))
- **ValidProject:** `ValidProject = Annotated[Project, Depends(get_project_or_404)]` — загрузка проекта по ID из пути, 404 если не найден
- **Pagination:** `PaginationDep = Annotated[Pagination, Depends(Pagination)]` — skip/limit с валидацией (skip≥0, 1≤limit≤100)
- **Auth:** отсутствует (нет middleware или Depends для аутентификации)

## Configuration
- **Settings class:** [`app/core/config.py`](app/core/config.py:7) наследует `BaseSettings`
- **Поля:**
  - `DATABASE_URL`: `postgresql+asyncpg://user:password@localhost/rpi_db`
  - `REDIS_URL`: `redis://localhost:6379/0`
  - `CACHE_TTL`: 300 (секунд)
  - `APP_TITLE`: "RPI Mapping API"
  - `APP_VERSION`: "1.0.0"
  - `DEBUG`: False
  - `CORS_ORIGINS`: `["http://localhost:5173"]` (парсится из JSON строки)
- **`.env`:** файл подключён через `model_config = SettingsConfigDict(env_file=".env")`

## Redis Usage
Redis **используется** для кэширования:
- **Ключи:**
  - `projects:kpi` — KPI агрегаты (TTL=60)
  - `projects:recent` — последние 5 проектов (TTL=60)
  - `projects:list` — список всех проектов (TTL=60)
  - `project:{id}` — детали проекта (TTL=300)
  - `project:{id}:rpi:list:{hash}` — список RPI с фильтрами (TTL=60)
  - `project:{id}:rpi:stats` — статистика RPI (TTL=120)
  - `project:{id}:sources` — список источников (TTL=300)
  - `project:{id}:mapping_tables` — таблицы маппинга (TTL=300)
- **Декоратор:** `@cached(key_fn, ttl)` в [`app/core/cache.py`](app/core/cache.py:93)
- **Lifespan:** в [`app/main.py`](app/main.py:12) проверяется ping Redis при старте

## File Handling
- **verification_file:** поле в `RPIMapping` хранит путь/имя файла (строка, max 512 символов)
- **Хранение:** файлы **не загружаются** через API — поле остаётся `None` или содержит ссылку
- **python-multipart:** зависимость есть в `requirements.txt` и `pyproject.toml`, но **не используется** в коде (нет эндпоинтов для загрузки файлов)
- **Сервис файлов:** отсутствует

## Error Handling
- **HTTP 404:** возвращается при отсутствии ресурса (проект, источник, таблица, колонка, RPI)
- **HTTP 409:** конфликт уникальности (дубликат имени проекта) — перехватывается через `handle_integrity()` в [`app/core/utils.py`](app/core/utils.py:8)
- **HTTP 422:** валидация Pydantic (некорректный request body)
- **Кастомный middleware:** CORS обрабатывается через [`app/core/middleware.py`](app/core/middleware.py:9), включая OPTIONS preflight
- **Глобальные exception handlers:** не определены (используются стандартные FastAPI)

## Validation Logic
- **Формула при is_calculated=true:**
  - `MappingColumnBase.check_formula()` в [`app/schemas/mapping_table.py`](app/schemas/mapping_table.py:17)
  - `RPIMappingBase.formula_required_if_calculated()` в [`app/schemas/rpi_mapping.py`](app/schemas/rpi_mapping.py:60)
- **DB-level constraint:** `chk_formula` в таблице `rpi_mappings` ([`alembic/versions/94aca1390145_init.py`](alembic/versions/94aca1390145_init.py:103))
- **Пагинация:** `Pagination` валидирует `skip≥0`, `1≤limit≤100` через `Query()`
- **Поиск:** `search` в `/projects` имеет `min_length=1`

## Unused Dependencies
| Зависимость | Статус | Примечание |
|-------------|--------|------------|
| `redis[asyncio]` | **Используется** | Кэширование в `app/core/cache.py` |
| `python-multipart` | **Не используется** | Нет эндпоинтов для загрузки файлов |
| `httpx` | **Не используется** | Есть в `pyproject.toml`, но нет импортов в коде |
| `ruff` | **Не используется** | Только для линтинга/форматирования |
| `pytest*` | **Не используется** | Только для тестов |

## Known Issues / TODOs
- **TODO:** ACL/permissions для проектов (отмечено в [`app/services/projects.py:156`](app/services/projects.py:156))
- **TODO:** Фильтр по `user_id` в `get_recent()` не реализован
- **DOCS MISMATCH:** В [`API.md`](API.md:348) указано `MeasurementType = 'Измерение' | 'Метрика'`, но в коде и миграциях используется `('dimension', 'metric')`
- **DOCS MISMATCH:** В схеме `RPIMappingUpdate` в [`app/schemas/rpi_mapping.py:71`](app/schemas/rpi_mapping.py:71) отсутствуют поля `ownership`, `block`, `status`, `is_calculated`, `formula`, `date_added`, `date_removed`, `comment`, `verification_file` — они не могут быть обновлены через PATCH
- **Potential issue:** В `get_one()` для `RPIMapping` при возврате из кэша возвращается `dict`, что может вызвать проблемы при последующих операциях (обработано в `update()`)
- **No file upload:** `verification_file` поле существует, но нет механизма загрузки/хранения файлов
