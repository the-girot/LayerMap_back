import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/rpi_db"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CACHE_TTL", "300")

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.core.cache as cache_module
from app.core.auth import get_current_user
from app.core.security import get_password_hash as _hash
from app.database import Base, get_db
from app.main import app
from app.models.user import User

FAKE_PASSWORD = "testpassword123"
FAKE_PASSWORD_HASH = _hash(FAKE_PASSWORD)

FAKE_USER = User(
    id=1,
    email="test@example.com",
    full_name="Test User",
    hashed_password=FAKE_PASSWORD_HASH,
    is_active=True,
    is_superuser=True,
    created_at=datetime.now(UTC),
    updated_at=datetime.now(UTC),
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
                    "source_tables, source_columns, rpi_mappings "
                    "RESTART IDENTITY CASCADE"
                )
            )
            await session.execute(
                text(
                    "INSERT INTO users (id, email, full_name, hashed_password, is_active, is_superuser) "
                    "VALUES (1, 'test@example.com', 'Test User', :pw, true, true)"
                ),
                {"pw": FAKE_PASSWORD_HASH},
            )
            await session.execute(
                text("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))")
            )
    yield


@pytest.fixture(autouse=True)
def override_db(session_maker):
    async def _get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
def auto_mock_redis(request, monkeypatch):
    """Мокает Redis везде кроме тестов с маркером use_real_redis."""
    if request.node.get_closest_marker("use_real_redis"):
        return
    monkeypatch.setattr(cache_module, "cache_get", AsyncMock(return_value=None))
    monkeypatch.setattr(cache_module, "cache_set", AsyncMock(return_value=None))
    monkeypatch.setattr(cache_module, "cache_delete", AsyncMock(return_value=None))
    monkeypatch.setattr(
        cache_module, "cache_delete_pattern", AsyncMock(return_value=None)
    )


@pytest.fixture
def authenticated():
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    yield FAKE_USER
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        yield c


@pytest.fixture
async def auth_client(client: AsyncClient, authenticated) -> AsyncClient:
    """AsyncClient с аутентифицированным первым пользователем."""
    yield client


@pytest.fixture
async def seeded_project_id(auth_client: AsyncClient) -> int:
    """Проект, созданный первым пользователем. Второй не имеет к нему доступа."""
    response = await auth_client.post(
        "/projects",
        json={"name": "Seeded Project for 403 test", "status": "active"},
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.fixture
async def another_user_client(session_maker) -> AsyncClient:
    """Второй пользователь — реальный объект в БД, НЕ суперпользователь."""
    from app.core.security import get_password_hash

    async with session_maker() as session:
        async with session.begin():
            await session.execute(
                text(
                    "INSERT INTO users (email, full_name, hashed_password, is_active, is_superuser) "
                    "VALUES ('another@example.com', 'Another User', :pw, true, false)"
                ),
                {"pw": get_password_hash("AnotherPass123!")},
            )

        result = await session.execute(
            text(
                "SELECT id, created_at, updated_at FROM users WHERE email = 'another@example.com'"
            )
        )
        row = result.one()

    another_user = User(
        id=row.id,
        email="another@example.com",
        full_name="Another User",
        hashed_password=get_password_hash("AnotherPass123!"),
        is_active=True,
        is_superuser=False,
        created_at=row.created_at,  # ← берём из БД
        updated_at=row.updated_at,  # ← берём из БД
    )

    app.dependency_overrides[get_current_user] = lambda: another_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        yield c

    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
