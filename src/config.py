"""Configuration management using Pydantic settings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # ECU configuration
    ecu_type: str = "mock"  # "mock" or "obd2"
    obd_port: Optional[str] = None  # None for auto-detect
    obd_baudrate: int = 38400
    
    # Telemetry streaming
    telemetry_interval: float = 0.1  # 100ms = 10Hz update rate
    
    # Application
    app_title: str = "Focus ST Telemetry Dashboard"
    app_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
