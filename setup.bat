@echo off
REM Banking Form Assistant - Setup Script for Windows

echo 🏦 Banking Form Assistant - Setup
echo ==================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo ✅ Python found
python --version
echo.

REM Check if .env file exists
if not exist .env (
    echo 📝 Creating .env file from .env.example...
    copy .env.example .env
    echo ⚠️  Please edit .env file and add your API keys!
    echo.
) else (
    echo ✅ .env file already exists
    echo.
)

REM Create virtual environment
if not exist venv (
    echo 🔧 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
    echo.
) else (
    echo ✅ Virtual environment already exists
    echo.
)

REM Activate virtual environment and install dependencies
echo 📦 Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo ✅ Setup complete!
echo.
echo 📋 Next steps:
echo 1. Edit .env file with your API keys
echo 2. Run: python app.py
echo 3. Open: http://localhost:5000
echo.
echo 📖 For deployment instructions, see DEPLOYMENT.md
echo.
pause
