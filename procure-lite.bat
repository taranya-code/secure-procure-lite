@echo off
REM =============================================================================
REM SecureProcure Lite — Windows Launcher
REM Usage: procure-lite.bat [start|stop|status|restart|logs|help]
REM =============================================================================

setlocal EnableDelayedExpansion

set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%
set VENV_DIR=%SCRIPT_DIR%\venv
set PID_FILE=%SCRIPT_DIR%\.pids\app.pid
set LOG_FILE=%SCRIPT_DIR%\.logs\app.log
set PORT=5001

if "%1"=="" goto :cmd_help
if /I "%1"=="start"   goto :cmd_start
if /I "%1"=="stop"    goto :cmd_stop
if /I "%1"=="status"  goto :cmd_status
if /I "%1"=="restart" goto :cmd_restart
if /I "%1"=="logs"    goto :cmd_logs
if /I "%1"=="help"    goto :cmd_help
if /I "%1"=="--help"  goto :cmd_help

echo [ERROR] Unknown command: %1
goto :cmd_help

REM =============================================================================
:cmd_start
echo.
echo  ============================================
echo    SecureProcure Lite -- Starting Up
echo  ============================================
echo.

REM Check if already running
if exist "%PID_FILE%" (
    set /p EXISTING_PID=<"%PID_FILE%"
    tasklist /FI "PID eq !EXISTING_PID!" 2>NUL | find /I "python" >NUL 2>&1
    if !errorlevel!==0 (
        echo   [WARN] Already running on PID !EXISTING_PID!
        echo   [INFO] Open http://localhost:%PORT%
        goto :eof
    ) else (
        del "%PID_FILE%" >NUL 2>&1
    )
)

REM Check Python
call :check_python
if errorlevel 1 exit /b 1

REM Create dirs
if not exist "%SCRIPT_DIR%\.pids" mkdir "%SCRIPT_DIR%\.pids"
if not exist "%SCRIPT_DIR%\.logs" mkdir "%SCRIPT_DIR%\.logs"
if not exist "%SCRIPT_DIR%\data"  mkdir "%SCRIPT_DIR%\data"

REM Setup venv
call :setup_venv
if errorlevel 1 exit /b 1

REM Setup DB
call :setup_db
if errorlevel 1 exit /b 1

REM Start server
echo   [->] Starting Flask server...
start /B "" "%VENV_DIR%\Scripts\python.exe" "%SCRIPT_DIR%\run.py" >> "%LOG_FILE%" 2>&1

REM Get PID of the python process just started
timeout /t 2 /nobreak >NUL
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr "PID"') do (
    set SERVER_PID=%%a
)
echo !SERVER_PID!> "%PID_FILE%"
echo   [OK] Server started (PID !SERVER_PID!)

REM Wait for port
echo   [->] Waiting for server to be ready...
set ELAPSED=0
:wait_loop
timeout /t 1 /nobreak >NUL
netstat -an | find ":%PORT% " | find "LISTENING" >NUL 2>&1
if !errorlevel!==0 goto :server_ready
set /a ELAPSED+=1
if !ELAPSED! geq 20 (
    echo   [ERROR] Server did not start. Check %LOG_FILE%
    exit /b 1
)
goto :wait_loop

:server_ready
echo.
echo  ============================================
echo    SecureProcure Lite is READY!
echo  ============================================
echo    App:    http://localhost:%PORT%
echo    Login:  admin@demo.com / password123
echo  --------------------------------------------
echo    Stop:   procure-lite.bat stop
echo    Logs:   procure-lite.bat logs
echo  ============================================
echo.

REM Open browser automatically
start "" "http://localhost:%PORT%"
goto :eof

REM =============================================================================
:cmd_stop
echo.
echo   [->] Stopping SecureProcure Lite...

if exist "%PID_FILE%" (
    set /p KILL_PID=<"%PID_FILE%"
    taskkill /PID !KILL_PID! /F >NUL 2>&1
    del "%PID_FILE%" >NUL 2>&1
    echo   [OK] Server stopped
) else (
    echo   [WARN] No PID file found. Attempting to kill by port...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%"') do (
        taskkill /PID %%a /F >NUL 2>&1
    )
    echo   [OK] Done
)
echo.
goto :eof

