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
from app.core.auth import current_active_user
from app.database import Base, get_db
from app.main import app
from app.models.user import User

FAKE_PASSWORD = "testpassword123"


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
                    "source_tables, source_columns, rpi_mappings, "
                    "dwh_tables, dwh_columns, layer_mappings, layer_mapping_sources "
                    "RESTART IDENTITY CASCADE"
                )
            )
            # Создаем тестового суперпользователя с правильными полями fastapi-users
            await session.execute(
                text(
                    "INSERT INTO users (id, email, full_name, hashed_password, is_active, "
                    "is_superuser, is_verified, created_at, updated_at) "
                    "VALUES (1, 'test@example.com', 'Test User', :pw, true, true, true, "
                    ":now, :now)"
                ),
                {
                    "pw": "pbkdf2:sha256:260000$testsalt$testhash",
                    "now": datetime.now(UTC),
                },
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
async def authenticated(db_session, monkeypatch):
    """
    Фикстура для аутентификации. Возвращает пользователя и мокает зависимости.
    """
    # Получаем тестового пользователя из БД
    result = await db_session.execute(
        text("SELECT * FROM users WHERE email = 'test@example.com'")
    )
    user_row = result.first()

    # Создаем объект User
    user = User(
        id=user_row.id,
        email=user_row.email,
        full_name=user_row.full_name,
        hashed_password=user_row.hashed_password,
        is_active=user_row.is_active,
        is_superuser=user_row.is_superuser,
        is_verified=user_row.is_verified,
        created_at=user_row.created_at,
        updated_at=user_row.updated_at,
    )

    # Мокаем get_user_manager
    async def mock_get_user_manager():
        yield None

    monkeypatch.setattr(app, "get_user_manager", mock_get_user_manager)

    # Мокаем current_active_user
    async def mock_current_user():
        return user

    app.dependency_overrides[current_active_user] = mock_current_user

    yield user

    app.dependency_overrides.pop(current_active_user, None)


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
    # Получаем токен для аутентификации
    login_response = await client.post(
        "/auth/jwt/login",
        data={
            "username": "test@example.com",
            "password": FAKE_PASSWORD,
        },
    )

    if login_response.status_code == 200:
        tokens = login_response.json()
        access_token = tokens["access_token"]
        client.headers["Authorization"] = f"Bearer {access_token}"

    yield client
