@echo off
REM Quick SSH to Raspberry Pi
REM This script enables password-based SSH connection to the Pi

setlocal enabledelayedexpansion

set PI_IP=116.102.136.220
set PI_USER=hhaiviet
set PI_PASS=Hoangviet12
set PI_PROJECT=/home/hhaiviet/kiotviet-integration

echo.
echo ========================================================================
echo Connecting to Raspberry Pi - %PI_USER%@%PI_IP%
echo ========================================================================
echo.

REM Check if sshpass is available
where sshpass >nul 2>&1
if errorlevel 1 (
    echo sshpass not found. Trying with built-in SSH...
    ssh %PI_USER%@%PI_IP%
) else (
    echo Using sshpass for password authentication...
    sshpass -p %PI_PASS% ssh -o StrictHostKeyChecking=no %PI_USER%@%PI_IP%
)

echo.
echo Connection closed.
pause
