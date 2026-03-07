@echo off
chcp 65001 >nul
cd /d %~dp0

echo.
echo Creating scheduled task...
echo.

schtasks /Create /TN "AuctionAI_Weekly_Update" /TR "%~dp0weekly_update.bat" /SC WEEKLY /D SUN /ST 03:00 /RL HIGHEST /F

if %errorLevel% equ 0 (
    echo.
    echo SUCCESS! Task created.
    echo Task Name: AuctionAI_Weekly_Update
    echo Schedule: Every Sunday at 3:00 AM
    echo.
    echo To test immediately:
    echo   schtasks /Run /TN "AuctionAI_Weekly_Update"
    echo.
) else (
    echo.
    echo FAILED! Error code: %errorLevel%
    echo.
    echo Please run this file as Administrator:
    echo 1. Right-click this file
    echo 2. Select "Run as administrator"
    echo.
)

pause
