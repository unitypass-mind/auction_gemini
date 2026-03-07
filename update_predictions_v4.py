"""
v4 모델로 기존 예측 데이터를 모두 재예측하여 업데이트
"""
import sqlite3
import joblib
import logging
from pathlib import Path
import sys

# train_model_v4의 함수들 import
sys.path.append('.')
from train_model_v4 import create_features_v4, calc_lowest_price_by_round

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "data/predictions.db"
MODEL_PATH = "models/auction_model_v4.pkl"
PATTERN_PROPERTY_ROUND_PATH = "models/pattern_property_round.pkl"
PATTERN_REGION_PATH = "models/pattern_region.pkl"
PATTERN_COMPLEX_PATH = "models/pattern_complex.pkl"

def update_all_predictions():
    """모든 예측 데이터를 v4 모델로 재예측"""

    # 1. 모델 및 패턴 테이블 로드
    logger.info("=" * 60)
    logger.info("v4 모델 및 패턴 테이블 로드")
    logger.info("=" * 60)

    model = joblib.load(MODEL_PATH)
    logger.info(f"✓ v4 모델 로드: {MODEL_PATH}")

    pattern_property_round = joblib.load(PATTERN_PROPERTY_ROUND_PATH)
    logger.info(f"✓ 패턴 테이블 로드: {len(pattern_property_round)}개 (물건×회차)")

    pattern_region = joblib.load(PATTERN_REGION_PATH)
    logger.info(f"✓ 패턴 테이블 로드: {len(pattern_region)}개 (지역)")

    pattern_complex = joblib.load(PATTERN_COMPLEX_PATH)
    logger.info(f"✓ 패턴 테이블 로드: {len(pattern_complex)}개 (복합)")

    # 2. 데이터베이스 연결
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 3. 모든 예측 데이터 조회
    cursor.execute("""
        SELECT
            id, case_no, 감정가, 물건종류, 지역, 면적, 경매회차, 입찰자수,
            입찰자수_실제, 공유지분_건물, 공유지분_토지, 청구금액비율,
            second_price, actual_price
        FROM predictions
        ORDER BY id
    """)

    rows = cursor.fetchall()
    total = len(rows)
    logger.info(f"\n총 {total}건의 데이터를 재예측합니다.")

    # 4. 각 데이터에 대해 재예측
    updated_count = 0
    error_count = 0

    for idx, row in enumerate(rows, 1):
        (id_, case_no, 감정가, 물건종류, 지역, 면적, 경매회차, 입찰자수,
         입찰자수_실제, 공유지분_건물, 공유지분_토지, 청구금액비율,
         second_price, actual_price) = row

        try:
            # v4 특성 생성
            features = create_features_v4(
                start_price=감정가 or 0,
                property_type=물건종류 or '기타',
                region=지역 or '기타',
                area=면적 or 0,
                auction_round=경매회차 or 1,
                bidders=입찰자수 or 0,
                bidders_actual=입찰자수_실제 if 입찰자수_실제 else 입찰자수,
                share_floor=공유지분_건물 or 0,
                share_land=공유지분_토지 or 0,
                debt_ratio=청구금액비율 or 0,
                second_price=second_price or 0,
                pattern_property_round=pattern_property_round,
                pattern_region=pattern_region,
                pattern_complex=pattern_complex,
            )

            # v4 모델로 예측
            prediction = model.predict(features.reshape(1, -1))[0]
            predicted_price = int(prediction)

            # 예측값 범위 제한 (감정가의 10% ~ 150%)
            min_price = int(감정가 * 0.10) if 감정가 else 0
            max_price = int(감정가 * 1.50) if 감정가 else predicted_price
            predicted_price = max(min_price, min(predicted_price, max_price))

            # 오차율 계산 (실제 낙찰가가 있는 경우)
            error_rate = None
            if actual_price and actual_price > 0:
                error_rate = abs(actual_price - predicted_price) / actual_price * 100

            # DB 업데이트
            cursor.execute("""
                UPDATE predictions
                SET predicted_price = ?, error_rate = ?
                WHERE id = ?
            """, (predicted_price, error_rate, id_))

            updated_count += 1

            # 진행상황 출력
            if idx % 100 == 0:
                logger.info(f"진행: {idx}/{total} ({idx/total*100:.1f}%) - 업데이트: {updated_count}건")

        except Exception as e:
            error_count += 1
            logger.error(f"오류 발생 (ID: {id_}, 사건번호: {case_no}): {e}")
            continue

    # 5. 커밋 및 종료
    conn.commit()
    conn.close()

    logger.info("\n" + "=" * 60)
    logger.info("✓ v4 모델 재예측 완료!")
    logger.info("=" * 60)
    logger.info(f"전체: {total}건")
    logger.info(f"업데이트 성공: {updated_count}건")
    logger.info(f"오류: {error_count}건")

    # 6. 통계 출력
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN actual_price > 0 THEN 1 END) as verified,
            AVG(CASE WHEN actual_price > 0 THEN error_rate END) as avg_error
        FROM predictions
    """)

    stats = cursor.fetchone()
    total_count, verified_count, avg_error = stats

    logger.info(f"\n현재 DB 통계:")
    logger.info(f"  전체 예측: {total_count}건")
    logger.info(f"  검증 완료: {verified_count}건")
    logger.info(f"  평균 오차율: {avg_error:.2f}%" if avg_error else "  평균 오차율: N/A")

    conn.close()

    return updated_count, error_count

if __name__ == "__main__":
    try:
        updated, errors = update_all_predictions()
        print(f"\n✓ 완료: {updated}건 업데이트, {errors}건 오류")
    except Exception as e:
        logger.error(f"스크립트 실행 실패: {e}", exc_info=True)
        sys.exit(1)
