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

REM Install the same project contract used by Docker/Railway
echo Installing agent dependencies...
uv pip install --python .venv\Scripts\python.exe -e "agent[dev]"

REM Create .env file if it doesn't exist
if not exist "agent\.env" (
    echo Creating .env file...
    copy agent\.env.example agent\.env
    echo Please edit agent\.env and add your OPENROUTER_KEY
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
echo   1. Edit agent\.env and add your OPENROUTER_KEY
echo   2. Run: start-dev.bat
echo.
echo The dashboard will be available at: http://localhost:8000/dashboard
pause
