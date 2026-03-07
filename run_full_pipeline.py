"""
전체 파이프라인 실행 스크립트
데이터 수집 -> 전처리 -> 모델 훈련을 한번에 실행
"""
import subprocess
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_script(script_name: str, description: str) -> bool:
    """
    Python 스크립트 실행

    Returns:
        성공 여부
    """
    logger.info("="*80)
    logger.info(f"{description} 시작")
    logger.info("="*80)

    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=True,
            capture_output=False
        )
        logger.info(f"{description} 완료")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"{description} 실패: {e}")
        return False

    except FileNotFoundError:
        logger.error(f"스크립트를 찾을 수 없습니다: {script_name}")
        return False


def main():
    """메인 함수"""
    logger.info("="*80)
    logger.info("AI 경매 예측 모델 전체 파이프라인")
    logger.info("="*80)

    print("\n실행할 단계를 선택하세요:")
    print("1. 전체 실행 (데이터 수집 -> 전처리 -> 모델 훈련)")
    print("2. 데이터 수집만")
    print("3. 전처리만 (데이터 수집 이미 완료된 경우)")
    print("4. 모델 훈련만 (전처리 이미 완료된 경우)")

    choice = input("\n선택 (1-4): ").strip()

    steps = []

    if choice == "1":
        steps = [
            ("collect_auction_data.py", "데이터 수집"),
            ("preprocess_data.py", "데이터 전처리"),
            ("train_model_advanced.py", "고급 모델 훈련"),
        ]
    elif choice == "2":
        steps = [("collect_auction_data.py", "데이터 수집")]
    elif choice == "3":
        steps = [("preprocess_data.py", "데이터 전처리")]
    elif choice == "4":
        steps = [("train_model_advanced.py", "고급 모델 훈련")]
    else:
        logger.error("잘못된 선택")
        return

    # 단계별 실행
    for script, description in steps:
        success = run_script(script, description)

        if not success:
            logger.error(f"\n파이프라인 중단: {description} 실패")
            return

        logger.info(f"\n{description} 성공\n")

    # 완료
    logger.info("="*80)
    logger.info("파이프라인 완료!")
    logger.info("="*80)

    # 생성된 파일 확인
    logger.info("\n생성된 파일:")

    files_to_check = [
        "data/auction_data.csv",
        "data/auction_data_processed.csv",
        "data/X_features.npy",
        "data/y_target.npy",
        "models/auction_model.pkl",
        "models/preprocessor.pkl",
        "models/training_results.json",
        "models/feature_importance.png",
    ]

    for file_path in files_to_check:
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024*1024:
                size_str = f"{size/1024:.1f} KB"
            else:
                size_str = f"{size/(1024*1024):.1f} MB"

            logger.info(f"  ✓ {file_path} ({size_str})")
        else:
            logger.info(f"  ✗ {file_path} (없음)")

    logger.info("\n다음 단계:")
    logger.info("  python main.py")
    logger.info("  또는")
    logger.info("  uvicorn main:app --reload")


if __name__ == "__main__":
    main()