REM =============================================================================
:cmd_status
echo.
echo   SecureProcure Lite -- Status
echo   --------------------------------
if exist "%PID_FILE%" (
    set /p STATUS_PID=<"%PID_FILE%"
    tasklist /FI "PID eq !STATUS_PID!" 2>NUL | find /I "python" >NUL 2>&1
    if !errorlevel!==0 (
        echo   Server:  RUNNING  PID=!STATUS_PID!  ^-^>  http://localhost:%PORT%
    ) else (
        echo   Server:  STOPPED  ^(stale PID file^)
    )
) else (
    netstat -an | find ":%PORT% " | find "LISTENING" >NUL 2>&1
    if !errorlevel!==0 (
        echo   Server:  PORT IN USE  ^(port %PORT% occupied by another process^)
    ) else (
        echo   Server:  STOPPED
    )
)
echo.
goto :eof

REM =============================================================================
:cmd_restart
call :cmd_stop
timeout /t 2 /nobreak >NUL
call :cmd_start
goto :eof

REM =============================================================================
:cmd_logs
echo.
echo   App Logs -- Last 50 lines
echo   --------------------------------
if exist "%LOG_FILE%" (
    powershell -Command "Get-Content '%LOG_FILE%' -Tail 50"
) else (
    echo   No log file yet.
)
echo.
goto :eof

REM =============================================================================
:cmd_help
echo.
echo   SecureProcure Lite -- Windows Launcher
echo.
echo   procure-lite.bat start     Start the app (auto-setup on first run)
echo   procure-lite.bat stop      Stop the server
echo   procure-lite.bat restart   Stop then start
echo   procure-lite.bat status    Show running status
echo   procure-lite.bat logs      Show last 50 log lines
echo.
echo   URL:        http://localhost:%PORT%
echo   Demo login: admin@demo.com / password123
echo.
goto :eof

REM =============================================================================
:check_python
python --version >NUL 2>&1
if !errorlevel!==0 (
    echo   [OK] Python found
    exit /b 0
)
python3 --version >NUL 2>&1
if !errorlevel!==0 (
    echo   [OK] Python3 found
    exit /b 0
)
echo.
echo   [ERROR] Python is not installed or not in PATH.
echo.
echo   Please install Python 3.10+ from https://www.python.org/downloads/
echo   IMPORTANT: Check "Add Python to PATH" during installation.
echo.
exit /b 1

REM =============================================================================
:setup_venv
if not exist "%VENV_DIR%" (
    echo   [->] Creating virtual environment...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo   [ERROR] Failed to create virtual environment
        exit /b 1
    )
    echo   [OK] Virtualenv created
)

echo   [->] Installing/checking dependencies...
"%VENV_DIR%\Scripts\pip.exe" install -q -r "%SCRIPT_DIR%\requirements.txt"
if errorlevel 1 (
    echo   [ERROR] pip install failed. Check your internet connection.
    exit /b 1
)
echo   [OK] Dependencies ready
exit /b 0

REM =============================================================================
:setup_db
echo   [->] Initialising database...
"%VENV_DIR%\Scripts\python.exe" -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all(); print('DB ready')" >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo   [ERROR] Database init failed. Check %LOG_FILE%
    exit /b 1
)
echo   [OK] Database ready

echo   [->] Checking demo data...
for /f %%a in ('"%VENV_DIR%\Scripts\python.exe" -c "from app import create_app; from app.models import User; app = create_app(); app.app_context().push(); print(User.query.count())" 2^>NUL') do set USER_COUNT=%%a

if "!USER_COUNT!"=="0" (
    echo   [->] Seeding demo data...
    "%VENV_DIR%\Scripts\python.exe" -c "from app import create_app; from app.seed import seed_demo_data; app = create_app(); app.app_context().push(); seed_demo_data()" >> "%LOG_FILE%" 2>&1
    if errorlevel 1 (
        echo   [WARN] Seed failed. Check %LOG_FILE%
    ) else (
        echo   [OK] Demo data seeded
    )
) else (
    echo   [OK] Database has data (!USER_COUNT! users^)
)
exit /b 0
