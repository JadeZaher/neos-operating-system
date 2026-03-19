@echo off
echo Setting up NEOS development environment on Windows...

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install agent package in development mode
echo Installing agent package...
cd agent
pip install -e ".[dev]"
cd ..

REM Install LiteLLM for local LLM support
echo Installing LiteLLM for local LLM support...
.venv\Scripts\pip install litellm

REM Create .env file if it doesn't exist
if not exist "agent\.env" (
    echo Creating .env file...
    copy agent\.env.example agent\.env
    echo Please edit agent\.env and add your ANTHROPIC_API_KEY
)

REM Initialize database (SQLite)
echo Initializing database...
cd agent
python -m scripts.seed_omnione
cd ..

echo.
echo Setup complete!
echo.
echo To start the development server:
echo   1. Edit agent\.env and add your ANTHROPIC_API_KEY
echo   2. Run: start-dev.bat
echo.
echo The dashboard will be available at: http://localhost:8000/dashboard
pause
