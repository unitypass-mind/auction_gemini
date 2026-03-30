"""단일 레코드 예측 테스트"""
import sqlite3
import joblib
import numpy as np
from pathlib import Path

# 모델 로드
model = joblib.load(Path("models/auction_model_v4.pkl"))
pattern_property_round = joblib.load(Path("models/pattern_property_round.pkl"))
pattern_region = joblib.load(Path("models/pattern_region.pkl"))
pattern_complex = joblib.load(Path("models/pattern_complex.pkl"))

# 데이터베이스에서 조회
conn = sqlite3.connect("data/predictions.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT
        id, case_no, 감정가, 물건종류, 지역, 면적, 경매회차,
        입찰자수, 입찰자수_실제, 공유지분_건물, 공유지분_토지,
        청구금액비율, second_price, actual_price, predicted_price
    FROM predictions
    WHERE case_no = '2024타경56274'
""")

row = cursor.fetchone()
(row_id, case_no, appraisal, prop_type, region, area, round_num,
 bidders, bidders_actual, share_floor, share_land, debt_ratio,
 second_price, actual_price, current_predicted) = row

print(f"사건번호: {case_no}")
print(f"감정가: {appraisal:,}원")
print(f"현재 예측값: {current_predicted:,}원")
print(f"실제 낙찰가: {actual_price:,}원")
print(f"물건종류: {prop_type}, 지역: {region}, 면적: {area}, 회차: {round_num}")
print()

# recalculate_predictions_v2.py와 동일한 특성 생성
def calc_lowest_price_by_round(appraisal_price: int, auction_round: int) -> int:
    ratio = 1.0
    for _ in range(auction_round - 1):
        ratio *= 0.8
    return int(appraisal_price * ratio)

# 기본값 설정
prop_type = prop_type or '기타'
region = region or '기타'
area = area or 85.0
round_num = round_num or 1
bidders = bidders or 10
bidders_actual = bidders_actual or bidders
share_floor = float(share_floor or 0)
share_land = float(share_land or 0)
debt_ratio = float(debt_ratio or 0)
second_price = int(second_price or 0)

# 간단한 특성 생성 (처음 10개만)
features = []

# 1. 기본 가격 특성 (5개)
lowest_bid_price = calc_lowest_price_by_round(appraisal, round_num)
lowest_price_ratio = lowest_bid_price / appraisal if appraisal > 0 else 0.8

features.extend([
    appraisal,
    np.log1p(appraisal),
    lowest_bid_price,
    np.log1p(lowest_bid_price),
    lowest_price_ratio,
])

print(f"최저입찰가: {lowest_bid_price:,}원 (비율: {lowest_price_ratio:.2f})")
print(f"첫 5개 특성: {features}")

conn.close()
