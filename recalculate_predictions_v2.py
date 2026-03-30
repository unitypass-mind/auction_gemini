"""
수집된 낙찰 데이터를 v4 모델로 재예측하고 오차율 계산 (정확한 특성 생성 사용)
"""
import sqlite3
import joblib
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 모델 파일 경로
MODEL_PATH = Path("models/auction_model_v4.pkl")
PATTERN_PROPERTY_ROUND_PATH = Path("models/pattern_property_round.pkl")
PATTERN_REGION_PATH = Path("models/pattern_region.pkl")
PATTERN_COMPLEX_PATH = Path("models/pattern_complex.pkl")
DB_PATH = Path("data/predictions.db")


def calc_lowest_price_by_round(appraisal_price: int, auction_round: int) -> int:
    """경매회차에 따른 최저입찰가 계산"""
    ratio = 1.0
    for _ in range(auction_round - 1):
        ratio *= 0.8
    return int(appraisal_price * ratio)


def create_features_v4(
    start_price: int,
    property_type: str,
    region: str,
    area: float,
    auction_round: int,
    bidders: int,
    bidders_actual: int = None,
    share_floor: float = 0,
    share_land: float = 0,
    debt_ratio: float = 0,
    second_price: int = 0,
    pattern_property_round: dict = None,
    pattern_region: dict = None,
    pattern_complex: dict = None,
    lowest_bid_price: int = None,
) -> np.ndarray:
    """
    v4 특성 생성 - main.py와 동일한 로직
    특성 개수: 53 (v3) + 5 (패턴) = 58개
    """
    features = []

    # 최저입찰가 계산
    if lowest_bid_price is None or lowest_bid_price == 0:
        lowest_bid_price = calc_lowest_price_by_round(start_price, auction_round)

    lowest_price_ratio = lowest_bid_price / start_price if start_price > 0 else 0.8

    if bidders_actual is None:
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

    # 6. 공유지분 & 부채 (4개)
    features.extend([
        share_floor,
        share_land,
        debt_ratio,
        np.log1p(debt_ratio),
    ])

    # 7. 2순위 가격 (3개)
    second_price_safe = max(0, second_price) if second_price else 0
    features.extend([
        second_price_safe,
        np.log1p(second_price_safe),
        second_price_safe / start_price if start_price > 0 and second_price_safe > 0 else 0,
    ])

    # 8. 최저입찰가 상호작용 특성 (4개)
    features.extend([
        lowest_price_ratio * auction_round,
        lowest_price_ratio * bidders_actual,
        lowest_bid_price * bidders_actual,
        np.log1p(lowest_price_ratio * auction_round),
    ])

    # 9. 고급 상호작용 특성 (7개)
    features.extend([
        start_price * auction_round,
        start_price * bidders_actual,
        area * auction_round,
        (start_price / area if area > 0 else 0) * auction_round,
        bidders_actual / auction_round if auction_round > 0 else bidders_actual,
        share_floor + share_land,
        debt_ratio * auction_round,
    ])

    # 10. 다항 특성 (4개)
    features.extend([
        start_price ** 2,
        area ** 2,
        auction_round ** 2,
        bidders_actual ** 2,
    ])

    # 11. 과거 패턴 특성 (5개)
    # 물건종류 정규화
    property_category = '기타'
    if '아파트' in property_type:
        property_category = '아파트'
    elif '오피스텔' in property_type:
        property_category = '오피스텔'
    elif '다세대' in property_type or '연립' in property_type:
        property_category = '다세대'
    elif '단독' in property_type:
        property_category = '단독주택'
    elif '상가' in property_type or '점포' in property_type:
        property_category = '상가'
    elif '토지' in property_type:
        property_category = '토지'

    # 지역 그룹핑
    region_group = '기타'
    for r in ['서울', '경기', '인천', '부산', '대구', '대전', '광주', '울산', '세종', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']:
        if r in region:
            region_group = r
            break

    # 패턴 1: 물건종류 × 경매회차
    pattern_pr_key = f"{property_category}_{auction_round}"
    pattern_pr_ratio = 0.5
    if pattern_property_round and pattern_pr_key in pattern_property_round:
        pattern_pr_ratio = pattern_property_round[pattern_pr_key]['avg_ratio']

    # 패턴 2: 지역별 평균
    region_avg_ratio = 0.5
    if pattern_region and region_group in pattern_region:
        region_avg_ratio = pattern_region[region_group]['avg_ratio']

    # 패턴 3: 복합 패턴 (지역 × 물건 × 회차)
    pattern_complex_key = f"{region_group}_{property_category}_{auction_round}"
    pattern_complex_ratio = 0.5
    if pattern_complex and pattern_complex_key in pattern_complex:
        pattern_complex_ratio = pattern_complex[pattern_complex_key]['avg_ratio']

    # 패턴 특성 추가 (5개)
    features.extend([
        pattern_pr_ratio,
        region_avg_ratio,
        pattern_complex_ratio,
        pattern_pr_ratio * region_avg_ratio,
        abs(pattern_pr_ratio - region_avg_ratio),
    ])

    # NaN, Inf 값 처리
    features_array = np.array(features, dtype=np.float64)
    features_array = np.nan_to_num(features_array, nan=0.0, posinf=0.0, neginf=0.0)

    return features_array


def main():
    logger.info("=" * 60)
    logger.info("v4 모델을 사용한 낙찰 데이터 재예측 (정확한 특성 생성)")
    logger.info("=" * 60)

    # 모델 로드
    logger.info("\n모델 및 패턴 테이블 로드 중...")
    try:
        model = joblib.load(MODEL_PATH)
        pattern_property_round = joblib.load(PATTERN_PROPERTY_ROUND_PATH)
        pattern_region = joblib.load(PATTERN_REGION_PATH)
        pattern_complex = joblib.load(PATTERN_COMPLEX_PATH)
        logger.info(f"v4 모델 로드 성공 (특성: {model.n_features_in_}개)")
    except Exception as e:
        logger.error(f"모델 로드 실패: {e}")
        return

    # 데이터베이스 연결
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 낙찰가가 있는 데이터 조회 (모든 필요한 컬럼 포함)
    cursor.execute("""
        SELECT
            id, case_no, 감정가, 물건종류, 지역, 면적, 경매회차,
            입찰자수, 입찰자수_실제, 공유지분_건물, 공유지분_토지,
            청구금액비율, second_price, actual_price
        FROM predictions
        WHERE actual_price > 0
        ORDER BY id
    """)

    rows = cursor.fetchall()
    logger.info(f"\n낙찰가 있는 데이터: {len(rows)}건")

    if len(rows) == 0:
        logger.warning("재예측할 데이터가 없습니다")
        conn.close()
        return

    # 재예측 시작
    logger.info("\n재예측 시작...")
    updated_count = 0
    errors = []

    for i, row in enumerate(rows, 1):
        (row_id, case_no, appraisal, prop_type, region, area, round_num,
         bidders, bidders_actual, share_floor, share_land, debt_ratio,
         second_price, actual_price) = row

        try:
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

            # 특성 생성
            features = create_features_v4(
                appraisal, prop_type, region, area, round_num, bidders,
                bidders_actual, share_floor, share_land, debt_ratio, second_price,
                pattern_property_round, pattern_region, pattern_complex
            )

            # v4 모델 예측
            predicted = int(model.predict(features.reshape(1, -1))[0])

            # 예측값 범위 제한 (감정가의 10% ~ 200%)
            min_price = int(appraisal * 0.10)
            max_price = int(appraisal * 2.00)
            predicted = max(min_price, min(predicted, max_price))

            # 오차 계산
            error_amount = abs(actual_price - predicted)
            error_rate = (error_amount / actual_price * 100) if actual_price > 0 else 0

            # 데이터베이스 업데이트
            cursor.execute("""
                UPDATE predictions
                SET predicted_price = ?,
                    error_amount = ?,
                    error_rate = ?,
                    model_used = 1,
                    prediction_mode = 'v4 AI model (58 features - corrected)'
                WHERE id = ?
            """, (predicted, error_amount, error_rate, row_id))

            updated_count += 1

            # 진행 상황 표시 (100건마다)
            if i % 100 == 0:
                logger.info(f"  진행: {i}/{len(rows)}건 처리 완료")

        except Exception as e:
            errors.append((case_no, str(e)))
            logger.error(f"  [{case_no}] 예측 실패: {e}")

    # 변경사항 저장
    conn.commit()

    # 최종 통계
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            AVG(error_rate) as avg_error,
            MIN(error_rate) as min_error,
            MAX(error_rate) as max_error,
            SUM(CASE WHEN error_rate < 20 THEN 1 ELSE 0 END) as under_20,
            SUM(CASE WHEN error_rate < 30 THEN 1 ELSE 0 END) as under_30,
            SUM(CASE WHEN error_rate < 50 THEN 1 ELSE 0 END) as under_50
        FROM predictions
        WHERE actual_price > 0 AND prediction_mode LIKE '%corrected%'
    """)

    stats = cursor.fetchone()
    total, avg_error, min_error, max_error, under_20, under_30, under_50 = stats

    conn.close()

    logger.info("\n" + "=" * 60)
    logger.info("재예측 완료!")
    logger.info("=" * 60)
    logger.info(f"업데이트된 데이터: {updated_count}건")
    logger.info(f"실패: {len(errors)}건")
    logger.info(f"\n최종 통계:")
    logger.info(f"  - 총 데이터: {total}건")
    logger.info(f"  - 평균 오차율: {avg_error:.2f}%")
    logger.info(f"  - 최소 오차율: {min_error:.2f}%")
    logger.info(f"  - 최대 오차율: {max_error:.2f}%")
    logger.info(f"\n정확도 분포:")
    logger.info(f"  - 오차 20% 미만: {under_20}건 ({under_20/total*100:.1f}%)")
    logger.info(f"  - 오차 30% 미만: {under_30}건 ({under_30/total*100:.1f}%)")
    logger.info(f"  - 오차 50% 미만: {under_50}건 ({under_50/total*100:.1f}%)")

    if errors:
        logger.info(f"\n오류 발생 항목 (최대 10개):")
        for case_no, error_msg in errors[:10]:
            logger.info(f"  - {case_no}: {error_msg}")


if __name__ == "__main__":
    main()
