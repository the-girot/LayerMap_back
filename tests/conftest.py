import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/rpi_db"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CACHE_TTL", "300")

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.core.cache as cache_module
from app.core.auth import get_current_user
from app.database import Base, get_db
from app.main import app
from app.models.user import User

FAKE_USER = User(
    id=1,
    email="test@example.com",
    full_name="Test User",
    hashed_password="hash",
    is_active=True,
    is_superuser=True,
)


@pytest.fixture(scope="session")
async def engine():
    _engine = create_async_engine(os.environ["DATABASE_URL"], echo=False, future=True)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    await _engine.dispose()


@pytest.fixture(scope="session")
def session_maker(engine):
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture
async def db_session(session_maker) -> AsyncSession:
    async with session_maker() as session:
        yield session


@pytest.fixture(autouse=True)
async def clean_tables(session_maker):
    async with session_maker() as session:
        async with session.begin():
            await session.execute(
                text(
                    "TRUNCATE users, project_members, projects, sources, "
                    "mapping_tables, mapping_columns, rpi_mappings "
                    "RESTART IDENTITY CASCADE"
                )
            )
            # Создаём тестового пользователя сразу после очистки
            await session.execute(
                text(
                    "INSERT INTO users (id, email, full_name, hashed_password, is_active, is_superuser) "
                    "VALUES (1, 'test@example.com', 'Test User', 'hash', true, true)"
                )
            )
    yield


@pytest.fixture(autouse=True)
def override_db(session_maker):
    async def _get_db():
        async with session_maker() as session:
            yield session

    async def _get_current_user():
        return FAKE_USER

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_current_user] = _get_current_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_redis(monkeypatch):
    monkeypatch.setattr(cache_module, "cache_get", AsyncMock(return_value=None))
    monkeypatch.setattr(cache_module, "cache_set", AsyncMock(return_value=None))
    monkeypatch.setattr(cache_module, "cache_delete", AsyncMock(return_value=None))
    monkeypatch.setattr(
        cache_module, "cache_delete_pattern", AsyncMock(return_value=None)
    )


@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        yield c
