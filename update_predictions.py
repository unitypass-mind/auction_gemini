"""
기존 검증 데이터의 예측값을 새 모델로 업데이트
"""
import sqlite3
import sys
import logging
from pathlib import Path

# main.py에서 필요한 함수 import
sys.path.insert(0, str(Path(__file__).parent))
from main import predict_price_advanced, model, pattern_property_round, pattern_region, pattern_complex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "data/predictions.db"


def update_all_predictions():
    """actual_price가 있는 모든 예측을 새 모델로 재계산"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # actual_price가 있는 모든 예측 조회
    cursor.execute("""
        SELECT id, case_no, 감정가, 물건종류, 지역, 면적, 경매회차, 입찰자수,
               입찰자수_실제, 공유지분_건물, 공유지분_토지, 청구금액비율,
               second_price, actual_price
        FROM predictions
        WHERE actual_price IS NOT NULL AND actual_price > 0
    """)

    rows = cursor.fetchall()
    logger.info(f"재예측 대상: {len(rows)}건")

    updated_count = 0
    for row in rows:
        (id, case_no, appraisal, property_type, region, area, auction_round,
         bidders, bidders_actual, share_floor, share_land, debt_ratio,
         second_price, actual_price) = row

        # 새 모델로 예측
        try:
            new_predicted = predict_price_advanced(
                start_price=appraisal,
                property_type=property_type or "기타",
                region=region or "기타",
                area=area or 85.0,
                auction_round=auction_round or 1,
                bidders=bidders or 10,
                bidders_actual=bidders_actual,
                second_price=second_price or 0,
                is_hard=0,
                tag_count=0,
                share_floor=share_floor or 0,
                share_land=share_land or 0,
                debt_ratio=debt_ratio or 0.0
            )

            # 오차 계산
            error_amount = abs(actual_price - new_predicted)
            error_rate = (error_amount / actual_price * 100) if actual_price > 0 else 0

            # DB 업데이트
            cursor.execute("""
                UPDATE predictions
                SET predicted_price = ?,
                    error_amount = ?,
                    error_rate = ?
                WHERE id = ?
            """, (new_predicted, error_amount, error_rate, id))

            updated_count += 1

            if updated_count % 50 == 0:
                logger.info(f"진행중: {updated_count}/{len(rows)}")

        except Exception as e:
            logger.error(f"예측 실패 (ID={id}): {e}")
            continue

    conn.commit()
    conn.close()

    logger.info(f"\n✅ 재예측 완료: {updated_count}건 업데이트")


if __name__ == "__main__":
    if model is None:
        logger.error("❌ AI 모델이 로드되지 않았습니다!")
        sys.exit(1)

    logger.info("="*80)
    logger.info("🔄 검증 데이터 재예측 시작 (새 v4 모델)")
    logger.info("="*80)

    update_all_predictions()

    logger.info("="*80)
    logger.info("✅ 완료! 웹 브라우저를 새로고침하여 확인하세요")
    logger.info("="*80)
