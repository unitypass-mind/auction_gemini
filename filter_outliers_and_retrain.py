"""
이상치 필터링 및 모델 재학습 스크립트

목표: 극단적 저가 낙찰 등 이상치를 제거하여 모델 정확도 향상
"""
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import json

# 설정
DB_PATH = "data/predictions.db"
OUTPUT_MODEL_PATH = "xgboost_auction_model_v5.json"
BACKUP_MODEL_PATH = "xgboost_auction_model_v4_backup.json"

print("=" * 80)
print("이상치 필터링 및 모델 재학습 시작")
print("=" * 80)

# 1. 데이터 로드
print("\n[1/6] 데이터 로드 중...")
conn = sqlite3.connect(DB_PATH)

query = """
SELECT
    감정가,
    물건종류,
    지역,
    면적,
    경매회차,
    입찰자수,
    actual_price,
    predicted_price,
    error_rate,
    ROUND((actual_price * 100.0 / 감정가), 2) as 낙찰률
FROM predictions
WHERE verified = 1
  AND actual_price IS NOT NULL
  AND actual_price > 0
  AND 감정가 > 0
"""

df = pd.read_sql_query(query, conn)
conn.close()

print(f"전체 데이터: {len(df)}건")

# 2. 이상치 필터링
print("\n[2/6] 이상치 필터링 중...")

# 필터링 전 통계
print(f"\n필터링 전:")
print(f"  평균 낙찰률: {df['낙찰률'].mean():.2f}%")
print(f"  중앙값 낙찰률: {df['낙찰률'].median():.2f}%")

# 필터링 조건 적용
df_clean = df[
    # 극단적 저가 제외 (40% 미만)
    (df['낙찰률'] >= 40) &
    # 비현실적 고가 제외 (150% 초과)
    (df['낙찰률'] <= 150) &
    # 경매회차 5회 이상 제외
    (df['경매회차'] < 5) &
    # 초소액 물건 제외 (500만원 미만)
    (df['감정가'] >= 5000000) &
    # 예측 오차 100% 이상 제외
    (df['error_rate'] < 100)
].copy()

removed_count = len(df) - len(df_clean)
removed_pct = (removed_count / len(df)) * 100

print(f"\n필터링 후:")
print(f"  제거된 데이터: {removed_count}건 ({removed_pct:.1f}%)")
print(f"  남은 데이터: {len(df_clean)}건")
print(f"  평균 낙찰률: {df_clean['낙찰률'].mean():.2f}%")
print(f"  중앙값 낙찰률: {df_clean['낙찰률'].median():.2f}%")

if len(df_clean) < 100:
    print("\n⚠️  경고: 필터링 후 데이터가 너무 적습니다. 필터 조건을 완화하세요.")
    exit(1)

# 3. IQR 기반 추가 필터링 (선택적)
print("\n[3/6] IQR 기반 이상치 검출...")
Q1 = df_clean['낙찰률'].quantile(0.25)
Q3 = df_clean['낙찰률'].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

print(f"  Q1 (25%): {Q1:.2f}%")
print(f"  Q3 (75%): {Q3:.2f}%")
print(f"  IQR: {IQR:.2f}%")
print(f"  하한: {lower_bound:.2f}%, 상한: {upper_bound:.2f}%")

df_iqr = df_clean[
    (df_clean['낙찰률'] >= lower_bound) &
    (df_clean['낙찰률'] <= upper_bound)
].copy()

iqr_removed = len(df_clean) - len(df_iqr)
print(f"  IQR 필터링으로 추가 제거: {iqr_removed}건")

# 최종 데이터 선택 (IQR 필터링 적용 여부 결정)
if len(df_iqr) >= 500:  # 충분한 데이터가 남아있으면 IQR 적용
    df_final = df_iqr
    print(f"  [OK] IQR 필터링 적용 (최종 {len(df_final)}건)")
else:
    df_final = df_clean
    print(f"  [OK] IQR 필터링 생략 (최종 {len(df_final)}건)")

# 4. 모델 학습용 데이터 준비
print("\n[4/6] 모델 학습용 데이터 준비 중...")

