@echo off
REM ==============================================================================
REM  BruteShield - Windows Production Startup Script
REM ==============================================================================

echo [BruteShield] Initializing production launcher...

IF EXIST "venv\Scripts\activate.bat" (
    echo [BruteShield] Activating Python virtual environment...
    call venv\Scripts\activate.bat
) ELSE (
    echo [!] Warning: venv\Scripts\activate.bat not found. Using system Python.
)

REM Verify Waitress is available
python -c "import waitress" >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [!] Waitress WSGI server not installed in current environment.
    echo [*] Installing requirements...
    pip install -r requirements.txt
)

echo [*] Starting BruteShield Production WSGI Server (Waitress)...
python wsgi.py
