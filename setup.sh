#!/bin/bash

# Banking Form Assistant - Setup Script

echo "🏦 Banking Form Assistant - Setup"
echo "=================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your API keys!"
    echo ""
else
    echo "✅ .env file already exists"
    echo ""
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
    echo ""
else
    echo "✅ Virtual environment already exists"
    echo ""
fi

# Activate virtual environment and install dependencies
echo "📦 Installing dependencies..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Mac/Linux
    source venv/bin/activate
fi

pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run: python app.py"
echo "3. Open: http://localhost:5000"
echo ""
echo "📖 For deployment instructions, see DEPLOYMENT.md"
echo ""
