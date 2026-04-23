from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:password@0.0.0.0:5432/admin_dashboard"
    redis_url: str = "redis://0.0.0.0:6379"
    secret_key: str = "change-me-in-production"
    environment: str = "development"
    admin_username: str = "admin"
    admin_password: str = "admin123"

    class Config:
        env_file = ".env"


settings = Settings()
