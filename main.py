"""Main entry point for Focus ST Telemetry Gateway"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

import uvicorn

from focusst_telemetry.config import Config
from focusst_telemetry.ecu.mock import MockECU
from focusst_telemetry.ecu.obd_bridge import OBDBridge
from focusst_telemetry.gateway.app import TelemetryGateway


def setup_logging(level: str = "INFO"):
    """Configure logging"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def create_ecu(data_source: str, update_rate: int):
    """Factory function to create ECU instance based on data source"""
    if data_source == "mock_ecu":
        return MockECU(update_rate=update_rate)
    elif data_source == "obd_bridge":
        return OBDBridge()
    else:
        raise ValueError(f"Unknown data source: {data_source}")


async def run_gateway(config: Config):
    """Run the telemetry gateway"""
    # Create ECU instance
    ecu = create_ecu(config.data_source, config.update_rate)
    
    # Create gateway
    gateway = TelemetryGateway(ecu, update_rate=config.update_rate)
    
    # Start gateway (this starts the data loop)
    await gateway.start()
    
    # Configure uvicorn
    uvicorn_config = uvicorn.Config(
        gateway.app,
        host=config.host,
        port=config.port,
        log_level=config.log_level.lower(),
    )
    server = uvicorn.Server(uvicorn_config)
    
    try:
        # Run server
        await server.serve()
    finally:
        # Clean shutdown
        await gateway.stop()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Focus ST Telemetry Gateway - Real-time ECU monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with mock ECU (development)
  python main.py --data_source mock_ecu
  
  # Run with OBD-II bridge (production)
  python main.py --data_source obd_bridge
  
  # Specify custom host and port
  python main.py --host 0.0.0.0 --port 8080
  
  # Load from config file
  python main.py --config config.toml
        """
    )
    
    parser.add_argument(
        "--data_source",
        choices=["mock_ecu", "obd_bridge"],
        help="Data source for telemetry (default: mock_ecu)",
    )
    parser.add_argument(
        "--host",
        help="Host to bind server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port to bind server to (default: 8000)",
    )
    parser.add_argument(
        "--update_rate",
        type=int,
        help="Data update rate in Hz (default: 20)",
    )
    parser.add_argument(
        "--log_level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--config",
        help="Path to TOML configuration file",
    )
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        config = Config.from_toml(args.config)
    else:
        config = Config.from_env()
    
    # Override with CLI arguments
    if args.data_source:
        config.data_source = args.data_source
    if args.host:
        config.host = args.host
    if args.port:
        config.port = args.port
    if args.update_rate:
        config.update_rate = args.update_rate
    if args.log_level:
        config.log_level = args.log_level
    
    # Setup logging
    setup_logging(config.log_level)
    
    # Print configuration
    print("=" * 60)
    print("🏁 Focus ST Telemetry Gateway")
    print("=" * 60)
    print(f"Data Source:  {config.data_source}")
    print(f"Host:         {config.host}")
    print(f"Port:         {config.port}")
    print(f"Update Rate:  {config.update_rate} Hz")
    print(f"Log Level:    {config.log_level}")
    print("=" * 60)
    print(f"\n🌐 Dashboard: http://{config.host if config.host != '0.0.0.0' else 'localhost'}:{config.port}")
    print(f"📡 WebSocket: ws://{config.host if config.host != '0.0.0.0' else 'localhost'}:{config.port}/ws")
    print("\nPress Ctrl+C to stop\n")
    
    # Run the gateway
    try:
        asyncio.run(run_gateway(config))
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
