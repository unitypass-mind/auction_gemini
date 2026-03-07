"""
자동 데이터 수집 스크립트 (100건)
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from valueauction_collector import ValueAuctionCollector
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """100건 자동 수집"""
    collector = ValueAuctionCollector()

    print("=" * 60)
    print("자동 데이터 수집 시작 (100건)")
    print("=" * 60)
    print()

    # 100건 수집
    stats = collector.collect_and_verify(max_items=100, start_offset=0)

    print()
    print("=" * 60)
    print("수집 완료!")
    print("=" * 60)
    print(f"가져온 데이터: {stats['total_fetched']}건")
    print(f"처리 완료: {stats['total_processed']}건")
    print(f"건너뜀: {stats['skipped']}건")
    print(f"오류: {stats['errors']}건")
    print("=" * 60)

    return stats

if __name__ == "__main__":
    main()
