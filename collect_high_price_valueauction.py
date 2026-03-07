"""
고가 물건 위주 데이터 수집 스크립트 (밸류옥션 API 사용)
감정가 10억 초과 물건을 집중적으로 수집합니다.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import logging
from datetime import datetime
from valueauction_collector import ValueAuctionCollector

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/high_price_collect_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def collect_high_price_items(target_count=150, min_price=1_000_000_000, continuous=False, days_limit=None):
    """
    고가 물건 위주 데이터 수집

    Args:
        target_count: 목표 수집 건수
        min_price: 최소 감정가 (기본값: 10억)
        continuous: 지속적 수집 모드 (기존 데이터 개수 무시하고 최신 데이터 확인)
        days_limit: 최근 N일 이내 데이터만 수집 (None이면 전체)
    """
    logger.info("=" * 80)
    if continuous:
        logger.info("지속적 데이터 수집 모드 - 최신 낙찰 데이터 확인 중")
    else:
        logger.info("고가 물건 위주 데이터 수집 시작 (밸류옥션 API)")
    logger.info(f"수집 범위: 감정가 {min_price:,}원 이상 최신 {target_count}건")
    logger.info("=" * 80)

    # 현재 데이터 확인
    import sqlite3
    conn = sqlite3.connect("data/predictions.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM predictions
        WHERE verified = 1 AND actual_price > 0 AND 감정가 > ?
    """, (min_price,))
    current_count = cursor.fetchone()[0]
    conn.close()

    logger.info(f"현재 {min_price/100000000:.0f}억 초과 데이터: {current_count}건")

    if continuous:
        logger.info(f"💡 지속적 수집 모드: API에서 최신 {target_count}건 확인 후 새로운 데이터만 추가")
    else:
        logger.info(f"추가 필요: {target_count - current_count}건")

    # 수집기 초기화
    collector = ValueAuctionCollector()

    # 밸류옥션 API로 최신 낙찰 물건 수집
    # 최소 감정가 필터 적용
    logger.info(f"\n밸류옥션 API 호출: 감정가 {min_price:,}원 이상 최신 데이터")

    stats = collector.collect_and_verify(
        max_items=target_count,
        start_offset=0,
        min_appraisal_price=min_price,  # 고가 물건 필터
        continuous=continuous,  # 지속적 수집 모드 전달
        days_limit=days_limit  # 날짜 제한
    )

    # 결과 요약
    logger.info("\n" + "=" * 80)
    logger.info("수집 완료!")
    logger.info("=" * 80)
    logger.info(f"총 가져옴: {stats['total_fetched']}건")
    logger.info(f"낙찰 완료: {stats['total_processed']}건")
    logger.info(f"낙찰 미완료: {stats.get('not_sold', 0)}건 (건너뜀)")
    if stats.get('too_old', 0) > 0:
        logger.info(f"날짜 범위 초과: {stats.get('too_old', 0)}건 (건너뜀)")
    logger.info(f"중복 건너뜀: {stats.get('duplicates', 0)}건")
    logger.info(f"데이터 부족: {stats['skipped']}건")
    logger.info(f"오류: {stats['errors']}건")

    # 최종 데이터 확인
    conn = sqlite3.connect("data/predictions.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM predictions
        WHERE verified = 1 AND actual_price > 0 AND 감정가 > ?
    """, (min_price,))
    final_count = cursor.fetchone()[0]
    conn.close()

    logger.info(f"\n최종 {min_price/100000000:.0f}억 초과 데이터: {final_count}건 (증가: +{final_count - current_count}건)")

    # 다음 단계 안내
    if stats['total_processed'] > 0:
        logger.info("\n📋 다음 단계:")
        logger.info("  1. python auto_pipeline.py --skip-collect (재학습)")
        logger.info("  2. 웹 UI에서 정확도 개선 확인")

    return stats

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='고가 물건 데이터 수집 (밸류옥션 API)')
    parser.add_argument('--target', type=int, default=150,
                        help='목표 수집 건수 (기본값: 150)')
    parser.add_argument('--min-price', type=int, default=1_000_000_000,
                        help='최소 감정가 (기본값: 10억)')
    parser.add_argument('--continuous', action='store_true',
                        help='지속적 수집 모드: 기존 데이터 개수 무시하고 항상 최신 데이터 확인 (권장)')
    parser.add_argument('--days', type=int, default=None,
                        help='최근 N일 이내 데이터만 수집 (예: --days 90 → 최근 3개월)')

    args = parser.parse_args()

    try:
        stats = collect_high_price_items(
            target_count=args.target,
            min_price=args.min_price,
            continuous=args.continuous,
            days_limit=args.days
        )

        if stats['total_processed'] > 0:
            logger.info("\n✅ 고가 물건 수집 성공!")
            sys.exit(0)
        else:
            logger.warning("\n⚠️ 수집된 데이터가 없습니다")
            logger.info("💡 감정가 기준을 낮춰보세요: --min-price 500000000")
            sys.exit(1)

    except Exception as e:
        logger.error(f"\n❌ 치명적 오류: {e}", exc_info=True)
        sys.exit(1)
