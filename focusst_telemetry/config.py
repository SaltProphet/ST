"""Configuration management for Focus ST Telemetry"""

import os
from pathlib import Path
from typing import Optional
try:
    import tomli as tomllib
except ImportError:
    import tomllib


class Config:
    """Configuration handler for the telemetry system"""
    
    def __init__(self):
        self.data_source: str = "mock_ecu"
        self.host: str = "0.0.0.0"
        self.port: int = 8000
        self.update_rate: int = 20  # Hz
        self.log_level: str = "INFO"
        
    @classmethod
    def from_toml(cls, config_path: str) -> "Config":
        """Load configuration from TOML file"""
        config = cls()
        path = Path(config_path)
        
        if path.exists():
            with open(path, "rb") as f:
                data = tomllib.load(f)
                
            # Load settings
            config.data_source = data.get("data_source", config.data_source)
            config.host = data.get("host", config.host)
            config.port = data.get("port", config.port)
            config.update_rate = data.get("update_rate", config.update_rate)
            config.log_level = data.get("log_level", config.log_level)
                
        return config
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        config = cls()
        config.data_source = os.getenv("DATA_SOURCE", config.data_source)
        config.host = os.getenv("HOST", config.host)
        config.port = int(os.getenv("PORT", str(config.port)))
        config.update_rate = int(os.getenv("UPDATE_RATE", str(config.update_rate)))
        config.log_level = os.getenv("LOG_LEVEL", config.log_level)
        return config
