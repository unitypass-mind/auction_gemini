"""recalculate_predictions_v2.py와 동일한 로직으로 한 건 예측"""
import sqlite3
import joblib
import numpy as np
from pathlib import Path

# 모델 로드
model = joblib.load(Path("models/auction_model_v4.pkl"))
pattern_property_round = joblib.load(Path("models/pattern_property_round.pkl"))
pattern_region = joblib.load(Path("models/pattern_region.pkl"))
pattern_complex = joblib.load(Path("models/pattern_complex.pkl"))

# calc_lowest_price_by_round 함수
def calc_lowest_price_by_round(appraisal_price: int, auction_round: int) -> int:
    ratio = 1.0
    for _ in range(auction_round - 1):
        ratio *= 0.8
    return int(appraisal_price * ratio)

# create_features_v4 함수 (간단 버전)
def create_features_v4_simple(start_price, property_type, region, area, auction_round, bidders):
    """v4 특성 생성 - 기본 필드만"""
    features = []

    # 최저입찰가 계산
    lowest_bid_price = calc_lowest_price_by_round(start_price, auction_round)
    lowest_price_ratio = lowest_bid_price / start_price if start_price > 0 else 0.8
    bidders_actual = bidders

    # 1. 기본 가격 특성 (5개)
    features.extend([
        start_price,
        np.log1p(start_price),
        lowest_bid_price,
        np.log1p(lowest_bid_price),
        lowest_price_ratio,
    ])

    # 2. 물건 종류 (원-핫 인코딩) (7개)
    property_types = ['아파트', '다세대', '단독주택', '오피스텔', '토지', '상가', '기타']
    for ptype in property_types:
        features.append(1 if ptype in property_type else 0)

    # 3. 지역 (원-핫 인코딩) (10개)
    regions = ['서울', '경기', '인천', '부산', '대구', '대전', '광주', '울산', '세종', '기타']
    region_matched = False
    for reg in regions[:-1]:
        if reg in region:
            features.append(1)
            region_matched = True
        else:
            features.append(0)
    features.append(0 if region_matched else 1)  # 기타

    # 4. 면적 관련 특성 (4개)
    features.extend([
        area,
        np.log1p(area),
        start_price / area if area > 0 else 0,
        np.log1p(start_price / area) if area > 0 else 0,
    ])

    # 5. 경매 진행 상황 (5개)
    features.extend([
        auction_round,
        np.log1p(auction_round),
        bidders,
        bidders_actual,
        np.log1p(bidders_actual),
    ])

    # 6-11: 나머지 특성들 (간단히 0으로 채움)
    # 총 58개가 되도록 나머지 추가
    while len(features) < 58:
        features.append(0.0)

    features_array = np.array(features[:58], dtype=np.float64)
    features_array = np.nan_to_num(features_array, nan=0.0, posinf=0.0, neginf=0.0)
    return features_array

# 데이터 조회
conn = sqlite3.connect("data/predictions.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT 감정가, 물건종류, 지역, 면적, 경매회차, 입찰자수, actual_price, predicted_price
    FROM predictions
    WHERE case_no = '2024타경56274'
""")

row = cursor.fetchone()
appraisal, prop_type, region, area, round_num, bidders, actual_price, current_predicted = row

print(f"=== 데이터 ===")
print(f"감정가: {appraisal:,}원")
print(f"물건종류: {prop_type}, 지역: {region}")
print(f"면적: {area}, 회차: {round_num}, 입찰자: {bidders}")
print(f"현재 predicted_price: {current_predicted:,}원")
print(f"실제 낙찰가: {actual_price:,}원")
print()

# 기본값 적용
prop_type = prop_type or '기타'
region = region or '기타'
area = area or 85.0  # 면적 0이면 85로
round_num = round_num or 1
bidders = bidders or 10

print(f"=== 기본값 적용 후 ===")
print(f"면적: {area}")
print()

# 특성 생성 (간단 버전)
features = create_features_v4_simple(appraisal, prop_type, region, area, round_num, bidders)

print(f"생성된 특성 개수: {len(features)}")
print(f"첫 10개 특성: {features[:10]}")
print()

# 예측
predicted_raw = model.predict(features.reshape(1, -1))[0]
print(f"모델 예측값 (raw): {predicted_raw:,.0f}원")

# 범위 제한
min_price = int(appraisal * 0.10)
max_price = int(appraisal * 2.00)
predicted = max(min_price, min(int(predicted_raw), max_price))

print(f"범위 제한 (10%~200%): {min_price:,}원 ~ {max_price:,}원")
print(f"최종 예측값: {predicted:,}원")
print()

# 오차
error_amount = abs(actual_price - predicted)
error_rate = (error_amount / actual_price * 100) if actual_price > 0 else 0
print(f"오차: {error_amount:,}원 ({error_rate:.2f}%)")

conn.close()
