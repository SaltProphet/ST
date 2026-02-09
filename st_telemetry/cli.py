"""Command-line interface for ST Telemetry."""

import asyncio
import logging
import sys
from pathlib import Path

import click
import uvicorn

from st_telemetry.config import get_config, set_config, Config
from st_telemetry.gateway.server import create_gateway

logger = logging.getLogger(__name__)


def setup_logging(level: str):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file (TOML or YAML)",
)
@click.option(
    "--log-level",
    "-l",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False),
    help="Logging level",
)
@click.pass_context
def cli(ctx, config, log_level):
    """Focus ST Telemetry Simulation & Gateway CLI."""
    # Load configuration
    cfg = get_config(config)
    set_config(cfg)
    
    # Setup logging
    if log_level:
        cfg.logging.level = log_level
    setup_logging(cfg.logging.level)
    
    # Store config in context
    ctx.obj = cfg


@cli.command()
@click.option("--host", "-h", help="Host to bind to")
@click.option("--port", "-p", type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.pass_obj
def start(config: Config, host, port, reload):
    """Start the telemetry gateway server."""
    # Override config with CLI options
    if host:
        config.gateway.host = host
    if port:
        config.gateway.port = port
    
    click.echo(f"Starting Focus ST Telemetry Gateway...")
    click.echo(f"Data source: {config.data_source.type}")
    click.echo(f"Server: http://{config.gateway.host}:{config.gateway.port}")
    
    # Create gateway
    gateway = create_gateway(config)
    
    # Create startup and shutdown handlers
    async def startup():
        try:
            await gateway.initialize()
            await gateway.start()
        except Exception as e:
            logger.error(f"Failed to start gateway: {e}")
            raise
    
    async def shutdown():
        try:
            await gateway.shutdown()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    # Add lifespan events
    @gateway.app.on_event("startup")
    async def on_startup():
        await startup()
    
    @gateway.app.on_event("shutdown")
    async def on_shutdown():
        await shutdown()
    
    # Run server
    uvicorn.run(
        gateway.asgi_app,
        host=config.gateway.host,
        port=config.gateway.port,
        reload=reload,
        log_level=config.logging.level.lower(),
    )


@cli.command()
@click.pass_obj
def info(config: Config):
    """Show configuration information."""
    click.echo("Focus ST Telemetry Configuration")
    click.echo("=" * 50)
    click.echo(f"Data Source: {config.data_source.type}")
    click.echo(f"Gateway: {config.gateway.host}:{config.gateway.port}")
    click.echo(f"UI Enabled: {config.ui.enabled}")
    click.echo(f"\nConfigured PIDs ({len(config.get_pids())}):")
    for pid in config.get_pids():
        click.echo(f"  - {pid.name} ({pid.id}): {pid.description}")
        click.echo(f"    Unit: {pid.unit}, Update Rate: {pid.update_rate_hz}Hz")


@cli.command()
@click.argument("pid_name")
@click.option("--count", "-n", type=int, default=10, help="Number of samples to read")
@click.option("--interval", "-i", type=float, default=1.0, help="Interval between samples (seconds)")
@click.pass_obj
def test_pid(config: Config, pid_name, count, interval):
    """Test reading a specific PID."""
    from st_telemetry.data_sources.factory import create_data_source
    
    async def test():
        data_source = create_data_source(config)
        await data_source.initialize()
        
        click.echo(f"Testing PID: {pid_name}")
        click.echo(f"Reading {count} samples at {interval}s intervals")
        click.echo("-" * 50)
        
        for i in range(count):
            data_point = await data_source.read_pid(pid_name)
            if data_point:
                click.echo(
                    f"[{i+1}/{count}] {data_point.pid_name}: "
                    f"Raw={data_point.raw_value:.3f}, "
                    f"Converted={data_point.converted_value:.3f} {data_point.unit}"
                )
                if data_point.warning:
                    click.echo(click.style(f"  WARNING: {data_point.warning}", fg="yellow"))
            else:
                click.echo(f"[{i+1}/{count}] Failed to read PID", err=True)
            
            if i < count - 1:
                await asyncio.sleep(interval)
        
        await data_source.shutdown()
    
    asyncio.run(test())


@cli.command()
@click.pass_obj
def validate_config(config: Config):
    """Validate the configuration file."""
    click.echo("Validating configuration...")
    
    errors = []
    warnings = []
    
    # Check data source
    if config.data_source.type not in ["mock_ecu", "obd_bridge"]:
        errors.append(f"Invalid data source type: {config.data_source.type}")
    
    # Check PIDs
    if not config.get_pids():
        errors.append("No PIDs configured")
    
    # Check UI paths
    if config.ui.enabled:
        templates_path = Path(config.ui.templates_dir)
        if not templates_path.exists():
            warnings.append(f"Templates directory not found: {templates_path}")
        
        static_path = Path(config.ui.static_dir)
        if not static_path.exists():
            warnings.append(f"Static directory not found: {static_path}")
    
    # Report results
    if errors:
        click.echo(click.style("\nErrors:", fg="red"))
        for error in errors:
            click.echo(click.style(f"  ✗ {error}", fg="red"))
    
    if warnings:
        click.echo(click.style("\nWarnings:", fg="yellow"))
        for warning in warnings:
            click.echo(click.style(f"  ! {warning}", fg="yellow"))
    
    if not errors and not warnings:
        click.echo(click.style("✓ Configuration is valid!", fg="green"))
    elif not errors:
        click.echo(click.style("\n✓ Configuration is valid (with warnings)", fg="green"))
    else:
        click.echo(click.style(f"\n✗ Configuration has {len(errors)} error(s)", fg="red"))
        sys.exit(1)


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
