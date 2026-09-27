from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "初中智能阅卷系统"
    DEBUG: bool = True
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./scoring_db.sqlite"
    
    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_DB: int = 0
    
    # MinIO 配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "scoring-images"
    MINIO_USE_SSL: bool = False
    
    # Celery 配置
    CELERY_BROKER_URL: str = "amqp://admin:admin123@localhost:5672//"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # JWT 配置
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    # OCR 配置
    OCR_DPI: int = 300
    OCR_CONFIDENCE_THRESHOLD: float = 0.6
    
    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    MAX_PDF_PAGES: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
