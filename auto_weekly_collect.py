"""
주간 자동 데이터 수집 스크립트
매주 정해진 시간에 자동으로 데이터를 수집합니다.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from valueauction_collector import ValueAuctionCollector
import logging
import json
from datetime import datetime
import os

# 로깅 설정
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{log_dir}/weekly_collect_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 설정 파일
CONFIG_FILE = "automation_config.json"

def load_config():
    """설정 파일 로드"""
    default_config = {
        "weekly_collection_count": 100,
        "max_retries": 3,
        "start_offset": 0,
        "notification_enabled": False,
        "notification_email": ""
    }

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {**default_config, **config}
        except Exception as e:
            logger.warning(f"설정 파일 로드 실패, 기본값 사용: {e}")

    return default_config

def save_collection_history(stats):
    """수집 이력 저장"""
    history_file = "logs/collection_history.json"

    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "stats": stats
    }

    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            history = []

    history.append(history_entry)

    # 최근 100개만 유지
    if len(history) > 100:
        history = history[-100:]

    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    logger.info(f"수집 이력 저장 완료: {history_file}")

def main():
    """주간 자동 데이터 수집"""
    logger.info("=" * 80)
    logger.info("주간 자동 데이터 수집 시작")
    logger.info(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    # 설정 로드
    config = load_config()
    collection_count = config['weekly_collection_count']
    max_retries = config['max_retries']

    logger.info(f"수집 목표: {collection_count}건")
    logger.info(f"최대 재시도: {max_retries}회")

    # 수집기 초기화
    collector = ValueAuctionCollector()

    # 데이터 수집
    retry_count = 0
    stats = None

    while retry_count < max_retries:
        try:
            logger.info(f"\n데이터 수집 시작 (시도 {retry_count + 1}/{max_retries})")
            stats = collector.collect_and_verify(
                max_items=collection_count,
                start_offset=config['start_offset']
            )

            # 성공 시 탈출
            if stats['total_processed'] > 0:
                logger.info("데이터 수집 성공!")
                break
            else:
                logger.warning("처리된 데이터가 없습니다. 재시도...")
                retry_count += 1

        except Exception as e:
            logger.error(f"수집 중 오류 발생: {e}")
            retry_count += 1
            if retry_count >= max_retries:
                logger.error("최대 재시도 횟수 초과. 수집 실패.")
                stats = {
                    'total_fetched': 0,
                    'total_processed': 0,
                    'skipped': 0,
                    'errors': 1,
                    'error_message': str(e)
                }

    # 결과 출력
    logger.info("")
    logger.info("=" * 80)
    logger.info("수집 완료!")
    logger.info("=" * 80)
    logger.info(f"가져온 데이터: {stats['total_fetched']}건")
    logger.info(f"처리 완료: {stats['total_processed']}건")
    logger.info(f"건너뜀: {stats['skipped']}건")
    logger.info(f"오류: {stats['errors']}건")
    logger.info("=" * 80)

    # 이력 저장
    save_collection_history(stats)

    # 알림 발송 (옵션)
    if config['notification_enabled'] and config['notification_email']:
        logger.info(f"알림 발송: {config['notification_email']}")
        # TODO: 이메일 알림 구현

    return stats

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result['total_processed'] > 0 else 1)
    except Exception as e:
        logger.error(f"치명적 오류: {e}")
        sys.exit(1)
