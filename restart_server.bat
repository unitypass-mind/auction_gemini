@echo off
chcp 65001 > nul
echo ========================================
echo 서버 재시작
echo ========================================
echo.
echo psutil 확인 중...
python -c "import psutil" 2>nul
if errorlevel 1 (
    echo psutil이 설치되지 않았습니다.
    echo 설치 중...
    pip install psutil
)
echo.
python restart_server.py
pause
