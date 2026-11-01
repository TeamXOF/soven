@echo off
setlocal EnableDelayedExpansion
title SOVEN - Launcher
echo ==========================================================
echo    SOVEN - Smart Launcher
echo ==========================================================
set ROOT=%~dp0

:: ── Step 0: check Python and Node exist ─────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.12 from https://python.org
    echo         IMPORTANT: tick "Add Python to PATH" during install.
    pause & exit /b 1
)
where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Install Node.js 20+ LTS from https://nodejs.org
    pause & exit /b 1
)
echo [OK] Python and Node.js found.

:: ── Step 1: check API keys (.env) ───────────────────────────────────────────
if not exist "%ROOT%backend\.env" (
    echo.
    echo [SETUP NEEDED] backend\.env was not found.
    echo   1^) Open the backend folder
    echo   2^) Copy .env.example and rename the copy to .env
    echo      ^(in Command Prompt:  copy .env.example .env^)
    echo   3^) Fill in optional provider keys, or prepare local speech recognition:
    echo        GOOGLE_API_KEYS  -  free key: https://aistudio.google.com/apikey
    echo        GROQ_API_KEY     -  free key: https://console.groq.com/keys
    echo   4^) Save it, then run this launcher again.
    echo.
    choice /C YN /M "Create .env from the template now so you only fill in keys? [Y/N]"
    if errorlevel 2 exit /b 0
    copy "%ROOT%backend\.env.example" "%ROOT%backend\.env" >nul
    notepad "%ROOT%backend\.env"
    echo Save .env, then run start_soven.bat again.
    pause & exit /b 0
)
echo [OK] Environment file found. Cloud reasoning is optional.

:: ── Step 2: backend dependencies ────────────────────────────────────────────
set "PYTHON_EXE=%ROOT%backend\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    python -m venv "%ROOT%backend\.venv"
    if errorlevel 1 (
        pause
        exit /b 1
    )
)
echo [SETUP] Checking backend dependencies...
"%PYTHON_EXE%" -m pip install --disable-pip-version-check -r "%ROOT%backend\requirements.txt"
if errorlevel 1 (
    echo [ERROR] Dependency setup failed. Use Python 3.12 and check your connection.
    pause & exit /b 1
)
"%PYTHON_EXE%" "%ROOT%backend\scripts\bootstrap_teacher.py" --check
if errorlevel 1 (
    echo [SETUP] Create or reset the teacher administrator password.
    "%PYTHON_EXE%" "%ROOT%backend\scripts\bootstrap_teacher.py" --username teacher
    if errorlevel 1 (
        pause
        exit /b 1
    )
)
echo [OK] Backend dependencies ready.

:: ── Step 3: frontend dependencies + build ───────────────────────────────────
if not exist "%ROOT%frontend\node_modules" (
    echo [SETUP] Installing frontend packages ^(first run only, a few minutes^)...
    cd /d "%ROOT%frontend" && call npm ci
    if errorlevel 1 (
        echo [ERROR] npm install failed. Check your internet connection and try again.
        pause & exit /b 1
    )
)
if exist "%ROOT%frontend\package.json" (
    echo [SETUP] Building the current frontend...
    cd /d "%ROOT%frontend" && call npm run build -- --webpack
    if errorlevel 1 (
        echo [ERROR] Frontend build failed.
        pause & exit /b 1
    )
)
echo [OK] Frontend ready.

:: ── Step 4: launch both servers ─────────────────────────────────────────────
echo.
echo Launching SOVEN...
cd /d "%ROOT%backend"
start "SOVEN Backend" cmd /k ""%PYTHON_EXE%" -m uvicorn main:app --port 8000"
cd /d "%ROOT%frontend"
start "SOVEN Frontend" cmd /k "npm start"
cd /d "%ROOT%"

echo.
echo Both servers are starting up!
echo   Frontend:        http://localhost:3000
echo   Teacher login:   use your configured username and password
echo   Story Mode:      http://localhost:3000/read
echo Wait ~10 seconds, then open http://localhost:3000
echo.
echo Dependencies and the current frontend are checked on each launch.
echo Keep backend\.env, the classroom database and backups private.
pause