# 필요한 특성만 선택
X = df_final[['감정가', '물건종류', '지역', '면적', '경매회차', '입찰자수']].copy()
y = df_final['actual_price'].values

# 결측치 처리
X['면적'].fillna(X['면적'].median(), inplace=True)
X['입찰자수'].fillna(0, inplace=True)
X['물건종류'].fillna('기타', inplace=True)
X['지역'].fillna('기타', inplace=True)

# 카테고리 인코딩
le_property = LabelEncoder()
le_region = LabelEncoder()

X['물건종류_encoded'] = le_property.fit_transform(X['물건종류'])
X['지역_encoded'] = le_region.fit_transform(X['지역'])

# 최종 특성 선택
X_final = X[['감정가', '면적', '경매회차', '입찰자수', '물건종류_encoded', '지역_encoded']].values

print(f"  학습 데이터: {len(X_final)}건, {X_final.shape[1]}개 특성")

# Train/Test 분할
X_train, X_test, y_train, y_test = train_test_split(
    X_final, y, test_size=0.2, random_state=42
)

print(f"  Train: {len(X_train)}건, Test: {len(X_test)}건")

# 5. 모델 학습
print("\n[5/6] XGBoost 모델 학습 중...")

# 기존 모델 백업
import shutil
if Path("xgboost_auction_model.json").exists():
    shutil.copy("xgboost_auction_model.json", BACKUP_MODEL_PATH)
    print(f"  [OK] 기존 모델 백업: {BACKUP_MODEL_PATH}")

# 모델 학습
model = XGBRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=8,
    min_child_weight=3,
    gamma=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    objective='reg:squarederror'
)

model.fit(X_train, y_train)
print("  [OK] 모델 학습 완료")

# 6. 모델 평가
print("\n[6/6] 모델 성능 평가...")

y_pred = model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

# 오차율 계산
error_rates = np.abs((y_test - y_pred) / y_test) * 100
avg_error_rate = np.mean(error_rates)
median_error_rate = np.median(error_rates)

print("\n" + "=" * 80)
print("모델 성능 지표")
print("=" * 80)
print(f"MAE (평균 절대 오차): {mae:,.0f}원")
print(f"R² Score: {r2:.4f}")
print(f"평균 오차율: {avg_error_rate:.2f}%")
print(f"중앙값 오차율: {median_error_rate:.2f}%")

# 기존 모델과 비교
print("\n[성능 비교]")
print(f"필터링 전 평균 오차율: 16.41%")
print(f"필터링 후 평균 오차율: {avg_error_rate:.2f}%")
print(f"개선율: {16.41 - avg_error_rate:.2f}%p")

# 7. 모델 저장
model.save_model(OUTPUT_MODEL_PATH)
print(f"\n[OK] 새 모델 저장: {OUTPUT_MODEL_PATH}")

# 인코더 저장
encoders = {
    'property_encoder': le_property,
    'region_encoder': le_region
}
joblib.dump(encoders, 'encoders_v5.pkl')
print(f"[OK] 인코더 저장: encoders_v5.pkl")

# 모델 메타데이터 저장
metadata = {
    'version': 'v5',
    'features': X_final.shape[1],
    'trained_samples': len(df_final),
    'filtered_from': len(df),
    'removed_outliers': removed_count,
    'mae': float(mae),
    'r2': float(r2),
    'avg_error_rate': float(avg_error_rate),
    'median_error_rate': float(median_error_rate),
    'filter_criteria': {
        '낙찰률_최소': 40,
        '낙찰률_최대': 150,
        '경매회차_최대': 4,
        '최소금액': 5000000,
        '최대오차율': 100
    }
}

with open('model_metadata_v5.json', 'w', encoding='utf-8') as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

print(f"[OK] 메타데이터 저장: model_metadata_v5.json")

print("\n" + "=" * 80)
print("[SUCCESS] 이상치 필터링 및 모델 재학습 완료!")
print("=" * 80)
print(f"\n다음 단계:")
print(f"1. 서버 코드에서 모델 파일 경로를 '{OUTPUT_MODEL_PATH}'로 변경")
print(f"2. 서버 재시작")
print(f"3. 앱에서 새로운 정확도 확인")
