@echo off
chcp 65001 > nul
echo ========================================
echo 자동화 스케줄러 시작
echo ========================================
echo.
echo APScheduler 확인 중...
python -c "import apscheduler" 2>nul
if errorlevel 1 (
    echo APScheduler가 설치되지 않았습니다.
    echo 설치 중...
    pip install apscheduler
)
echo.
echo 스케줄러 시작...
python scheduler.py
pause
