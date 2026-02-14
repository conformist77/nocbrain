from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://nocbrain:nocbrain_password@localhost:5432/nocbrain"
    redis_url: str = "redis://localhost:6379"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Zabbix
    zabbix_url: Optional[str] = None
    zabbix_user: Optional[str] = None
    zabbix_password: Optional[str] = None
    
    # LLM
    openai_api_key: Optional[str] = None
    llm_model: str = "gpt-3.5-turbo"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    class Config:
        env_file = ".env"


settings = Settings()
