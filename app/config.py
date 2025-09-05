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
    client_id: str = "d5ae8779-b99a-4bbe-b7aa-a12299f08824"
    tenant_id: str = "077ebd7f-3765-4a11-ba7e-0a10f09e1498"
    graph_user_scopes: str = "User.Read Mail.Read Mail.Send"
    
    # API Security
    api_key: str = "your-secure-api-key-here"  # In production, use a strong key
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
