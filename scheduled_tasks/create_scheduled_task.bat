@echo off
REM ====================================
REM Windows 작업 스케줄러 자동 등록
REM ====================================

echo ========================================
echo Windows 작업 스케줄러 자동 설정
echo ========================================
echo.

REM 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [오류] 관리자 권한이 필요합니다!
    echo.
    echo 해결 방법:
    echo 1. 이 파일을 우클릭
    echo 2. "관리자 권한으로 실행" 선택
    echo.
    pause
    exit /b 1
)

echo [확인] 관리자 권한으로 실행 중...
echo.

REM 기존 작업 삭제 (있는 경우)
schtasks /Query /TN "경매AI주간업데이트" >nul 2>&1
if %errorLevel% equ 0 (
    echo [알림] 기존 작업이 존재합니다. 삭제 중...
    schtasks /Delete /TN "경매AI주간업데이트" /F
    echo.
)

REM 작업 스케줄러 등록
echo [진행] 작업 스케줄러 등록 중...
echo.

schtasks /Create ^
    /TN "경매AI주간업데이트" ^
    /TR "C:\Users\unity\auction_gemini\scheduled_tasks\weekly_update.bat" ^
    /SC WEEKLY ^
    /D SUN ^
    /ST 03:00 ^
    /RU "%USERNAME%" ^
    /RL HIGHEST ^
    /F

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo [성공] 작업 스케줄러 등록 완료!
    echo ========================================
    echo.
    echo 작업 이름: 경매AI주간업데이트
    echo 실행 시간: 매주 일요일 오전 3:00
    echo 실행 파일: weekly_update.bat
    echo.
    echo 확인 방법:
    echo 1. 시작 메뉴 ^> 작업 스케줄러 검색
    echo 2. "경매AI주간업데이트" 작업 확인
    echo.
    echo 즉시 테스트:
    echo   schtasks /Run /TN "경매AI주간업데이트"
    echo.
) else (
    echo.
    echo ========================================
    echo [오류] 작업 등록 실패!
    echo ========================================
    echo.
    echo 오류 코드: %errorLevel%
    echo.
)

pause
