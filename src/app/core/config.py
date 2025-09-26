# app/core/config.py
from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Project Metadata ---
    PROJECT_NAME: str = "Hackathon API"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Backend service for automating Social Media"
    ENVIRONMENT: str = "development"

    # --- API Configuration ---
    API_V1_STR: str = "/api/v1"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000"
    )

    # --- Core Infrastructure Credentials ---
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_SERVER: str = "postgres"
    POSTGRES_PORT: int = 5432

    API_KEY: str

    REDIS_URL: str

    FRONTEND_URL: str = "http://localhost:5173"

    @computed_field
    @property
    def DATABASE_URL(self) -> PostgresDsn:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field
    @property
    def DATABASE_URL_SYNC(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@localhost:5433/{self.POSTGRES_DB}"
        )

    # --- Database Pool Settings (CORRECTED) ---
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_TIMEOUT: int = 30

    # --- Security & JWT Settings ---
    JWT_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ALGORITHM: str = "HS256"

    # --- Model Configuration ---
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
