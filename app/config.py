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
    client_secret: str = os.getenv('CLIENT_SECRET')
    
    # MongoDB Settings
    mongodb_connection_string: str = os.getenv('MONGODB_CONNECTION_STRING', '')
    mongodb_database: str = os.getenv('MONGODB_DATABASE', 'powertrans_analytics')
    mongodb_collection: str = os.getenv('MONGODB_COLLECTION', 'email_viewers')
    
    # API Security
    api_key: str = "your-secure-api-key-here"  # In production, use a strong key
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
