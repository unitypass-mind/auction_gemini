"""
기존 검증된 데이터를 v2 모델로 재예측하여 DB 업데이트
"""
import sqlite3
import sys
import io
import joblib
import numpy as np
from pathlib import Path
import logging

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = Path("data/predictions.db")
MODEL_PATH = Path("models/auction_model_v2.pkl")


def create_features_v2(
    start_price: int,
    property_type: str,
    region: str,
    area: float,
    auction_round: int,
    bidders: int,
    bidders_actual: int,
    second_price: int,
    is_hard: int,
    tag_count: int,
    share_floor: int,
    share_land: int,
    debt_ratio: float
) -> np.ndarray:
    """신규 변수를 포함한 특성 생성 (48개 특성)"""

    # 기본값 설정
    if bidders_actual is None or bidders_actual == 0:
        bidders_actual = bidders
    if second_price is None or second_price < 0:
        second_price = 0

    features = []

    # 1. 기존 기본 특성 (11개)
    min_price = start_price * 0.8
    평당감정가 = start_price / (area * 0.3025) if area > 0 else 0

    features.extend([
        start_price,
        np.log1p(start_price),
        min_price,
        np.log1p(min_price),
        0.8,
        bidders_actual,
        np.log1p(bidders_actual),
        bidders_actual / 11.0,
        auction_round,
        auction_round ** 2,
        max(0.5, 1 - (auction_round - 1) * 0.1),
    ])

    # 2. 상호작용 특성 (2개)
    features.extend([
        np.log1p(start_price) * np.log1p(bidders_actual),
        0.8 * bidders_actual,
    ])

    # 3. 면적 특성 (5개)
    features.extend([
        area,
        np.log1p(area),
        평당감정가,
        np.log1p(평당감정가),
        np.log1p(area) * np.log1p(bidders_actual),
    ])

    # 4. 지역 인코딩 (1개)
    region_map = {'경기': 0, '기타': 1, '대구': 2, '부산': 3, '서울': 4, '인천': 5}
    region_idx = region_map.get(region, 1)
    features.append(region_idx)

    # 5. 지역 원-핫 (6개)
    region_order = ['경기', '기타', '대구', '부산', '서울', '인천']
    for r in region_order:
        features.append(1 if region == r else 0)

    # 6. 물건종류 인코딩 (1개)
    type_map = {'다세대': 0, '단독주택': 1, '상가': 2, '아파트': 3, '오피스텔': 4}
    type_idx = type_map.get(property_type, 3)
    features.append(type_idx)

    # 7. 물건종류 원-핫 (5개)
    type_order = ['다세대', '단독주택', '상가', '아파트', '오피스텔']
    for t in type_order:
        features.append(1 if property_type == t else 0)

    # 8. 가격구간 원-핫 (5개)
    if start_price <= 100_000_000:
        price_range = [1, 0, 0, 0, 0]
    elif start_price <= 300_000_000:
        price_range = [0, 1, 0, 0, 0]
    elif start_price <= 500_000_000:
        price_range = [0, 0, 1, 0, 0]
    elif start_price <= 1_000_000_000:
        price_range = [0, 0, 0, 1, 0]
    else:
        price_range = [0, 0, 0, 0, 1]
    features.extend(price_range)

    # ===== 신규 변수 (12개) =====

    # 9. 2등 입찰가 관련 (3개)
    features.append(second_price)
    features.append(np.log1p(second_price))
    if second_price > 0:
        competition_gap = 1 - (second_price / start_price)
    else:
        competition_gap = 0
    features.append(competition_gap)

    # 10. 권리 관련 (4개)
    features.append(is_hard)
    features.append(tag_count)
    features.append(np.log1p(tag_count))
    risk_score = is_hard * 0.2 + tag_count * 0.05
    features.append(risk_score)

    # 11. 공유지분 (2개)
    features.append(share_floor)
    features.append(share_land)

    # 12. 청구금액 (3개)
    features.append(debt_ratio)
    features.append(debt_ratio ** 2)
    debt_risk = 1 if debt_ratio > 0.7 else 0
    features.append(debt_risk)

    return np.array(features).reshape(1, -1)


