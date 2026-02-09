"""Factory for creating data sources."""

import logging

from st_telemetry.config import Config
from st_telemetry.data_sources.base import DataSource
from st_telemetry.data_sources.mock_ecu import MockECU
from st_telemetry.data_sources.obd_bridge import OBDBridge

logger = logging.getLogger(__name__)


def create_data_source(config: Config) -> DataSource:
    """Create a data source based on configuration.
    
    Args:
        config: Configuration object
        
    Returns:
        DataSource instance
        
    Raises:
        ValueError: If data source type is not supported
    """
    source_type = config.data_source.type
    
    logger.info(f"Creating data source: {source_type}")
    
    if source_type == "mock_ecu":
        return MockECU(config)
    elif source_type == "obd_bridge":
        return OBDBridge(config)
    else:
        raise ValueError(f"Unsupported data source type: {source_type}")
