@echo off
setlocal enabledelayedexpansion

echo.
echo ======================================
echo   GestFlow Setup for Windows
echo ======================================
echo.

:: ── Check Python ──
python --version > nul 2>&1
if errorlevel 1 (
    echo  ❌ Python not found
    echo  Download from: https://python.org
    echo  Make sure to check "Add Python to PATH"
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYVER=%%i
echo  ✅ %PYVER% found

:: ── Navigate to repo root ──
set SCRIPT_DIR=%~dp0
set REPO_DIR=%SCRIPT_DIR%..
cd /d "%REPO_DIR%"

echo  ✅ Repo: %REPO_DIR%

:: ── Create virtual environment ──
if not exist ".venv" (
    echo.
    echo  Creating virtual environment...
    python -m venv .venv
    echo  ✅ Virtual environment created
)

:: ── Activate virtual environment ──
call .venv\Scripts\activate.bat
echo  ✅ Virtual environment activated

:: ── Upgrade pip ──
python -m pip install --upgrade pip --quiet

:: ── Run Python installer ──
echo.
python installer\setup.py

echo.
echo ======================================
echo  ✅ GestFlow setup complete!
echo.
echo  To start GestFlow:
echo  cd gestflow\gestflow_02_content_engine
echo  python main.py
echo ======================================
echo.
pause