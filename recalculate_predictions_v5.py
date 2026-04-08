"""
v5 모델로 기존 검증 데이터 재예측 스크립트

- verified=1 인 레코드(실제 낙찰가 있는 것)를 v5 모델로 재예측
- predicted_price, error_amount, error_rate 업데이트
- 통계화면에 v5 실제 성능이 반영됨
"""
import sqlite3
import numpy as np
import joblib
from pathlib import Path

DB_PATH = Path("data/predictions.db")
MODEL_PATH = Path("models/auction_model_v5.pkl")
ENCODERS_PATH = Path("encoders_v5.pkl")

print("=" * 60)
print("v5 모델 재예측 시작")
print("=" * 60)

# 모델 & 인코더 로드
print("\n[1/4] 모델 및 인코더 로드...")
model = joblib.load(MODEL_PATH)
encoders = joblib.load(ENCODERS_PATH)
le_property = encoders['property_encoder']
le_region = encoders['region_encoder']
print(f"  물건종류 클래스: {len(le_property.classes_)}개")
print(f"  지역 클래스: {len(le_region.classes_)}개")

# 검증 데이터 조회
print("\n[2/4] 검증 데이터 조회...")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
    SELECT id, case_no, 감정가, 물건종류, 지역, 면적, 경매회차, 입찰자수, actual_price
    FROM predictions
    WHERE verified = 1
      AND actual_price IS NOT NULL
      AND actual_price > 0
      AND 감정가 IS NOT NULL
      AND 감정가 > 0
    ORDER BY id
""")
rows = cursor.fetchall()
print(f"  대상 레코드: {len(rows)}건")

# 재예측
print("\n[3/4] v5 모델로 재예측 중...")

known_properties = set(le_property.classes_)
known_regions = set(le_region.classes_)

updated = 0
skipped = 0
errors = []

for row in rows:
    try:
        # 피처 준비
        appraised = float(row['감정가'] or 0)
        area = float(row['면적'] or 0) or 85.0
        round_num = int(row['경매회차'] or 1)
        bidders = int(row['입찰자수'] or 0)
        prop_type = str(row['물건종류'] or '기타')
        region = str(row['지역'] or '기타')
        actual_price = int(row['actual_price'])

        if appraised <= 0 or actual_price <= 0:
            skipped += 1
            continue

        # 인코딩 (미지 클래스는 '기타'로 대체)
        prop_encoded = le_property.transform([prop_type if prop_type in known_properties else '기타'])[0]
        region_encoded = le_region.transform([region if region in known_regions else '기타'])[0]

        # 예측
        X = np.array([[appraised, area, round_num, bidders, prop_encoded, region_encoded]])
        predicted = int(model.predict(X)[0])

        # 오차 계산
        error_amount = abs(actual_price - predicted)
        error_rate = round(error_amount / actual_price * 100, 2)

        # DB 업데이트
        cursor.execute("""
            UPDATE predictions
            SET predicted_price = ?,
                error_amount = ?,
                error_rate = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (predicted, error_amount, error_rate, row['id']))
        updated += 1

    except Exception as e:
        skipped += 1
        errors.append(f"id={row['id']}: {e}")

conn.commit()

# 결과 확인
print(f"\n  업데이트: {updated}건")
print(f"  스킵: {skipped}건")
if errors[:5]:
    print(f"  오류 샘플: {errors[:5]}")

# 재예측 후 통계 확인
print("\n[4/4] 재예측 후 통계 확인...")
cursor.execute("""
    SELECT
        COUNT(*) as cnt,
        AVG(CASE WHEN error_rate <= 100 THEN error_rate END) as avg_err,
        COUNT(*) FILTER(WHERE error_rate <= 100) as valid_cnt
    FROM predictions
    WHERE verified = 1 AND actual_price > 0
""")
stat = cursor.fetchone()

# 중앙값 계산
cursor.execute("""
    SELECT error_rate FROM predictions
    WHERE verified = 1 AND error_rate <= 100 AND actual_price > 0
    ORDER BY error_rate
""")
rates = [r[0] for r in cursor.fetchall()]
median_err = float(np.median(rates)) if rates else 0

print(f"\n  전체 검증 건수  : {stat['cnt']}건")
print(f"  유효 건수(≤100%): {stat['valid_cnt']}건")
print(f"  평균 오차율     : {stat['avg_err']:.2f}%")
print(f"  중앙값 오차율   : {median_err:.2f}%")

conn.close()
print("\n=== 완료 ===")
