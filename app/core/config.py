from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_name: str = "FastAPI Microservices"
    version: str = "0.1.0"
    debug: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
