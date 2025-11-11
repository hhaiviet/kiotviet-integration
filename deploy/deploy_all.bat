@echo off
REM KiotViet SSH Setup and Deployment Script

cd /d "%USERPROFILE%\OneDrive - Li & Fung\Documents\kiotviet 248minimart project\kiotviet-integration"

echo.
echo ============================================================
echo KiotViet Integration - Raspberry Pi SSH Setup and Deploy
echo ============================================================
echo.

REM Step 1: SSH Setup
echo [1/3] Setting up SSH key...
python auto_ssh_setup.py

if errorlevel 1 (
    echo.
    echo ERROR: SSH setup failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo [2/3] Preparing for deployment...
echo ============================================================
echo.

REM Step 2: Pre-deployment check
python pre_deploy_check.py

echo.
echo ============================================================
echo [3/3] Starting deployment...
echo ============================================================
echo.

REM Step 3: Deploy
powershell -ExecutionPolicy Bypass -Command ".\Deploy-ToRaspberryPi-Clean.ps1 -Username '0913431718' -Password '68686868' -RetailerId '248minimart' -BranchId '291407'"

if errorlevel 1 (
    echo.
    echo ERROR: Deployment failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo DEPLOYMENT COMPLETED SUCCESSFULLY!
echo ============================================================
echo.
echo You can now monitor the Pi with:
echo   python remote_debug.py status
echo   python remote_debug.py logs --follow
echo.
pause
