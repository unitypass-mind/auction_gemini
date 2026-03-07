"""
최근 낙찰 데이터 수집 및 모델 재학습 자동화 스크립트
"""

import sys
from valueauction_collector import ValueAuctionCollector
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def collect_recent_data():
    """최근 낙찰 데이터 수집"""
    collector = ValueAuctionCollector()

    logger.info("=" * 80)
    logger.info("최근 낙찰 데이터 수집 시작")
    logger.info("=" * 80)

    # 최근 30일간 데이터, 최대 200건 확인 (중복 제외하고 새 데이터만 수집)
    stats = collector.collect_and_verify(
        max_items=200,
        start_offset=0,
        min_appraisal_price=0,
        continuous=True,  # 중복 체크 후 새 데이터만
        days_limit=30  # 최근 30일
    )

    logger.info("\n" + "=" * 80)
    logger.info("📊 수집 통계")
    logger.info("=" * 80)
    logger.info(f"API에서 가져온 총 데이터: {stats['total_fetched']}건")
    logger.info(f"✅ 처리 완료 (새로운 데이터): {stats['total_processed']}건")
    logger.info(f"⏭️  중복 건너뜀: {stats['duplicates']}건")
    logger.info(f"❌ 낙찰 미완료: {stats['not_sold']}건")
    logger.info(f"📅 날짜 범위 초과: {stats['too_old']}건")
    logger.info(f"⚠️  건너뜀 (기타): {stats['skipped']}건")
    logger.info(f"🔴 오류: {stats['errors']}건")
    logger.info("=" * 80)

    return stats


if __name__ == "__main__":
    try:
        stats = collect_recent_data()

        if stats['total_processed'] > 0:
            logger.info(f"\n✅ {stats['total_processed']}건의 새로운 낙찰 데이터가 추가되었습니다!")
            logger.info("💡 다음 단계: 모델 재학습을 실행하세요")
            sys.exit(0)
        else:
            logger.info("\n💡 새로운 데이터가 없습니다. 모델 재학습이 필요하지 않습니다.")
            sys.exit(1)

    except Exception as e:
        logger.error(f"데이터 수집 중 오류 발생: {e}", exc_info=True)
        sys.exit(1)
