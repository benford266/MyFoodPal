"""
Backend Configuration
"""
import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "sqlite:///./foodpal.db"
    
    # LM Studio / Ollama Configuration
    LM_STUDIO_BASE_URL: str = "http://localhost:11434"
    LM_STUDIO_MODEL: str = "llama3"
    
    # ComfyUI Configuration  
    COMFYUI_SERVER: str = "192.168.4.208:8188"
    ENABLE_IMAGE_GENERATION: bool = True
    
    # Security
    SECRET_KEY: str = "foodpal-secret-key-2024-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ]
    
    # File Storage
    MEDIA_DIR: str = "../media"
    
    class Config:
        env_file = ".env"


settings = Settings()