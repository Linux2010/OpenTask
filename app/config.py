"""
OpenTask Configuration

Environment-based configuration using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Database Configuration
    DB_HOST: str = "hope05"
    DB_PORT: int = 53306
    DB_USER: str = "root"
    DB_PASSWORD: str = "Tianfs@2020!!"
    DB_NAME: str = "hope_engine"
    
    # API Configuration
    API_KEY: str = "hope-bot-apikey-2026-0424"
    API_PORT: int = 8090
    API_PREFIX: str = "/api"
    
    # Service Configuration
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def database_url(self) -> str:
        """Get database connection URL"""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()