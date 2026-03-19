@echo off
echo Starting NEOS development server...

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Change to agent directory
cd agent

REM Start development server
echo Starting server on http://localhost:8000/dashboard
python -m neos_agent.main --dev

pause
