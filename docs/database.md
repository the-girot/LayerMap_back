# База данных и ORM

> PostgreSQL + SQLAlchemy async — основа хранения данных. Alembic для миграций схемы.

## Расположение в репозитории

| Путь | Назначение |
|------|-----------|
| `app/database.py` | Engine, AsyncSessionLocal, Base, get_db |
| `app/models/` | SQLAlchemy ORM-модели (7 файлов) |
| `alembic/` | Миграции схемы БД |
| `alembic.ini` | Конфигурация Alembic |
| `alembic/env.py` | Скрипт окружения Alembic |

## Как устроено

### Подключение

```python
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
```

- **AsyncEngine** — через `create_async_engine` с asyncpg
- **AsyncSessionLocal** — фабрика сессий
- **get_db** — FastAPI-зависимость, yield-сессия для lifespan запроса

### ORM-модели

Все модели наследуются от `Base = DeclarativeBase()`:

```
User (users)
  └── ProjectMember (project_members) — M:N связь User ↔ Project с ролью
  
Project (projects)
  ├── Source (sources)
  │   └── SourceTable (source_tables)
  │       └── SourceColumn (source_columns)
  └── RPIMapping (rpi_mappings) ──→ SourceColumn (FK source_column_id)
```

**Ключевые связи:**
- `Project` → `Source` — 1:N, каскадное удаление
- `Source` → `SourceTable` — 1:N, каскадное удаление
- `SourceTable` → `SourceColumn` — 1:N, каскадное удаление
- `Project` → `RPIMapping` — 1:N, каскадное удаление
- `RPIMapping` → `SourceColumn` — N:1, SET NULL при удалении колонки
- `User` ↔ `Project` — M:N через `ProjectMember` с ролью (owner/editor/viewer)

### Check Constraints

- `rpi_mappings.chk_formula`: `(is_calculated = TRUE AND formula IS NOT NULL) OR (is_calculated = FALSE)`
- `project_members.uq_project_members_user_project`: UniqueConstraint на `(user_id, project_id)`

### Миграции (Alembic)

Цепочка миграций:

| Ревизия | Описание |
|---------|---------|
| `94aca1390145` | Инициализация: projects, sources, mapping_tables, mapping_columns, rpi_mappings |
| `35bc1c36160b` | Unique name для projects, фикс server_default |
| `001_fix_measurement_type_enum` | Enum измерений: русский → английский |
| `ac218a78dc1f` | Timezone-aware timestamps |
| `f50fdec921f8` | Удаление циклического FK, рефакторинг |
| `5c43b21311b9` | Таблицы users и project_members |
| `002_mapping_to_source_table` | Миграция mapping_tables → source_tables |
| `cbc528c85f8f` | Фикс FK rpi_mappings → source_columns |
| `XXXX_fastapi_users_fields` | is_verified для users |
| `ba526ac7dd21` | FastAPI users: фикс Enum |
| `a031b94cecb6` | dimension поле, nullable measurement_type |

## Ключевые сущности

- **`Base`** — декларативный базовый класс для всех моделей
- **`get_db`** — генератор FastAPI, возвращает `AsyncSession`
- **`DBSession`** — тип: `Annotated[AsyncSession, Depends(get_db)]`
- **Project, Source, SourceTable, SourceColumn, RPIMapping, User, ProjectMember** — ORM-модели

## Как использовать / запустить

```bash
# Поднять БД
docker compose up -d postgres

# Применить миграции
alembic upgrade head

# Создать новую миграцию
alembic revision --autogenerate -m "описание"

# Откатить одну миграцию
alembic downgrade -1
```

## Связи с другими доменами

- [config.md](config.md) — `settings.DATABASE_URL`
- [projects.md](projects.md) — сервисы используют модели Project, ProjectMember
- [sources.md](sources.md) — сервисы используют Source, SourceTable, SourceColumn
- [rpi_mappings.md](rpi_mappings.md) — сервисы используют RPIMapping
- [users.md](users.md) — User модель и менеджер
- [api.md](api.md) — зависимости DBSession в роутерах

## Нюансы и ограничения

- `expire_on_commit=False` — объекты остаются доступными после commit
- Каскадные удаления: удаление проекта удаляет все связанные сущности
- `source_column_id` в RPIMapping — SET NULL, не каскадное удаление
- В миграциях есть несколько пустых (`pass only`) — технический долг
