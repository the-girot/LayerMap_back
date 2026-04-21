from pydantic_settings import BaseSettings
from pydantic import field_validator
import json
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL : str = "postgresql+asyncpg://user:password@localhost/rpi_db"
    REDIS_URL    : str = "redis://localhost:6379/0"
    CACHE_TTL    : int = 300
    APP_TITLE    : str = "RPI Mapping API"
    APP_VERSION  : str = "1.0.0"
    DEBUG        : bool = False
    CORS_ORIGINS : list[str] = ["http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"   # ← игнорировать неизвестные переменные
    )


settings = Settings()