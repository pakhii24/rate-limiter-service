from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379"
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/ratelimiter"
    app_env: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()