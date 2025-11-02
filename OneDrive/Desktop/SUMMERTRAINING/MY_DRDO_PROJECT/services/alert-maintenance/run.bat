@echo off
REM Alert & Maintenance Service Startup Script (Windows)

echo ==================================================
echo   DRDO Alert ^& Maintenance Service
echo ==================================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Warning: Virtual environment not found. Creating...
    python -m venv venv
    echo Virtual environment created
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist "venv\.installed" (
    echo Installing dependencies...
    pip install -r requirements.txt
    type nul > venv\.installed
    echo Dependencies installed
)

REM Check if .env file exists
if not exist ".env" (
    echo Warning: .env file not found. Copying from .env.example...
    copy .env.example .env
    echo .env file created - please update with your credentials
    echo.
    echo IMPORTANT: Update .env with your database and Redis credentials
    echo.
    pause
)

REM Start the service
echo.
echo Starting Alert ^& Maintenance Service...
echo    Port: 8003
echo    Docs: http://localhost:8003/docs
echo.
echo Press Ctrl+C to stop
echo ==================================================
echo.

uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
