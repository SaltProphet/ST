"""Tests for data source factory."""

import pytest

from st_telemetry.config import Config
from st_telemetry.data_sources.factory import create_data_source
from st_telemetry.data_sources.mock_ecu import MockECU
from st_telemetry.data_sources.obd_bridge import OBDBridge


def test_create_mock_ecu():
    """Test creating Mock ECU data source."""
    config = Config()
    config.data_source.type = "mock_ecu"
    
    data_source = create_data_source(config)
    assert isinstance(data_source, MockECU)


def test_create_obd_bridge():
    """Test creating OBD bridge data source."""
    config = Config()
    config.data_source.type = "obd_bridge"
    
    data_source = create_data_source(config)
    assert isinstance(data_source, OBDBridge)


def test_invalid_data_source():
    """Test creating invalid data source."""
    config = Config()
    config.data_source.type = "invalid_source"
    
    with pytest.raises(ValueError, match="Unsupported data source type"):
        create_data_source(config)
