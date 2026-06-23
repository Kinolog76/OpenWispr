@echo off
REM Build the standalone OpenWispr.exe bundle with PyInstaller.
REM Output: dist\OpenWispr\OpenWispr.exe (run from the repo root).
cd /d "%~dp0.."

if not exist .venv (
    echo Run scripts\run.bat once first to create the environment.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Installing build tools...
pip install pyinstaller >nul

echo Generating icon...
python packaging\make_icon_file.py

echo Building (this takes a few minutes)...
pyinstaller --noconfirm --clean packaging\OpenWispr.spec

echo.
echo ============================================================
echo Build done. Test it:  dist\OpenWispr\OpenWispr.exe
echo Then build the installer:
echo   "%%LOCALAPPDATA%%\Programs\Inno Setup 6\ISCC.exe" packaging\installer.iss
echo ============================================================
pause