def create_features_enhanced(
    start_price: int,
    property_type: str,
    region: str,
    area: float,
    auction_round: int,
    bidders: int,
    bidders_actual: int,
    second_price: int,
    is_hard: int,
    tag_count: int,
    share_floor: int,
    share_land: int,
    debt_ratio: float
) -> np.ndarray:
    """고도화된 특성 생성 (93개 특성)"""
    # 기본값 설정
    if bidders_actual is None or bidders_actual == 0:
        bidders_actual = bidders
    if second_price is None or second_price < 0:
        second_price = 0

    # 기존 48개 특성
    features = []
    min_price = start_price * 0.8
    평당감정가 = start_price / (area * 0.3025) if area > 0 else 0

    features.extend([
        start_price, np.log1p(start_price), min_price, np.log1p(min_price),
        0.8, bidders_actual, np.log1p(bidders_actual), bidders_actual / 11.0,
        auction_round, auction_round ** 2, max(0.5, 1 - (auction_round - 1) * 0.1),
    ])

    features.extend([
        np.log1p(start_price) * np.log1p(bidders_actual),
        0.8 * bidders_actual,
    ])

    features.extend([
        area, np.log1p(area), 평당감정가, np.log1p(평당감정가),
        np.log1p(area) * np.log1p(bidders_actual),
    ])

    region_map = {'경기': 0, '기타': 1, '대구': 2, '부산': 3, '서울': 4, '인천': 5}
    features.append(region_map.get(region, 1))

    region_order = ['경기', '기타', '대구', '부산', '서울', '인천']
    for r in region_order:
        features.append(1 if region == r else 0)

    type_map = {'다세대': 0, '단독주택': 1, '상가': 2, '아파트': 3, '오피스텔': 4}
    features.append(type_map.get(property_type, 3))

    type_order = ['다세대', '단독주택', '상가', '아파트', '오피스텔']
    for t in type_order:
        features.append(1 if property_type == t else 0)

    if start_price <= 100_000_000:
        price_range = [1, 0, 0, 0, 0]
    elif start_price <= 300_000_000:
        price_range = [0, 1, 0, 0, 0]
    elif start_price <= 500_000_000:
        price_range = [0, 0, 1, 0, 0]
    elif start_price <= 1_000_000_000:
        price_range = [0, 0, 0, 1, 0]
    else:
        price_range = [0, 0, 0, 0, 1]
    features.extend(price_range)

    features.append(second_price)
    features.append(np.log1p(second_price))
    competition_gap = 1 - (second_price / start_price) if second_price > 0 else 0
    features.append(competition_gap)

    features.append(is_hard)
    features.append(tag_count)
    features.append(np.log1p(tag_count))
    risk_score = is_hard * 0.2 + tag_count * 0.05
    features.append(risk_score)

    features.append(share_floor)
    features.append(share_land)

    features.append(debt_ratio)
    features.append(debt_ratio ** 2)
    debt_risk = 1 if debt_ratio > 0.7 else 0
    features.append(debt_risk)

    # 신규 고급 특성 (45개)
    features.append(np.sqrt(start_price))
    features.append(np.cbrt(start_price))
    price_per_area = start_price / area if area > 0 else 0
    features.append(np.log1p(price_per_area))
    price_tier = np.log10(start_price + 1) / 10
    features.append(price_tier)
    price_gap = start_price - min_price
    features.append(np.log1p(price_gap))

    bidder_density = bidders_actual / max(1, auction_round)
    features.append(bidder_density)
    features.append(bidders_actual ** 2)
    second_price_ratio = second_price / start_price if second_price > 0 and start_price > 0 else 0
    features.append(second_price_ratio)
    competition_intensity = (start_price - second_price) / start_price if second_price > 0 else 1.0
    features.append(competition_intensity)
    features.append(np.log1p(bidders_actual) ** 2)
    competition_index = bidders_actual * bidder_density
    features.append(competition_index)

    features.append(np.log1p(auction_round))
    features.append(auction_round ** 3)
    round_depreciation = max(0.3, 1 - (auction_round * 0.15))
    features.append(round_depreciation)
    serious_failure = 1 if auction_round >= 3 else 0
    features.append(serious_failure)

    features.append(area ** 2)
    features.append(평당감정가 ** 2)
    is_small = 1 if area < 60 else 0
    is_large = 1 if area > 120 else 0
    features.append(is_small)
    features.append(is_large)
    area_efficiency = area / (np.log1p(start_price) + 1)
    features.append(area_efficiency)

    features.append(np.log1p(start_price) * auction_round)
    features.append(np.log1p(start_price) * np.log1p(area))
    features.append(bidders_actual * auction_round)
    features.append(bidders_actual * area)
    features.append(평당감정가 * bidders_actual)
    features.append(auction_round * area)
    features.append(np.log1p(start_price) * bidders_actual * auction_round)
    features.append(bidders_actual * np.log1p(start_price))

    features.append(is_hard * np.log1p(start_price))
    tag_density = tag_count / max(1, auction_round)
    features.append(tag_density)
    total_risk = (is_hard * 0.3 + tag_count * 0.1 + share_floor * 0.2 +
                  share_land * 0.2 + debt_ratio * 0.2)
    features.append(total_risk)
    features.append(is_hard * debt_ratio)
    total_share = share_floor + share_land
    features.append(total_share)
    features.append(total_risk * auction_round)

    is_seoul_apt = 1 if (region == '서울' and property_type == '아파트') else 0
    features.append(is_seoul_apt)
    is_gyeonggi_apt = 1 if (region == '경기' and property_type == '아파트') else 0
    features.append(is_gyeonggi_apt)

    features.append(np.log1p(debt_ratio))
    features.append(debt_ratio ** 3)
    high_debt = 1 if debt_ratio > 0.5 else 0
    features.append(high_debt)
    features.append(debt_ratio * bidders_actual)

    return np.array(features).reshape(1, -1)


