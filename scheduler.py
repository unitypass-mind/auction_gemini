"""
작업 스케줄러
Python APScheduler를 사용한 자동화 작업 스케줄링
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import subprocess
import logging
import json
import os
from datetime import datetime

# 로깅 설정
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{log_dir}/scheduler_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

CONFIG_FILE = "automation_config.json"

def load_config():
    """설정 파일 로드"""
    if not os.path.exists(CONFIG_FILE):
        logger.error(f"설정 파일을 찾을 수 없습니다: {CONFIG_FILE}")
        return None

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"설정 파일 로드 실패: {e}")
        return None

def run_script(script_name, description):
    """스크립트 실행"""
    logger.info("=" * 80)
    logger.info(f"작업 시작: {description}")
    logger.info(f"스크립트: {script_name}")
    logger.info(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    try:
        result = subprocess.run(
            f"python {script_name}",
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        if result.returncode == 0:
            logger.info(f"✅ {description} 완료")
        else:
            logger.error(f"❌ {description} 실패 (코드: {result.returncode})")
            if result.stderr:
                logger.error(f"오류: {result.stderr}")

        return result.returncode == 0

    except Exception as e:
        logger.error(f"실행 중 오류: {e}")
        return False

# 스케줄된 작업들
def job_data_collection():
    """데이터 수집 작업"""
    run_script("auto_weekly_collect.py", "주간 데이터 수집")

def job_full_pipeline():
    """전체 파이프라인 실행"""
    run_script("auto_pipeline.py", "전체 파이프라인 (재학습 포함)")

def job_performance_check():
    """성능 모니터링"""
    run_script("performance_monitor.py", "성능 모니터링")

def setup_scheduler(config):
    """스케줄러 설정"""
    scheduler = BlockingScheduler()

    # 데이터 수집 스케줄
    if config['schedule']['data_collection']['enabled']:
        collection_config = config['schedule']['data_collection']

        if collection_config['frequency'] == 'weekly':
            day_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            day = day_map.get(collection_config['day_of_week'].lower(), 0)
            hour, minute = map(int, collection_config['time'].split(':'))

            scheduler.add_job(
                job_data_collection,
                CronTrigger(day_of_week=day, hour=hour, minute=minute),
                id='data_collection',
                name='주간 데이터 수집'
            )
            logger.info(f"✅ 데이터 수집 스케줄 등록: 매주 {collection_config['day_of_week']} {collection_config['time']}")

    # 모델 재학습 스케줄
    if config['schedule']['model_retrain']['enabled']:
        retrain_config = config['schedule']['model_retrain']

        if retrain_config['frequency'] == 'weekly':
            day_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            day = day_map.get(retrain_config['day_of_week'].lower(), 0)
            hour, minute = map(int, retrain_config['time'].split(':'))

            scheduler.add_job(
                job_full_pipeline,
                CronTrigger(day_of_week=day, hour=hour, minute=minute),
                id='model_retrain',
                name='모델 재학습'
            )
            logger.info(f"✅ 모델 재학습 스케줄 등록: 매주 {retrain_config['day_of_week']} {retrain_config['time']}")

    # 성능 모니터링 스케줄
    if config['schedule']['performance_check']['enabled']:
        perf_config = config['schedule']['performance_check']

        if perf_config['frequency'] == 'daily':
            hour, minute = map(int, perf_config['time'].split(':'))

            scheduler.add_job(
                job_performance_check,
                CronTrigger(hour=hour, minute=minute),
                id='performance_check',
                name='성능 모니터링'
            )
            logger.info(f"✅ 성능 모니터링 스케줄 등록: 매일 {perf_config['time']}")

    return scheduler

def main():
    """메인 함수"""
    logger.info("=" * 80)
    logger.info("🤖 자동화 스케줄러 시작")
    logger.info("=" * 80)

    # 설정 로드
    config = load_config()
    if not config:
        logger.error("설정을 로드할 수 없습니다. 종료합니다.")
        return

    # 스케줄러 설정
    scheduler = setup_scheduler(config)

    # 등록된 작업 출력
    logger.info("\n등록된 작업:")
    for job in scheduler.get_jobs():
        logger.info(f"  - {job.name} (ID: {job.id})")
        logger.info(f"    다음 실행: {job.next_run_time}")

    logger.info("\n스케줄러가 실행 중입니다. Ctrl+C로 종료하세요.")
    logger.info("=" * 80)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("\n스케줄러를 종료합니다.")
        scheduler.shutdown()

if __name__ == "__main__":
    main()
