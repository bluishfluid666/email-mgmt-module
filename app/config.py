from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Settings
    app_name: str = "Email Management API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Azure/Graph Settings
    client_id: str = os.getenv('CLIENT_ID')
    tenant_id: str = os.getenv('TENANT_ID')
    graph_user_scopes: str = os.getenv('GRAPH_USER_SCOPES')
    
    # API Security
    api_key: str = "your-secure-api-key-here"  # In production, use a strong key
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
