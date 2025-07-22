"""
Configuration module for the replenishment service.
Handles environment variables and application settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MongoDB Configuration
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "replenishment_service"
    mongodb_collection: str = "predictions"
    
    # Node.js API Configuration
    nodejs_api_base_url: str = "http://localhost:3000/api"
    nodejs_api_key: Optional[str] = None
    
    # FastAPI Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Model Configuration
    model_path: str = "./models/xgboost_model.pkl"
    model_retrain_interval_days: int = 30
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/replenishment_service.log"
    
    # Security
    secret_key: str = "your_secret_key_here"
    access_token_expire_minutes: int = 30
    
    # Feature Engineering
    historical_months: int = 12
    forecast_horizon: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 