"""
과거 낙찰 데이터 대량 수집 스크립트
- ValueAuction API에서 과거 2년간 낙찰 완료된 데이터 수집
- 중복 체크하여 새로운 데이터만 추가
"""
import sys
from valueauction_collector import ValueAuctionCollector
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def collect_historical_data(days=730, max_items=10000):
    """
    과거 데이터 대량 수집

    Args:
        days: 수집할 과거 기간 (기본: 730일 = 2년)
        max_items: 최대 수집 항목 수 (기본: 10000건)
    """
    collector = ValueAuctionCollector()

    logger.info("="*80)
    logger.info(f"과거 낙찰 데이터 대량 수집 시작")
    logger.info(f"   - 수집 기간: 최근 {days}일 ({days//365}년)")
    logger.info(f"   - 최대 항목: {max_items}건")
    logger.info("="*80)

    # 대량 수집 (중복 체크하면서 새 데이터만 추가)
    stats = collector.collect_and_verify(
        max_items=max_items,
        start_offset=0,
        min_appraisal_price=0,
        continuous=True,  # 중복 만나도 계속 진행
        days_limit=days   # 과거 N일
    )

    logger.info("\n" + "="*80)
    logger.info("[수집 통계]")
    logger.info("="*80)
    logger.info(f"API에서 확인한 총 데이터: {stats['total_fetched']}건")
    logger.info(f"[OK] 새로 추가된 데이터: {stats['total_processed']}건")
    logger.info(f"[SKIP] 중복 건너뜀: {stats['duplicates']}건")
    logger.info(f"[FAIL] 낙찰 미완료: {stats['not_sold']}건")
    logger.info(f"[OLD] 날짜 범위 초과: {stats['too_old']}건")
    logger.info(f"[WARN] 건너뜀 (기타): {stats['skipped']}건")
    logger.info(f"[ERROR] 오류: {stats['errors']}건")
    logger.info("="*80)

    return stats


if __name__ == "__main__":
    try:
        # 사용자에게 확인
        print("\n" + "="*80)
        print("[과거 낙찰 데이터 대량 수집]")
        print("="*80)
        print("현재 DB에는 약 1,360건의 검증된 낙찰 데이터가 있습니다.")
        print("\n수집 옵션:")
        print("  1. 과거 1년 데이터 (최대 5,000건)")
        print("  2. 과거 2년 데이터 (최대 10,000건)")
        print("  3. 과거 3년 데이터 (최대 15,000건)")
        print("  4. 커스텀 설정")
        print()

        choice = input("선택하세요 (1-4, 또는 'q'로 종료): ").strip()

        if choice == 'q':
            logger.info("사용자가 취소했습니다.")
            sys.exit(0)

        if choice == '1':
            days, max_items = 365, 5000
        elif choice == '2':
            days, max_items = 730, 10000
        elif choice == '3':
            days, max_items = 1095, 15000
        elif choice == '4':
            days = int(input("수집 기간 (일): "))
            max_items = int(input("최대 항목 수: "))
        else:
            logger.error("잘못된 선택입니다.")
            sys.exit(1)

        print(f"\n[시작] 수집 시작: 최근 {days}일, 최대 {max_items}건")
        print("[INFO] 예상 소요 시간: API 속도에 따라 수 분~수십 분 소요될 수 있습니다.")
        print()

        confirm = input("계속하시겠습니까? (y/n): ").strip().lower()
        if confirm != 'y':
            logger.info("사용자가 취소했습니다.")
            sys.exit(0)

        stats = collect_historical_data(days=days, max_items=max_items)

        if stats['total_processed'] > 0:
            logger.info(f"\n[SUCCESS] {stats['total_processed']}건의 새로운 낙찰 데이터가 추가되었습니다!")
            logger.info("\n[다음 단계]")
            logger.info("  1. python create_pattern_tables.py  # 패턴 테이블 재생성")
            logger.info("  2. python train_model_v4.py         # 모델 재학습")
            logger.info("  3. 서버 재시작                       # 새 모델 적용")
            sys.exit(0)
        else:
            logger.info("\n[INFO] 새로운 데이터가 없습니다.")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\n\n사용자가 중단했습니다.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n데이터 수집 중 오류 발생: {e}", exc_info=True)
        sys.exit(1)
