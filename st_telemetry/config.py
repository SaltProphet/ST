"""Configuration management for ST Telemetry."""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import yaml
from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings


class PIDConfig(BaseModel):
    """Configuration for a single PID."""

    id: str
    name: str
    description: str
    unit: str
    conversion_multiplier: float = 1.0
    conversion_offset: float = 0.0
    update_rate_hz: int = 1
    mock_wave_type: str = "sine"
    mock_frequency: float = 0.1
    mock_amplitude: float = 1.0
    mock_offset: float = 0.0
    mock_noise_stddev: float = 0.1
    warning_threshold: Optional[float] = None


class DataSourceConfig(BaseModel):
    """Data source configuration."""

    type: str = "mock_ecu"


class GatewayConfig(BaseModel):
    """Gateway server configuration."""

    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = ["*"]
    websocket_path: str = "/socket.io"
    
    # Socket.io configuration
    socketio_logger: bool = True
    socketio_engineio_logger: bool = False


class UIConfig(BaseModel):
    """UI configuration."""

    enabled: bool = True
    templates_dir: str = "templates"
    static_dir: str = "static"
    title: str = "Focus ST Telemetry Dashboard"


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class Config(BaseSettings):
    """Main configuration class."""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    data_source: DataSourceConfig = Field(default_factory=DataSourceConfig)
    pids: Dict[str, Any] = Field(default_factory=dict)
    gateway: GatewayConfig = Field(default_factory=GatewayConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    _pid_list: Optional[List[PIDConfig]] = None

    @classmethod
    def load_from_file(cls, config_path: Optional[str] = None) -> "Config":
        """Load configuration from TOML or YAML file."""
        if config_path is None:
            # Search for config files in standard locations
            for candidate in ["config.toml", "config.yaml", "config.yml"]:
                if Path(candidate).exists():
                    config_path = candidate
                    break

        if config_path is None:
            # Return default config
            return cls()

        config_path_obj = Path(config_path)
        if not config_path_obj.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        # Load based on extension
        if config_path_obj.suffix == ".toml":
            with open(config_path_obj, "rb") as f:
                data = tomllib.load(f)
        elif config_path_obj.suffix in [".yaml", ".yml"]:
            with open(config_path_obj, "r") as f:
                data = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported configuration file format: {config_path_obj.suffix}")

        return cls(**data)

    def get_pids(self) -> List[PIDConfig]:
        """Get list of PID configurations."""
        if self._pid_list is None:
            self._pid_list = [PIDConfig(**pid) for pid in self.pids.get("list", [])]
        return self._pid_list

    def get_pid_by_name(self, name: str) -> Optional[PIDConfig]:
        """Get PID configuration by name."""
        for pid in self.get_pids():
            if pid.name == name:
                return pid
        return None


# Global configuration instance
_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """Get or load global configuration."""
    global _config
    if _config is None:
        _config = Config.load_from_file(config_path)
    return _config


def set_config(config: Config) -> None:
    """Set global configuration."""
    global _config
    _config = config
