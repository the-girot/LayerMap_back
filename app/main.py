from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.cache import _pool, get_redis
from app.core.config import settings
from app.routers import auth, projects, rpi_mappings, source_tables, sources

# Список разрешённых origins для CORS (конкретные URL, не *)
CORS_ORIGINS = [
    "http://localhost:5173",  # Vite dev
    "http://localhost:3000",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with get_redis() as r:
        await r.ping()
    yield
    if _pool:
        await _pool.aclose()


app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Роутеры аутентификации
# ---------------------------------------------------------------------------

app.include_router(auth.get_auth_router())

# ---------------------------------------------------------------------------
# Роутеры приложения
# ---------------------------------------------------------------------------

app.include_router(projects.router)
app.include_router(sources.router)
app.include_router(source_tables.router)
app.include_router(rpi_mappings.router)


@app.get("/health", tags=["Health"])
async def health():
    async with get_redis() as r:
        redis_ok = await r.ping()
    return {"status": "healthy", "redis": redis_ok}
