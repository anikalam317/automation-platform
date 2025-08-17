from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # Database - Using SQLite for easy testing
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    # Redis/Celery
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # App settings
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key")

    # External services
    kubernetes_namespace: str = os.getenv("K8S_NAMESPACE", "default")

    class Config:
        env_file = ".env"


settings = Settings()
