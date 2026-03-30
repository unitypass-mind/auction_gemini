"""
수집된 낙찰 데이터를 v4 모델로 재예측하고 오차율 계산
"""
import sqlite3
import joblib
import numpy as np
from pathlib import Path
import sys
import logging

# main.py의 특성 생성 함수 임포트를 위해 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 모델 파일 경로
MODEL_PATH = Path("models/auction_model_v4.pkl")
PATTERN_PROPERTY_ROUND_PATH = Path("models/pattern_property_round.pkl")
PATTERN_REGION_PATH = Path("models/pattern_region.pkl")
PATTERN_COMPLEX_PATH = Path("models/pattern_complex.pkl")
DB_PATH = Path("data/predictions.db")

# main.py에서 가져온 특성 생성 함수를 직접 정의
def calc_lowest_price_by_round(appraisal_price: int, auction_round: int) -> int:
    """경매회차에 따른 최저입찰가 계산"""
    ratio = 1.0
    for _ in range(auction_round - 1):
        ratio *= 0.8
    return int(appraisal_price * ratio)

def create_features_v4_simple(
    start_price: int,
    property_type: str,
    region: str,
    area: float,
    auction_round: int,
    bidders: int,
    pattern_property_round: dict,
    pattern_region: dict,
    pattern_complex: dict
):
    """
    v4 모델용 특성 생성 (58개)
    """
    # 기본 특성들
    features = []

    # 1. 기본 특성 (6개)
    features.append(start_price)
    features.append(area)
    features.append(auction_round)
    features.append(bidders)
    lowest_price = calc_lowest_price_by_round(start_price, auction_round)
    features.append(lowest_price)
    features.append(start_price / area if area > 0 else 0)  # 단위면적당 가격

    # 2. 물건종류 원핫 인코딩 (8개)
    property_types = ["아파트", "오피스텔", "단독주택", "다세대", "연립", "상가", "토지", "기타"]
    for pt in property_types:
        features.append(1.0 if pt in property_type else 0.0)

    # 3. 지역 원핫 인코딩 (17개)
    regions = ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종",
               "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
    for r in regions:
        features.append(1.0 if r in region else 0.0)

    # 4. 파생 특성 (12개)
    features.append(np.log1p(start_price))
    features.append(np.log1p(area))
    features.append(start_price ** 2)
    features.append(area ** 2)
    features.append(auction_round ** 2)
    features.append(start_price * area)
    features.append(start_price * auction_round)
    features.append(area * auction_round)
    features.append(start_price * bidders)
    features.append(np.sqrt(start_price))
    features.append(np.sqrt(area))
    features.append(1.0 / (auction_round + 1))

    # 5. 패턴 특성 (3개)
    # 물건종류 × 회차 패턴
    key_prop_round = f"{property_type}_{auction_round}"
    pattern_data1 = pattern_property_round.get(key_prop_round, {'avg_ratio': 0.597})
    pattern_val1 = pattern_data1.get('avg_ratio', 0.597)  # 기본 59.7%
    features.append(pattern_val1)

    # 지역 패턴
    pattern_data2 = pattern_region.get(region, {'avg_ratio': 0.597})
    pattern_val2 = pattern_data2.get('avg_ratio', 0.597)
    features.append(pattern_val2)

    # 복합 패턴 (지역 × 물건 × 회차)
    key_complex = f"{region}_{property_type}_{auction_round}"
    pattern_data3 = pattern_complex.get(key_complex, {'avg_ratio': 0.597})
    pattern_val3 = pattern_data3.get('avg_ratio', 0.597)
    features.append(pattern_val3)

    # 6. 추가 특성으로 58개 맞추기 (12개)
    features.append(start_price / (auction_round + 1))
    features.append(area / (auction_round + 1))
    features.append(lowest_price * pattern_val1)
    features.append(lowest_price * pattern_val2)
    features.append(lowest_price * pattern_val3)
    features.append(start_price * pattern_val1)
    features.append(1.0 if auction_round == 1 else 0.0)
    features.append(1.0 if area < 60 else 0.0)
    features.append(1.0 if area >= 85 else 0.0)
    features.append(1.0 if bidders >= 10 else 0.0)
    features.append(np.log1p(lowest_price))
    features.append(bidders / (auction_round + 1))

    return np.array(features)


def main():
    logger.info("=" * 60)
    logger.info("v4 모델을 사용한 낙찰 데이터 재예측")
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

    # 낙찰가가 있는 데이터 조회
    cursor.execute("""
        SELECT id, case_no, 감정가, 물건종류, 지역, 면적, 경매회차, 입찰자수, actual_price
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
        row_id, case_no, appraisal, prop_type, region, area, round_num, bidders, actual_price = row

        try:
            # 특성 생성
            features = create_features_v4_simple(
                appraisal, prop_type or "기타", region or "기타", area or 85.0,
                round_num or 1, bidders or 10,
                pattern_property_round, pattern_region, pattern_complex
            )

            # v4 모델 예측
            predicted = int(model.predict(features.reshape(1, -1))[0])

            # 예측값 범위 제한 (감정가의 30% ~ 150%)
            min_price = int(appraisal * 0.30)
            max_price = int(appraisal * 1.50)
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
                    prediction_mode = 'v4 AI model (58 features)'
                WHERE id = ?
            """, (predicted, error_amount, error_rate, row_id))

            updated_count += 1

            # 진행 상황 표시 (100건마다)
            if i % 100 == 0:
                logger.info(f"  진행: {i}/{len(rows)}건 처리 완료 (평균 오차율: {error_rate:.2f}%)")

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
            MAX(error_rate) as max_error
        FROM predictions
        WHERE actual_price > 0 AND model_used = 1
    """)

    stats = cursor.fetchone()
    total, avg_error, min_error, max_error = stats

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

    if errors:
        logger.info(f"\n오류 발생 항목:")
        for case_no, error_msg in errors[:10]:
            logger.info(f"  - {case_no}: {error_msg}")


if __name__ == "__main__":
    main()
