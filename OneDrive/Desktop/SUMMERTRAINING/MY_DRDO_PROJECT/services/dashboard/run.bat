@echo off
REM Dashboard Service Startup Script (Windows)

echo ==================================================
echo   DRDO Dashboard Service
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
    echo .env file created
    echo.
    echo IMPORTANT: Update .env with your microservice URLs
    echo.
    pause
)

REM Start the dashboard
echo.
echo Starting Dashboard Service...
echo    Port: 8004
echo    URL: http://localhost:8004
echo.
echo Press Ctrl+C to stop
echo ==================================================
echo.

streamlit run app\main.py --server.port=8004
