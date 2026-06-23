@echo off
REM One-click launcher for OpenWispr on Windows.
REM First run creates a virtual environment and installs dependencies.
cd /d "%~dp0"

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo Python not found. Install Python 3.9+ from https://python.org
        echo and tick "Add python.exe to PATH" during setup.
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat

echo Installing / checking dependencies...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt

echo.
echo Starting OpenWispr...
python flow.py

pause
