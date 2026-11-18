@echo off
REM =========================================================================
REM  BruteShield — Windows Production Launcher
REM =========================================================================
REM  This script validates the local environment and starts the production
REM  WSGI server (Waitress).  It does NOT deploy the application to any
REM  remote server or cloud service.
REM
REM  Default binding: 127.0.0.1:5000  (localhost only)
REM =========================================================================

setlocal enabledelayedexpansion

REM --- 1. Check Python ---
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [FATAL] Python is not on the PATH.
    echo         Install Python 3.10+ and ensure it is accessible.
    exit /b 1
)

REM --- 2. Check virtual environment ---
if not exist "venv\Scripts\activate.bat" (
    echo [FATAL] Virtual environment not found at venv\Scripts\activate.bat.
    echo         Create one with:  python -m venv venv
    exit /b 1
)
call venv\Scripts\activate.bat

REM --- 3. Check Waitress ---
python -c "import waitress" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [FATAL] The 'waitress' package is not installed.
    echo         Install requirements:  pip install -r requirements.txt
    exit /b 1
)

REM --- 4. Check database directory ---
if not exist "logs" (
    echo [INFO] Creating logs\ directory for database storage...
    mkdir logs
)

REM --- 5. Check ML model file ---
if not exist "trained_model.pkl" (
    echo [WARN] ML model file trained_model.pkl not found.
    echo        The application will start but ML scoring will be unavailable.
)

REM --- 6. Warn about demo secrets in production ---
if defined BRUTESHIELD_ENV (
    if /i "!BRUTESHIELD_ENV!"=="production" (
        if not defined BRUTESHIELD_SECRET_KEY (
            echo [FATAL] BRUTESHIELD_ENV is 'production' but BRUTESHIELD_SECRET_KEY is not set.
            echo         Set a cryptographically random secret before starting production.
            exit /b 1
        )
        if not defined BRUTESHIELD_VAULT_KEY (
            echo [FATAL] BRUTESHIELD_ENV is 'production' but BRUTESHIELD_VAULT_KEY is not set.
            echo         Set a 32-byte vault key before starting production.
            exit /b 1
        )
    )
)

echo.
echo =========================================================================
echo  BruteShield — Starting Production WSGI Server
echo  Binding : %BRUTESHIELD_HOST%:%BRUTESHIELD_PORT%  (default 127.0.0.1:5000)
echo =========================================================================
echo.

python wsgi.py
