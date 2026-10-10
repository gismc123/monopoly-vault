from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    """App settings, read from environment variables (see .env.example)."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    # Either give a full DATABASE_URL, or the POSTGRES_* parts and we build it.
    database_url: str | None = None
    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_user: str = "vault"
    postgres_password: str = ""
    postgres_db: str = "vault"

    jwt_secret: str = "dev-only-secret"
    jwt_expire_hours: int = 720
    allow_signup: bool = True

    campaign_year: int = 2026
    photo_dir: str = "/data/photos"
    max_upload_mb: int = 12

    @property
    def sqlalchemy_url(self) -> str | URL:
        if self.database_url:
            return self.database_url
        return URL.create(
            "postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