def update_predictions():
    """기존 검증된 데이터를 v2 모델로 재예측"""

    logger.info("=" * 60)
    logger.info("검증된 데이터 v2 모델 재예측 시작")
    logger.info("=" * 60)

    # 모델 로드
    if not MODEL_PATH.exists():
        logger.error(f"v2 모델 파일이 없습니다: {MODEL_PATH}")
        return

    model = joblib.load(MODEL_PATH)
    logger.info(f"v2 모델 로드 완료: {MODEL_PATH}")

    # 모델이 기대하는 특성 개수 확인
    try:
        expected_features = model.n_features_in_ if hasattr(model, 'n_features_in_') else 48
    except:
        expected_features = 48

    logger.info(f"모델 기대 특성 개수: {expected_features}개")
    use_enhanced = (expected_features > 48)  # 48개보다 많으면 enhanced 모델

    # DB 연결
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 검증된 데이터 조회
    cursor.execute("""
        SELECT
            id, 감정가, 물건종류, 지역, 면적, 경매회차, 입찰자수,
            입찰자수_실제, second_price, 권리분석복잡도, 권리사항태그수,
            공유지분_건물, 공유지분_토지, 청구금액비율,
            actual_price, predicted_price
        FROM predictions
        WHERE verified = 1 AND actual_price > 0
    """)

    rows = cursor.fetchall()
    total_count = len(rows)
    logger.info(f"검증된 데이터 {total_count}건 조회")

    updated_count = 0
    total_old_error = 0
    total_new_error = 0

    print("\n재예측 진행 중...")
    print("-" * 60)

    for row in rows:
        (record_id, start_price, property_type, region, area, auction_round, bidders,
         bidders_actual, second_price, is_hard, tag_count,
         share_floor, share_land, debt_ratio, actual_price, old_predicted) = row

        # None 값 처리
        if bidders_actual is None:
            bidders_actual = bidders
        if second_price is None:
            second_price = 0
        if is_hard is None:
            is_hard = 0
        if tag_count is None:
            tag_count = 0
        if share_floor is None:
            share_floor = 0
        if share_land is None:
            share_land = 0
        if debt_ratio is None:
            debt_ratio = 0.0
        if area is None or area == 0:
            area = 85.0

        try:
            # 모델 타입에 따라 적절한 특성 생성
            if use_enhanced:
                features = create_features_enhanced(
                    start_price, property_type, region, area, auction_round, bidders,
                    bidders_actual, second_price, is_hard, tag_count,
                    share_floor, share_land, debt_ratio
                )
            else:
                features = create_features_v2(
                    start_price, property_type, region, area, auction_round, bidders,
                    bidders_actual, second_price, is_hard, tag_count,
                    share_floor, share_land, debt_ratio
                )

            new_predicted = int(model.predict(features)[0])

            # 예측값 범위 제한
            min_price = int(start_price * 0.10)
            max_price = int(start_price * 1.50)
            new_predicted = max(min_price, min(new_predicted, max_price))

            # 새로운 오차 계산
            new_error_amount = abs(actual_price - new_predicted)
            new_error_rate = (new_error_amount / actual_price * 100) if actual_price > 0 else 0

            # 구 예측 오차
            old_error_amount = abs(actual_price - old_predicted)
            old_error_rate = (old_error_amount / actual_price * 100) if actual_price > 0 else 0

            # 예상 수익 재계산
            expected_profit = start_price - new_predicted
            profit_rate = (expected_profit / start_price * 100) if start_price > 0 else 0

            # DB 업데이트
            cursor.execute("""
                UPDATE predictions
                SET
                    predicted_price = ?,
                    expected_profit = ?,
                    profit_rate = ?,
                    error_amount = ?,
                    error_rate = ?,
                    prediction_mode = 'v2_model_48features',
                    model_used = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                new_predicted,
                expected_profit,
                profit_rate,
                new_error_amount,
                new_error_rate,
                record_id
            ))

            updated_count += 1
            total_old_error += old_error_rate
            total_new_error += new_error_rate

            # 진행상황 표시 (10건마다)
            if updated_count % 10 == 0:
                print(f"진행: {updated_count}/{total_count}건 완료...")

        except Exception as e:
            logger.error(f"재예측 실패 (ID={record_id}): {e}")
            continue

    # 커밋
    conn.commit()
    conn.close()

    # 결과 출력
    print("\n" + "=" * 60)
    print("재예측 완료!")
    print("=" * 60)
    print(f"총 데이터: {total_count}건")
    print(f"업데이트 완료: {updated_count}건")
    print(f"실패: {total_count - updated_count}건")
    print()
    print("정확도 개선:")
    print(f"  구 모델 평균 오차율: {total_old_error / updated_count:.2f}%")
    print(f"  v2 모델 평균 오차율: {total_new_error / updated_count:.2f}%")
    print(f"  개선률: {total_old_error / updated_count - total_new_error / updated_count:.2f}%p 향상")
    print("=" * 60)


if __name__ == "__main__":
    update_predictions()
