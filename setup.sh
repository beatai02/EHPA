#!/bin/bash
# EHPA Task 1 Setup Script
# Quick setup for development environment

set -e

echo "======================================"
echo "  EHPA Task 1 - Setup Script"
echo "======================================"
echo ""

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "⚠️  Warning: This script is designed for Linux (Kali recommended)"
    echo "   Some features may not work on other systems"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Python version
echo "🔍 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Found Python $PYTHON_VERSION"

# Check for pentesting tools
echo ""
echo "🔍 Checking pentesting tools..."
MISSING_TOOLS=()

for tool in nmap nikto sqlmap gobuster; do
    if command -v $tool &> /dev/null; then
        echo "✅ $tool found"
    else
        echo "❌ $tool not found"
        MISSING_TOOLS+=($tool)
    fi
done

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  Missing tools: ${MISSING_TOOLS[*]}"
    echo "   Install with: sudo apt install ${MISSING_TOOLS[*]}"
    read -p "Continue setup anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  venv directory already exists"
    read -p "Recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
    fi
else
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Check if .env exists
echo ""
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found"
    echo "📝 Please configure .env file:"
    echo "   1. Add your Anthropic API key"
    echo "   2. Configure allowed targets"
    echo ""
    read -p "Press Enter to continue..."
else
    echo "✅ .env file found"

    # Check if API key is set
    if grep -q "your_api_key_here" .env; then
        echo "⚠️  WARNING: Anthropic API key not configured in .env"
        echo "   Edit .env and add your API key"
    fi
fi

# Create necessary directories
echo ""
echo "📁 Creating data directories..."
mkdir -p data/sessions data/findings data/reports logs

# Test imports
echo ""
echo "🧪 Testing Python imports..."
python3 -c "
try:
    import anthropic
    import fastapi
    import uvicorn
    import pydantic
    print('✅ All core dependencies imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

echo ""
echo "======================================"
echo "  ✅ Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Configure .env file with your Anthropic API key"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Start server: python3 main.py"
echo "4. Access API docs: http://localhost:8000/api/docs"
echo ""
echo "Happy hacking! 🎯"
