"""Configuration management for the telemetry system."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Database Configuration
    database_url: str = "sqlite:///./telemetry.db"
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Telemetry Configuration
    rolling_buffer_seconds: int = 600
    sample_rate_hz: int = 10
    
    # Alerts Configuration
    enable_email_alerts: bool = False
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    alert_email_to: Optional[str] = None
    
    # Cloud Sync Configuration
    enable_cloud_sync: bool = False
    cloud_api_url: Optional[str] = None
    cloud_api_key: Optional[str] = None
    
    # OBD Configuration
    obd_port: str = "/dev/ttyUSB0"
    obd_baudrate: int = 38400
    simulation_mode: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
