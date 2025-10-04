@echo off
REM Toolflock Development Setup Script for Windows
echo 🚀 Setting up Toolflock development environment...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.12 or later.
    pause
    exit /b 1
)

REM Check Python version
echo ✅ Python version:
python --version

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
pip install --upgrade pip

REM Install requirements
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Copy .env.example to .env if .env doesn't exist
if not exist ".env" (
    echo ⚙️  Creating .env file from template...
    copy .env.example .env
    echo 📝 Please edit .env file with your actual configuration values.
)

REM Create directories
if not exist "uploads" mkdir uploads
if not exist "static\uploads" mkdir static\uploads

echo.
echo ✅ Setup complete! Run the following commands to start development:
echo    venv\Scripts\activate.bat
echo    python app.py
echo.
echo 🌐 Your app will be available at: http://localhost:5000
pause