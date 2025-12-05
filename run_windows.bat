@echo off
REM FlacLossless Application Launcher
REM This script starts both backend and frontend, then opens the app in browser

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"
set "BACKEND_LOG=%SCRIPT_DIR%backend.log"
set "FRONTEND_LOG=%SCRIPT_DIR%frontend.log"

echo.
echo ========================================
echo   FlacLossless - Starting Application
echo ========================================
echo.

REM Check if venv exists
if not exist "%VENV_DIR%" (
    echo Error: Virtual environment not found!
    echo Please run the installer first.
    pause
    exit /b 1
)

REM Check if ffmpeg is installed
where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo Warning: ffmpeg not found. Audio conversion may not work.
    echo Download from: https://ffmpeg.org/download.html
    echo.
)

REM Activate venv and start backend
echo Starting backend server...
start "FlacLossless Backend" cmd /k "cd /d "%SCRIPT_DIR%" && call .venv\Scripts\activate.bat && python backend\server.py"

REM Wait a bit for backend to start
timeout /t 3 /nobreak

REM Start frontend
echo Starting frontend development server...
start "FlacLossless Frontend" cmd /k "cd /d "%SCRIPT_DIR%" && npm run dev"

REM Wait for frontend to start
timeout /t 5 /nobreak

REM Open browser
echo Opening application in browser...
start http://localhost:5173

echo.
echo ========================================
echo   Application started!
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:3001
echo ========================================
echo.
echo Close these windows to stop the app.
echo.

pause
