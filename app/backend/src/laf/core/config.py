from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # Database - Using SQLite for easy testing
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    # Redis/Celery
    redis_url: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

    # App settings
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key")

    # External services
    kubernetes_namespace: str = os.getenv("K8S_NAMESPACE", "default")
    sample_prep_url: str = os.getenv("SAMPLE_PREP_URL", "http://localhost:5002")
    hplc_url: str = os.getenv("HPLC_URL", "http://localhost:5003")

    class Config:
        env_file = ".env"


settings = Settings()
