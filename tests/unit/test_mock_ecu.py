"""Tests for Mock ECU data source."""

import asyncio
import pytest

from st_telemetry.config import Config, PIDConfig
from st_telemetry.data_sources.mock_ecu import MockECU


@pytest.fixture
def test_config():
    """Create a test configuration."""
    config = Config()
    config.pids = {
        "list": [
            {
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
        ]
    }
    return config


@pytest.mark.asyncio
async def test_mock_ecu_initialization(test_config):
    """Test Mock ECU initialization."""
    mock_ecu = MockECU(test_config)
    await mock_ecu.initialize()
    
    assert mock_ecu._start_time is not None
    assert "boost" in mock_ecu._callbacks
    
    await mock_ecu.shutdown()


@pytest.mark.asyncio
async def test_read_pid(test_config):
    """Test reading a single PID value."""
    mock_ecu = MockECU(test_config)
    await mock_ecu.initialize()
    
    data_point = await mock_ecu.read_pid("boost")
    
    assert data_point is not None
    assert data_point.pid_name == "boost"
    assert data_point.pid_id == "2204FE"
    assert data_point.unit == "psi"
    assert isinstance(data_point.raw_value, float)
    assert isinstance(data_point.converted_value, float)
    assert data_point.timestamp > 0
    
    await mock_ecu.shutdown()


@pytest.mark.asyncio
async def test_value_conversion(test_config):
    """Test PID value conversion."""
    mock_ecu = MockECU(test_config)
    await mock_ecu.initialize()
    
    data_point = await mock_ecu.read_pid("boost")
    
    # Verify conversion formula: RawValue * 0.0145 - 14.7
    expected_conversion = data_point.raw_value * 0.0145 - 14.7
    assert abs(data_point.converted_value - expected_conversion) < 0.001
    
    await mock_ecu.shutdown()


@pytest.mark.asyncio
async def test_streaming(test_config):
    """Test data streaming."""
    mock_ecu = MockECU(test_config)
    await mock_ecu.initialize()
    
    # Collect data points
    data_points = []
    
    async def callback(data_point):
        data_points.append(data_point)
    
    mock_ecu.register_callback("boost", callback)
    
    # Start streaming
    await mock_ecu.start_streaming()
    assert mock_ecu.is_streaming()
    
    # Wait for some data
    await asyncio.sleep(0.2)
    
    # Stop streaming
    await mock_ecu.stop_streaming()
    assert not mock_ecu.is_streaming()
    
    # Should have received some data points
    assert len(data_points) > 0
    
    await mock_ecu.shutdown()


@pytest.mark.asyncio
async def test_warning_detection():
    """Test warning detection for OAR."""
    config = Config()
    config.pids = {
        "list": [
            {
                "id": "2203E8",
                "name": "oar",
                "description": "Octane Adjust Ratio",
                "unit": "ratio",
                "conversion_multiplier": 1.0,
                "conversion_offset": 0.0,
                "update_rate_hz": 5,
                "mock_wave_type": "sine",
                "mock_frequency": 0.2,
                "mock_amplitude": 0.5,
                "mock_offset": 0.0,
                "mock_noise_stddev": 0.05,
                "warning_threshold": -1.0,
            }
        ]
    }
    
    mock_ecu = MockECU(config)
    await mock_ecu.initialize()
    
    # Set previous value to threshold
    mock_ecu._previous_values["oar"] = -1.0
    
    # Generate a value that's different from threshold
    pid_config = config.get_pid_by_name("oar")
    warning = mock_ecu._check_warning(pid_config, 0.5)
    
    # Should trigger warning
    assert warning is not None
    assert "oar" in warning.lower()
    
    await mock_ecu.shutdown()
