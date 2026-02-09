#!/usr/bin/env python3
"""Setup script for Focus ST Telemetry Gateway"""

import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.11+"""
    if sys.version_info < (3, 11):
        print(f"❌ Python 3.11+ is required. You have {sys.version_info.major}.{sys.version_info.minor}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True


def install_dependencies():
    """Install dependencies from requirements.txt"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False


def create_example_config():
    """Create example config file if it doesn't exist"""
    config_file = Path("config.toml")
    example_file = Path("config.example.toml")
    
    if not config_file.exists() and example_file.exists():
        print("\n📝 Creating config.toml from example...")
        config_file.write_text(example_file.read_text())
        print("✅ config.toml created")
    elif config_file.exists():
        print("\n✅ config.toml already exists")
    else:
        print("\n⚠️  No config file found")


def main():
    """Run setup"""
    print("=" * 60)
    print("🏁 Focus ST Telemetry Gateway - Setup")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Create config
    create_example_config()
    
    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\nTo start the gateway:")
    print("  python main.py --data_source mock_ecu")
    print("\nTo test the WebSocket connection:")
    print("  python test_client.py --duration 5")
    print()


if __name__ == "__main__":
    main()
