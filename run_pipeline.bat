@echo off
chcp 65001 > nul
echo ========================================
echo 자동 재학습 파이프라인 실행
echo ========================================
echo.
python auto_pipeline.py %*
pause
