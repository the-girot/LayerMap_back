from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.cache import _pool, get_redis
from app.core.config import settings
from app.core.middleware import CORSMiddleware as AppCORSMiddleware
from app.routers import auth, mapping_tables, projects, rpi_mappings, sources


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
    AppCORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(sources.router)
app.include_router(mapping_tables.router)
app.include_router(rpi_mappings.router)


@app.get("/health", tags=["Health"])
async def health():
    async with get_redis() as r:
        redis_ok = await r.ping()
    return {"status": "healthy", "redis": redis_ok}
