# Источники, Таблицы и Колонки

> Управление источниками данных (API, DB, FILE, STREAM) и их схемой (таблицы → колонки). Базовый строительный блок для RPI-маппингов.

## Расположение в репозитории

| Путь | Назначение |
|------|-----------|
| `app/models/source.py` | ORM модель Source, SourceType enum |
| `app/models/source_table.py` | ORM модели SourceTable, SourceColumn, ColumnType enum |
| `app/schemas/source.py` | Pydantic схемы Source (5 классов) |
| `app/schemas/source_table.py` | Pydantic схемы SourceTable + SourceColumn (9 классов) |
| `app/services/sources.py` | Бизнес-логика CRUD источников |
| `app/services/source_tables.py` | Бизнес-логика CRUD таблиц и колонок |
| `app/routers/sources.py` | REST эндпоинты источников |
| `app/routers/source_tables.py` | REST эндпоинты таблиц и колонок |

## Как устроено

### Иерархия

```
Project
  └── Source (id, name, type, project_id)
       └── SourceTable (id, name, source_id)
            └── SourceColumn (id, name, type: dimension/metric, data_type)
                 └── RPIMapping (FK source_column_id)
```

### Типы источников

```python
class SourceType(enum.StrEnum):
    API = "API"
    DB = "DB"
    FILE = "FILE"
    STREAM = "STREAM"
```

### Типы колонок

```python
class ColumnType(enum.StrEnum):
    dimension = "dimension"
    metric = "metric"
```

### Валидация формул

Для расчётных колонок (`is_calculated=True`) поле `formula` обязательно:

```python
@model_validator(mode="after")
def check_formula(self):
    if self.is_calculated and not self.formula:
        raise ValueError("formula обязательна для расчётных колонок")
    if not self.is_calculated and self.formula:
        self.formula = None  # автоочистка
    return self
```

### API эндпоинты

**Источники** (`/projects/{project_id}/sources`):

| Метод | Путь | Описание |
|-------|------|---------|
| GET | `/` | Список источников проекта |
| GET | `/{source_id}` | Детали + вложенные таблицы |
| POST | `/` | Создание |
| PATCH | `/{source_id}` | Обновление |
| DELETE | `/{source_id}` | Удаление |

**Таблицы** (`/projects/{project_id}/sources/{source_id}/tables`):

| Метод | Путь | Описание |
|-------|------|---------|
| GET | `/` | Список таблиц источника |
| GET | `/{table_id}` | Детали таблицы |
| POST | `/` | Создание |
| PATCH | `/{table_id}` | Обновление |
| DELETE | `/{table_id}` | Удаление |

**Колонки** (`.../tables/{table_id}/columns`):

| Метод | Путь | Описание |
|-------|------|---------|
| GET | `/` | Список колонок таблицы |
| GET | `/{column_id}` | Детали колонки |
| POST | `/` | Создание |
| PATCH | `/{column_id}` | Обновление |
| DELETE | `/{column_id}` | Удаление |

## Ключевые сущности

- **Source** — точка подключения источника данных
- **SourceTable** — логическая таблица внутри источника
- **SourceColumn** — колонка таблицы с типом (dimension/metric) и типом данных
- **DataType** — enum: string, integer, float, boolean, date, datetime
- **SourceTableOut** — включает вложенный список `columns`

## Связи с другими доменами

- [database.md](database.md) — ORM модели, каскадные удаления
- [projects.md](projects.md) — Source вложен в Project
- [rpi_mappings.md](rpi_mappings.md) — RPIMapping ссылается на SourceColumn
- [cache.md](cache.md) — кэширование списков источников
- [api.md](api.md) — зависимости, схемы, валидаторы

## Нюансы и ограничения

- **Полная вложенность**: удаление проекта → каскадно удаляются все источники, таблицы, колонки
- `SourceColumn` ссылается через FK на `SourceTable` с CASCADE
- `RPIMapping.source_column_id` — SET NULL (не удаляет RPI при удалении колонки)
- `SourceDetailOut` включает eager-load `tables`, что может быть дорогим для источников с большим количеством таблиц
- Кэш источников инвалидируется при мутациях
- `SourceColumnCreate` принимает `data_type` как enum `DataType`, а `SourceColumnUpdate` — как `str` (неконсистентность)
