# Инфраструктура

> Docker Compose, CI/CD, окружение и настройки развёртывания.

## Расположение в репозитории

| Путь | Назначение |
|------|-----------|
| `docker-compose.yaml` | Postgres 16 + Redis 7 |
| `Dockerfile` | <!-- Не обнаружено в репозитории --> |
| `.github/workflows/api-testing.yml` | CI/CD: tests, lint, security scan, deploy |
| `.env` | Переменные окружения (secrets) |
| `.python-version` | Версия Python для проекта |
| `pyproject.toml` | Зависимости, метаданные, инструменты |

## Как устроено

### Docker Compose

```yaml
services:
  postgres:
    image: postgres:16-alpine
    ports: ["5432:5432"]
    environment:
      POSTGRES_DB: rpi_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    healthcheck: pg_isready
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    healthcheck: redis-cli ping
    volumes: [redisdata:/data]
    command: redis-server --save 60 1
```

### CI/CD Pipeline

4 параллельные джобы в GitHub Actions:

```mermaid
graph LR
    Push["Push / PR"] --> Test["test (pytest + coverage)"]
    Push --> Docs["api-documentation"]
    Push --> Security["security-scan (Bandit + Safety)"]
    Test --> Deploy["deploy (main only)"]
    Docs --> Deploy
    Security --> Deploy
```

**test job:**
- Ubuntu latest, Postgres 15 + Redis 7 service containers
- Python 3.11, ruff lint + format check
- Все тесты с pytest-cov → Codecov
- Отдельные прогоны: security, performance, integration, contract suites

**security-scan job:**
- Bandit (SAST)
- Safety (dependency vulnerabilities)

**deploy job:**
- Только для main branch
- Placeholder (реальная логика деплоя не реализована)

### Переменные окружения

| Переменная | По умолчанию | Описание |
|-----------|-------------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://user:password@localhost/rpi_db` | PostgreSQL подключение |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis подключение |
| `CACHE_TTL` | `300` | TTL кэша в секундах |
| `DEBUG` | `false` | Режим отладки |
| `APP_TITLE` | `"RPI Mapping API"` | Название приложения |
| `APP_VERSION` | `"1.0.0"` | Версия |
| `CORS_ORIGINS` | `['http://localhost:5173']` | Разрешённые CORS origin'ы |
| `JWT_SECRET_KEY` | `"your-super-secret-key-change-in-production"` | Секрет для подписи JWT |
| `COOKIE_SECURE` | `true` | Secure флаг cookie |
| `COOKIE_SAMESITE` | `lax` | SameSite политика |
| `COOKIE_MAX_AGE` | `1800` | Время жизни cookie |

## Ключевые сущности

- **docker-compose.yaml** — локальная инфраструктура (Postgres + Redis)
- **api-testing.yml** — CI/CD pipeline

## Как использовать / запустить

```bash
# Локальный запуск инфраструктуры
docker compose up -d

# Применить миграции
alembic upgrade head

# Запустить приложение
uvicorn app.main:app --reload

# Собрать и запустить (если будет Dockerfile)
docker compose --profile app up -d
```

## Связи с другими доменами

- [config.md](config.md) — переменные окружения, настройки
- [tests.md](tests.md) — CI/CD запуск тестов
- [database.md](database.md) — миграции, подключение к БД
- [cache.md](cache.md) — подключение к Redis

## Нюансы и ограничения

- **Dockerfile отсутствует** — приложение не контейнеризировано для production
- **Локальный запуск** требует ручного запуска `uvicorn`
- CI/CD **deploy job** — placeholder, реальная логика деплоя не реализована
- Пароли и секреты в `docker-compose.yaml` и `.env` — **только для разработки**
- `.python-version` указывает версию Python, но CI использует Python 3.11 (несоответствие с pyproject.toml, где >=3.13)
