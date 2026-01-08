@echo off
set VENV_DIR=venv

if not exist %VENV_DIR% (
    echo Virtual environment not found. Please run setup_env.bat first.
    pause
    exit /b
)

echo Starting Jarvis v1.0.0...
call %VENV_DIR%\Scripts\activate
python -m src.app
pause
