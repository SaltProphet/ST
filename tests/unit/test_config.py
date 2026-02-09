"""Tests for configuration management."""

import pytest
from pathlib import Path
import tempfile
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from st_telemetry.config import Config, PIDConfig


def test_default_config():
    """Test default configuration."""
    config = Config()
    assert config.data_source.type == "mock_ecu"
    assert config.gateway.host == "0.0.0.0"
    assert config.gateway.port == 8000


def test_load_from_toml():
    """Test loading configuration from TOML file."""
    toml_content = """
[data_source]
type = "mock_ecu"

[gateway]
host = "127.0.0.1"
port = 9000

[[pids.list]]
id = "TEST01"
name = "test_pid"
description = "Test PID"
unit = "unit"
conversion_multiplier = 2.0
conversion_offset = 10.0
update_rate_hz = 5
mock_wave_type = "sine"
mock_frequency = 0.5
mock_amplitude = 5.0
mock_offset = 0.0
mock_noise_stddev = 0.1
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write(toml_content)
        config_path = f.name
    
    try:
        config = Config.load_from_file(config_path)
        assert config.data_source.type == "mock_ecu"
        assert config.gateway.host == "127.0.0.1"
        assert config.gateway.port == 9000
        
        pids = config.get_pids()
        assert len(pids) == 1
        assert pids[0].name == "test_pid"
        assert pids[0].conversion_multiplier == 2.0
    finally:
        Path(config_path).unlink()


def test_get_pid_by_name():
    """Test getting PID by name."""
    toml_content = """
[[pids.list]]
id = "2204FE"
name = "boost"
description = "Boost Pressure"
unit = "psi"
conversion_multiplier = 0.0145
conversion_offset = -14.7
update_rate_hz = 20
mock_wave_type = "sine"
mock_frequency = 0.5
mock_amplitude = 10.0
mock_offset = 5.0
mock_noise_stddev = 0.5
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write(toml_content)
        config_path = f.name
    
    try:
        config = Config.load_from_file(config_path)
        boost_pid = config.get_pid_by_name("boost")
        assert boost_pid is not None
        assert boost_pid.id == "2204FE"
        assert boost_pid.conversion_multiplier == 0.0145
        
        # Non-existent PID
        missing_pid = config.get_pid_by_name("nonexistent")
        assert missing_pid is None
    finally:
        Path(config_path).unlink()


def test_pid_config_validation():
    """Test PID configuration validation."""
    pid_data = {
        "id": "2204FE",
        "name": "boost",
        "description": "Boost Pressure",
        "unit": "psi",
        "conversion_multiplier": 0.0145,
        "conversion_offset": -14.7,
        "update_rate_hz": 20,
        "mock_wave_type": "sine",
        "mock_frequency": 0.5,
        "mock_amplitude": 10.0,
        "mock_offset": 5.0,
        "mock_noise_stddev": 0.5,
    }
    
    pid = PIDConfig(**pid_data)
    assert pid.name == "boost"
    assert pid.conversion_multiplier == 0.0145
    assert pid.update_rate_hz == 20
