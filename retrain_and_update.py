"""
전체 파이프라인: 데이터 수집 → 모델 재학습 → 서버 재시작
"""

import subprocess
import sys
import logging
from pathlib import Path
import shutil
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(cmd, description):
    """커맨드 실행"""
    logger.info(f"\n{'='*80}")
    logger.info(f"📌 {description}")
    logger.info(f"{'='*80}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 실행 실패: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return False


def backup_model():
    """현재 모델 백업"""
    model_path = Path("models/auction_model_v4.pkl")
    if model_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path(f"models/backups/auction_model_v4_{timestamp}.pkl")
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(model_path, backup_path)
        logger.info(f"✅ 모델 백업 완료: {backup_path}")
        return True
    return False


def main():
    """전체 파이프라인 실행"""
    logger.info("\n" + "="*80)
    logger.info("🚀 AI 모델 재학습 및 업데이트 파이프라인 시작")
    logger.info("="*80)

    # 1. 최근 낙찰 데이터 수집
    logger.info("\n📊 Step 1: 최근 낙찰 데이터 수집")
    if not run_command("python collect_recent_sold.py", "낙찰 데이터 수집"):
        logger.warning("⚠️  새로운 데이터가 없거나 수집 실패")
        response = input("\n계속 진행하시겠습니까? (y/n): ").strip().lower()
        if response != 'y':
            logger.info("중단되었습니다.")
            return

    # 2. 현재 모델 백업
    logger.info("\n💾 Step 2: 현재 모델 백업")
    backup_model()

    # 3. 패턴 테이블 생성
    logger.info("\n🔍 Step 3: 과거 패턴 테이블 생성")
    if not run_command("python create_pattern_tables.py", "패턴 테이블 생성"):
        logger.error("❌ 패턴 테이블 생성 실패")
        return

    # 4. 모델 재학습
    logger.info("\n🤖 Step 4: AI 모델 v4 재학습")
    if not run_command("python train_model_v4.py", "모델 재학습"):
        logger.error("❌ 모델 재학습 실패")
        return

    # 5. 정확도 확인
    logger.info("\n📊 Step 5: 모델 성능 평가")
    # 재학습 결과는 train_model_v4.py에서 출력됨

    # 6. 서버 재시작
    logger.info("\n🔄 Step 6: 서버 재시작")
    logger.info("서버를 수동으로 재시작해주세요:")
    logger.info("  1. Ctrl+C로 현재 서버 중지")
    logger.info("  2. python main.py 실행")

    logger.info("\n" + "="*80)
    logger.info("✅ 파이프라인 완료!")
    logger.info("="*80)
    logger.info("\n다음 단계:")
    logger.info("1. 웹 브라우저에서 '정확도' 탭 확인")
    logger.info("2. 테스트 물건으로 예측 정확도 검증")
    logger.info("="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n사용자가 중단했습니다.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n예상치 못한 오류: {e}", exc_info=True)
        sys.exit(1)
