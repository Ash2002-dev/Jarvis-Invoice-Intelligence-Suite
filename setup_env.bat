@echo off
set VENV_DIR=venv

echo Creating Virtual Environment...
py -m venv %VENV_DIR%

echo Activating Virtual Environment...
call %VENV_DIR%\Scripts\activate

echo Installing Dependencies...
pip install -r requirements.txt

echo Environment setup complete.
pause
