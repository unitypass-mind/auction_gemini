@echo off
REM ====================================
REM 작업 스케줄러 등록 (CMD 버전)
REM 이 파일을 우클릭 -> "관리자 권한으로 실행"
REM ====================================

echo.
echo ========================================
echo 작업 스케줄러 등록 중...
echo ========================================
echo.

REM 기존 작업 삭제 (있는 경우)
schtasks /Query /TN "AuctionAI_Weekly_Update" >nul 2>&1
if %errorLevel% equ 0 (
    echo 기존 작업 삭제 중...
    schtasks /Delete /TN "AuctionAI_Weekly_Update" /F >nul 2>&1
)

REM 작업 생성
schtasks /Create ^
  /TN "AuctionAI_Weekly_Update" ^
  /TR "C:\Users\unity\auction_gemini\scheduled_tasks\weekly_update.bat" ^
  /SC WEEKLY ^
  /D SUN ^
  /ST 03:00 ^
  /RL HIGHEST ^
  /F

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo 성공! 작업이 등록되었습니다.
    echo ========================================
    echo.
    echo 작업 이름: AuctionAI_Weekly_Update
    echo 실행 시간: 매주 일요일 오전 3:00
    echo.
    echo 작업 확인:
    echo   schtasks /Query /TN "AuctionAI_Weekly_Update"
    echo.
    echo 즉시 실행 테스트:
    echo   schtasks /Run /TN "AuctionAI_Weekly_Update"
    echo.

    REM 작업 정보 표시
    echo 등록된 작업 상세 정보:
    echo.
    schtasks /Query /TN "AuctionAI_Weekly_Update" /V /FO LIST
) else (
    echo.
    echo ========================================
    echo 실패! 작업 등록에 실패했습니다.
    echo ========================================
    echo.
    echo 오류 코드: %errorLevel%
    echo.
    echo 해결 방법:
    echo 1. 이 파일을 우클릭
    echo 2. "관리자 권한으로 실행" 선택
    echo 3. 사용자 계정 컨트롤(UAC) 팝업에서 "예" 클릭
    echo.
)

echo.
pause
