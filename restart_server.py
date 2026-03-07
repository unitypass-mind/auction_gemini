"""
서버 재시작 스크립트
실행 중인 서버를 찾아서 종료하고 새로 시작합니다.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import subprocess
import time
import psutil
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_server_process():
    """실행 중인 서버 프로세스 찾기"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and 'python' in proc.info['name'].lower():
                # main.py를 실행 중인 프로세스 찾기
                if any('main.py' in str(arg) for arg in cmdline):
                    return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def stop_server():
    """서버 중지"""
    logger.info("실행 중인 서버를 찾는 중...")
    proc = find_server_process()

    if proc:
        logger.info(f"서버 프로세스 발견: PID {proc.pid}")
        logger.info("서버를 종료하는 중...")

        try:
            proc.terminate()
            proc.wait(timeout=10)
            logger.info("✅ 서버가 정상적으로 종료되었습니다")
            return True
        except psutil.TimeoutExpired:
            logger.warning("서버가 응답하지 않습니다. 강제 종료를 시도합니다...")
            proc.kill()
            logger.info("✅ 서버가 강제 종료되었습니다")
            return True
        except Exception as e:
            logger.error(f"서버 종료 중 오류: {e}")
            return False
    else:
        logger.info("실행 중인 서버가 없습니다")
        return True

def start_server():
    """서버 시작"""
    logger.info("새 서버를 시작하는 중...")

    try:
        # 백그라운드에서 서버 시작
        if os.name == 'nt':  # Windows
            # Windows에서는 CREATE_NEW_CONSOLE 플래그 사용
            subprocess.Popen(
                ['python', 'main.py'],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:  # Linux/Mac
            subprocess.Popen(
                ['python', 'main.py'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

        # 서버가 시작될 때까지 대기
        time.sleep(3)

        # 서버가 정상적으로 시작되었는지 확인
        proc = find_server_process()
        if proc:
            logger.info(f"✅ 서버가 성공적으로 시작되었습니다 (PID: {proc.pid})")
            logger.info("서버 주소: http://localhost:8000")
            return True
        else:
            logger.error("❌ 서버 시작 확인 실패")
            return False

    except Exception as e:
        logger.error(f"서버 시작 중 오류: {e}")
        return False

def main():
    """메인 함수"""
    logger.info("=" * 60)
    logger.info("🔄 서버 재시작")
    logger.info("=" * 60)

    # 1. 서버 중지
    if not stop_server():
        logger.error("서버 중지 실패")
        return False

    # 잠시 대기
    time.sleep(2)

    # 2. 서버 시작
    if not start_server():
        logger.error("서버 시작 실패")
        return False

    logger.info("=" * 60)
    logger.info("✅ 서버 재시작 완료!")
    logger.info("=" * 60)
    return True

if __name__ == "__main__":
    try:
        # psutil 설치 확인
        import psutil
    except ImportError:
        logger.error("psutil이 설치되어 있지 않습니다.")
        logger.info("설치 명령: pip install psutil")
        sys.exit(1)

    success = main()
    sys.exit(0 if success else 1)
