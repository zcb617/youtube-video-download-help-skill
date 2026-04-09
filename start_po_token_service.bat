@echo off
echo ========================================
echo  PO Token Provider Service Launcher
echo ========================================
echo.
echo This script starts the PO Token Provider service
echo required for YouTube video downloads.
echo.
echo Prerequisites:
echo   1. Node.js 20+ must be installed
echo   2. PO Token Provider must be cloned
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed!
    echo.
    echo Please install Node.js 20+ from:
    echo   https://nodejs.org/
    echo.
    echo Or use nvm-windows:
    echo   nvm install 24
    echo   nvm use 24
    pause
    exit /b 1
)

REM Check Node.js version
for /f "tokens=1 delims=v." %%a in ('node --version') do set NODE_MAJOR=%%a
if %NODE_MAJOR% LSS 20 (
    echo [WARNING] Node.js version is too old!
    node --version
    echo Required: Node.js 20 or higher
    echo.
    echo Please upgrade Node.js.
    pause
    exit /b 1
)

echo [OK] Node.js version:
node --version
echo.

REM Check if PO Token Provider exists
if not exist "bgutil-ytdlp-pot-provider\server\package.json" (
    echo [INFO] PO Token Provider not found. Cloning now...
    echo.
    git clone --single-branch --branch 1.3.1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git
    if errorlevel 1 (
        echo [ERROR] Failed to clone PO Token Provider!
        echo.
        echo Please clone manually:
        echo   git clone --single-branch --branch 1.3.1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git
        pause
        exit /b 1
    )
    echo [OK] PO Token Provider cloned successfully
echo.
)

echo [OK] PO Token Provider found
echo.
echo Starting service...
echo Service will run on: http://127.0.0.1:4416
echo Press Ctrl+C to stop
echo ========================================
echo.

cd bgutil-ytdlp-pot-provider\server
npm ci && npx tsc && node build\main.js

if errorlevel 1 (
    echo.
    echo [ERROR] Service failed to start!
    echo.
    pause
    exit /b 1
)

pause
