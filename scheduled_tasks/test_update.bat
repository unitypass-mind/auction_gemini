@echo off
REM ====================================
REM 주간 자동 업데이트 테스트 (소량)
REM 전체 프로세스를 빠르게 테스트합니다
REM ====================================

cd /d C:\Users\unity\auction_gemini

echo ========================================
echo 자동 업데이트 테스트 시작
echo ========================================

REM 간단한 수집 테스트 (10건만)
echo.
echo [테스트] 소량 데이터 수집 중 (10건)...
python -c "from valueauction_collector import ValueAuctionCollector; collector = ValueAuctionCollector(); stats = collector.collect_and_verify(max_items=10); print(f'수집 완료: {stats[\"total_processed\"]}건')"

REM 구간별 분석
echo.
echo [테스트] 구간별 분석...
python analyze_by_price_range.py

echo.
echo ========================================
echo 테스트 완료!
echo ========================================
echo.
echo 문제가 없다면 weekly_update.bat를 스케줄러에 등록하세요.
echo 가이드: scheduled_tasks\SCHEDULER_SETUP_GUIDE.md
echo.

pause
