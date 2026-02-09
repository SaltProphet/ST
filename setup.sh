#!/bin/bash
# Setup script for Focus ST Telemetry System

set -e

echo "🏎️  Focus ST Telemetry System Setup"
echo "===================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.12 or higher."
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  Please edit .env file to configure your settings"
else
    echo ""
    echo "✓ .env file already exists"
fi

# Create templates directory if it doesn't exist
mkdir -p templates

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start using the system:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Configure settings in .env file"
echo "  3. Run the server: python app.py"
echo "  4. Open browser: http://localhost:8000"
echo ""
echo "For CLI usage: python cli.py --help"
echo "To run tests: pytest test_telemetry.py"
echo ""
echo "Default admin credentials:"
echo "  Username: admin"
echo "  Password: admin"
echo "  ⚠️  Change these immediately in production!"
echo ""
