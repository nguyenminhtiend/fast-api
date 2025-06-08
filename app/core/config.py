from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_name: str
    version: str
    debug: bool

    # Security
    secret_key: str = "your-secret-key-change-this-in-production"

    # Database
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str

    @property
    def database_url(self) -> str:
        """Async SQLAlchemy database URL"""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def sync_database_url(self) -> str:
        """Sync SQLAlchemy database URL for Alembic"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
