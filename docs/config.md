# Конфигурация приложения

> Централизованное управление настройками окружения, параметрами JWT, CORS и подключениями к внешним сервисам.

## Расположение в репозитории

| Путь | Назначение |
|------|-----------|
| `app/core/config.py` | Pydantic `Settings` — все настройки приложения |
| `.env` | Файл с переменными окружения (не коммитится) |
| `pyproject.toml` | Метаданные проекта, зависимости, инструменты (pytest, ruff) |
| `requirements.txt` | Минимальный список runtime-зависимостей |

## Как устроено

Класс `Settings` (наследуется от `pydantic_settings.BaseSettings`) загружает конфигурацию:

1. **Переменные окружения** — читаются из `.env` через `env_file=".env"`
2. **Значения по умолчанию** — вшиты в аннотации полей класса
3. **Валидация** — `CORS_ORIGINS` парсится из JSON-строки через `field_validator`

```python
class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/rpi_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL: int = 300
    REDIS_MAX_CONNECTIONS: int = 200
    APP_TITLE: str = "RPI Mapping API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    RESET_PASSWORD_TOKEN_SECRET: str = "reset-password-secret-change-in-production"
    VERIFICATION_TOKEN_SECRET: str = "verification-secret-change-in-production"
    COOKIE_SECURE: bool = True
    COOKIE_SAMESITE: str = "lax"
    COOKIE_MAX_AGE: int = 1800
```

## Ключевые сущности

- **`settings`** — глобальный синглтон, импортируется во всех модулях через `from app.core.config import settings`
- **`SettingsConfigDict(env_file=".env", extra="ignore")`** — конфигурация Pydantic для загрузки из `.env`

## Как использовать / запустить

```bash
# Создать .env файл с реальными значениями (см. .env.example)
# Запуск через docker-compose поднимает Postgres и Redis
docker compose up -d
# Ручной запуск сервера
uvicorn app.main:app --reload
```

## Связи с другими доменами

- [database.md](database.md) — использует `settings.DATABASE_URL`
- [cache.md](cache.md) — использует `settings.REDIS_URL`, `settings.CACHE_TTL`, `settings.REDIS_MAX_CONNECTIONS`
- [auth.md](auth.md) — использует `settings.JWT_SECRET_KEY`, `settings.ACCESS_TOKEN_EXPIRE_MINUTES`, cookie-настройки
- [api.md](api.md) — использует `settings.APP_TITLE`, `settings.APP_VERSION`, `settings.DEBUG`
- [infrastructure.md](infrastructure.md) — использует те же переменные окружения

## Нюансы и ограничения

- Секреты (`JWT_SECRET_KEY`, `RESET_PASSWORD_TOKEN_SECRET`, `VERIFICATION_TOKEN_SECRET`) имеют значения по умолчанию, **обязательно заменить в production**
- `CORS_ORIGINS` принимает JSON-строку: `'["http://localhost:5173"]'`
- `extras="ignore"` — лишние переменные окружения не вызывают ошибок
