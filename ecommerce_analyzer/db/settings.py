"""Settings for database connection."""
from typing import Optional

from config import ENV_DIR
from pydantic import BaseSettings, Field

MAX_QUERY_ARGS = 32767


class DataBaseSettings(BaseSettings):
    """Data base settings."""

    user: str = Field(..., env="POSTGRES_USER")
    password: str = Field(..., env="POSTGRES_PASSWORD")
    host: str = Field(..., env="POSTGRES_HOST")
    port: int = Field(..., env="POSTGRES_PORT")
    db: str = Field(..., env="POSTGRES_DB")

    def dsn(self) -> str:
        """Generate dsn string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    class Config:
        """Config."""

        env_prefix = "postgres_"
        env_file = ENV_DIR / ".env"
