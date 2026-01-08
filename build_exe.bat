@echo off
set VENV_DIR=venv

:: Check if venv exists, if not, create it
if not exist %VENV_DIR% (
    echo Virtual environment not found. Running setup...
    call setup_env.bat
)

echo Activating Virtual Environment...
call %VENV_DIR%\Scripts\activate

echo Building JARVIS v1.0.0...
echo Using JarvisInvoice.spec for professional configuration...

:: Clean previous dist
if exist dist rmdir /s /q dist

:: Run PyInstaller using the .spec file
pyinstaller --clean JarvisInvoice.spec

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo Build Successful!
    echo Final Executable: dist\Jarvis Invoice Intelligence\Jarvis Invoice Intelligence.exe
    echo ========================================================
) else (
    echo.
    echo Build Failed!
)
pause
