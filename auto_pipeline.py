"""
자동 재학습 파이프라인
데이터 수집 → 이상치 제거 → 재학습 → 재예측 → 분석 → 서버 리로드를 한 번에 실행합니다.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import subprocess
import logging
import json
from datetime import datetime
import os
import time
import requests

# 로깅 설정
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{log_dir}/pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_command(command, step_name):
    """명령어 실행 및 로그 기록"""
    logger.info("=" * 80)
    logger.info(f"단계: {step_name}")
    logger.info(f"명령어: {command}")
    logger.info("=" * 80)

    start_time = time.time()

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        elapsed = time.time() - start_time

        # 표준 출력 로그
        if result.stdout:
            logger.info(f"\n{result.stdout}")

        # 표준 에러 로그
        if result.stderr:
            logger.warning(f"\nStderr:\n{result.stderr}")

        # 반환 코드 확인
        if result.returncode != 0:
            logger.error(f"오류 발생! 반환 코드: {result.returncode}")
            return False, elapsed

        logger.info(f"✅ {step_name} 완료! (소요 시간: {elapsed:.1f}초)")
        return True, elapsed

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"실행 중 예외 발생: {e}")
        return False, elapsed

def save_pipeline_result(results):
    """파이프라인 실행 결과 저장"""
    result_file = "logs/pipeline_history.json"

    pipeline_entry = {
        "timestamp": datetime.now().isoformat(),
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "results": results
    }

    history = []
    if os.path.exists(result_file):
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            history = []

    history.append(pipeline_entry)

    # 최근 50개만 유지
    if len(history) > 50:
        history = history[-50:]

    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    logger.info(f"파이프라인 실행 이력 저장 완료: {result_file}")

def main(collect_data=True, collect_count=100):
    """
    자동 재학습 파이프라인 실행

    Args:
        collect_data: 데이터 수집 여부 (False면 수집 건너뜀)
        collect_count: 수집할 데이터 건수
    """
    logger.info("=" * 80)
    logger.info("🤖 자동 재학습 파이프라인 시작")
    logger.info(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    pipeline_steps = []
    total_start_time = time.time()

    # Step 1: 데이터 수집 (선택적)
    if collect_data:
        logger.info(f"\n📥 Step 1/6: 데이터 수집 ({collect_count}건)")
        success, elapsed = run_command(
            "/root/auction_gemini/venv/bin/python3 auto_weekly_collect.py",
            "데이터 수집"
        )
        pipeline_steps.append({
            "step": "1. 데이터 수집",
            "success": success,
            "elapsed": elapsed
        })

        if not success:
            logger.error("❌ 데이터 수집 실패. 파이프라인 중단.")
            save_pipeline_result({
                "success": False,
                "failed_step": "데이터 수집",
                "steps": pipeline_steps
            })
            return False
    else:
        logger.info("\n⏭️ Step 1/6: 데이터 수집 건너뜀")

    # Step 2: 이상치 제거
    logger.info("\n🧹 Step 2/6: 이상치 데이터 제거")
    success, elapsed = run_command(
        "/root/auction_gemini/venv/bin/python3 fix_outliers_safe.py",
        "이상치 제거"
    )
    pipeline_steps.append({
        "step": "2. 이상치 제거",
        "success": success,
        "elapsed": elapsed
    })

    if not success:
        logger.warning("⚠️ 이상치 제거 실패 (치명적이지 않음, 계속 진행)")

    # Step 3: 모델 재학습
    logger.info("\n🧠 Step 3/6: 모델 재학습 (고도화 모델)")
    success, elapsed = run_command(
        "/root/auction_gemini/venv/bin/python3 train_model_enhanced.py",
        "모델 재학습 (특성 엔지니어링 + 하이퍼파라미터 튜닝 + 앙상블)"
    )
    pipeline_steps.append({
        "step": "3. 모델 재학습",
        "success": success,
        "elapsed": elapsed
    })

    if not success:
        logger.error("❌ 모델 재학습 실패. 파이프라인 중단.")
        save_pipeline_result({
            "success": False,
            "failed_step": "모델 재학습",
            "steps": pipeline_steps
        })
        return False

    # Step 4: 전체 재예측
    logger.info("\n🔮 Step 4/6: 전체 재예측")
    success, elapsed = run_command(
        "/root/auction_gemini/venv/bin/python3 update_predictions_v2.py",
        "전체 재예측"
    )
    pipeline_steps.append({
        "step": "4. 전체 재예측",
        "success": success,
        "elapsed": elapsed
    })

    if not success:
        logger.error("❌ 전체 재예측 실패. 파이프라인 중단.")
        save_pipeline_result({
            "success": False,
            "failed_step": "전체 재예측",
            "steps": pipeline_steps
        })
        return False

    # Step 5: 구간별 분석
    logger.info("\n📊 Step 5/6: 구간별 분석")
    success, elapsed = run_command(
        "/root/auction_gemini/venv/bin/python3 analyze_by_price_range.py",
        "구간별 분석"
    )
    pipeline_steps.append({
        "step": "5. 구간별 분석",
        "success": success,
        "elapsed": elapsed
    })

    if not success:
        logger.warning("⚠️ 구간별 분석 실패 (치명적이지 않음)")

    # Step 6: 서버 모델 리로드
    logger.info("\n🔄 Step 6/6: 서버 모델 리로드")
    start_time = time.time()
    server_reload_success = False

    try:
        # 서버가 실행 중인지 확인
        health_response = requests.get("http://localhost:8000/health", timeout=2)

        if health_response.status_code == 200:
            # 서버가 실행 중이면 모델 리로드
            logger.info("서버가 실행 중입니다. 모델을 리로드합니다...")
            reload_response = requests.post("http://localhost:8000/reload-model", timeout=10)

            if reload_response.status_code == 200:
                result = reload_response.json()
                logger.info(f"✅ 모델 리로드 성공!")
                logger.info(f"  - 모델 버전: {result.get('model_version')}")
                logger.info(f"  - 로드 시간: {result.get('load_time')}")
                server_reload_success = True
            else:
                logger.warning(f"⚠️ 모델 리로드 실패: HTTP {reload_response.status_code}")
        else:
            logger.warning("⚠️ 서버가 응답하지 않습니다 (서버가 실행 중이 아닐 수 있음)")

    except requests.exceptions.ConnectionError:
        logger.warning("⚠️ 서버에 연결할 수 없습니다 (서버가 실행 중이 아님)")
        logger.info("💡 서버를 시작하려면: python3 main.py")

    except Exception as e:
        logger.error(f"❌ 서버 모델 리로드 중 오류: {e}")

    elapsed = time.time() - start_time
    pipeline_steps.append({
        "step": "6. 서버 모델 리로드",
        "success": server_reload_success,
        "elapsed": elapsed
    })

    # 전체 소요 시간
    total_elapsed = time.time() - total_start_time

    # 최종 결과
    logger.info("\n" + "=" * 80)
    logger.info("🎉 파이프라인 완료!")
    logger.info("=" * 80)
    logger.info(f"전체 소요 시간: {total_elapsed:.1f}초 ({total_elapsed/60:.1f}분)")
    logger.info("\n단계별 소요 시간:")
    for step in pipeline_steps:
        status = "✅" if step['success'] else "❌"
        logger.info(f"  {status} {step['step']}: {step['elapsed']:.1f}초")
    logger.info("=" * 80)

    # 결과 저장
    save_pipeline_result({
        "success": True,
        "total_elapsed": total_elapsed,
        "steps": pipeline_steps
    })

    return True

if __name__ == "__main__":
    # 명령줄 인자 처리
    import argparse

    parser = argparse.ArgumentParser(description='자동 재학습 파이프라인')
    parser.add_argument('--skip-collect', action='store_true',
                        help='데이터 수집 건너뜀')
    parser.add_argument('--collect-count', type=int, default=100,
                        help='수집할 데이터 건수 (기본값: 100)')

    args = parser.parse_args()

    try:
        success = main(
            collect_data=not args.skip_collect,
            collect_count=args.collect_count
        )
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"치명적 오류: {e}")
        sys.exit(1)
