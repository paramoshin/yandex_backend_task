"""Settings for database connection."""
from ecommerce_analyzer.config import ENV_DIR
from pydantic import BaseSettings, Field


class DataBaseSettings(BaseSettings):
    """Data base settings."""

    user: str = Field(..., env="PG_USER")
    password: str = Field(..., env="PG_PASSWORD")
    host: str = Field(..., env="PG_HOST")
    port: int = Field(..., env="PG_PORT")
    db: str = Field(..., env="PG_DB")

    def dsn(self) -> str:
        """Generate dsn string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    class Config:
        """Config."""

        env_prefix = "pg_"
        env_file = ENV_DIR / ".env"
