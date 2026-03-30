"""
소규모 테스트 (50건만 수집)
"""
import sys
import sqlite3
from pathlib import Path

# collect_sold_auctions의 함수들을 임포트
sys.path.insert(0, str(Path(__file__).parent))
from collect_sold_auctions import search_valueauction_sold, extract_auction_data
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("소규모 테스트 시작 (50건)")

sold_items = search_valueauction_sold(
    region=None,
    property_type=None,
    max_results=50,
    start_offset=100
)

logger.info(f"\n수집된 항목: {len(sold_items)}건")

# 처음 5건만 데이터 추출 테스트
for i, item in enumerate(sold_items[:5], 1):
    data = extract_auction_data(item)
    if data:
        logger.info(f"\n{i}. {data['case_no']}")
        logger.info(f"   낙찰가: {data['actual_price']:,}원")
        logger.info(f"   지역: {data['지역']}")
        logger.info(f"   종류: {data['물건종류']}")
