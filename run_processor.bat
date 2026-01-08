@echo off
set VENV_DIR=venv

if not exist %VENV_DIR% (
    echo Virtual environment not found. Please run setup_env.bat first.
    pause
    exit /b
)

echo Starting Jarvis Processor...
call %VENV_DIR%\Scripts\activate
python -m src.main
pause
