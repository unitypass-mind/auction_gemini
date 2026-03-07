@echo off
REM ====================================
REM 주간 자동 데이터 수집 및 모델 재학습
REM ====================================

cd /d C:\Users\unity\auction_gemini

echo ========================================
echo 주간 자동 업데이트 시작
echo 실행 시각: %date% %time%
echo ========================================

REM 1단계: 주간 데이터 수집 (100건)
echo.
echo [1/4] 신규 데이터 수집 중...
python auto_weekly_collect.py
if errorlevel 1 (
    echo 오류: 데이터 수집 실패
    exit /b 1
)

REM 2단계: 이상치 제거
echo.
echo [2/4] 이상치 제거 중...
python fix_outliers_safe.py

REM 3단계: 모델 재학습 (XGBoost 고도화 모델)
echo.
echo [3/4] 모델 재학습 중...
python train_model_enhanced.py
if errorlevel 1 (
    echo 오류: 모델 학습 실패
    exit /b 1
)

REM XGBoost를 메인 모델로 설정
copy /Y models\backup_XGBoost.pkl models\auction_model_v2.pkl

REM 4단계: 전체 재예측
echo.
echo [4/4] 전체 재예측 중...
python update_predictions_v2.py
if errorlevel 1 (
    echo 오류: 재예측 실패
    exit /b 1
)

REM 5단계: 구간별 분석
echo.
echo [5/5] 구간별 분석 중...
python analyze_by_price_range.py

echo.
echo ========================================
echo 주간 자동 업데이트 완료!
echo 완료 시각: %date% %time%
echo ========================================

REM 로그 파일 저장
echo 완료: %date% %time% >> logs\weekly_update_log.txt
