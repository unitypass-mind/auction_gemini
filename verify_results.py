"""
실제 낙찰 결과 검증 스크립트

예측한 물건의 실제 낙찰가를 입력하거나 자동으로 수집합니다.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import logging
from database import db
from typing import Optional
import pandas as pd
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_from_csv(csv_path: str) -> int:
    """
    CSV 파일에서 실제 낙찰 결과를 읽어서 업데이트

    CSV 형식:
    사건번호,실제낙찰가,낙찰일자
    2024타경00001,245000000,2024-03-15
    2024타경00002,180000000,2024-03-16

    Args:
        csv_path: CSV 파일 경로

    Returns:
        업데이트된 건수
    """
    try:
        df = pd.read_csv(csv_path)
        required_columns = ['사건번호', '실제낙찰가']

        if not all(col in df.columns for col in required_columns):
            logger.error(f"필수 컬럼 누락: {required_columns}")
            return 0

        updated_count = 0

        for _, row in df.iterrows():
            case_no = row['사건번호']
            actual_price = int(row['실제낙찰가'])
            actual_date = row.get('낙찰일자')

            success = db.update_actual_result(case_no, actual_price, actual_date)

            if success:
                updated_count += 1
                logger.info(f"업데이트 완료: {case_no}")
            else:
                logger.warning(f"업데이트 실패: {case_no}")

        logger.info(f"총 {updated_count}건 업데이트 완료")
        return updated_count

    except Exception as e:
        logger.error(f"CSV 처리 실패: {e}", exc_info=True)
        return 0


def verify_manual(case_no: str, actual_price: int, actual_date: Optional[str] = None) -> bool:
    """
    수동으로 실제 낙찰가 입력

    Args:
        case_no: 사건번호
        actual_price: 실제 낙찰가
        actual_date: 낙찰 날짜 (선택)

    Returns:
        성공 여부
    """
    success = db.update_actual_result(case_no, actual_price, actual_date)

    if success:
        logger.info(f"검증 완료: {case_no} -> {actual_price:,}원")
    else:
        logger.error(f"검증 실패: {case_no}")

    return success


def show_unverified_predictions(limit: int = 20):
    """
    검증되지 않은 예측 목록 표시

    Args:
        limit: 표시할 최대 개수
    """
    unverified = db.get_unverified_predictions(limit)

    if not unverified:
        print("\n검증 대기 중인 예측이 없습니다.")
        return

    print(f"\n📋 검증 대기 중인 예측 ({len(unverified)}건):")
    print("-" * 100)
    print(f"{'No':<4} {'사건번호':<20} {'감정가':<15} {'예측 낙찰가':<15} {'예측일시':<20}")
    print("-" * 100)

    for idx, item in enumerate(unverified, 1):
        case_no = item.get('사건번호') or item.get('case_no')
        estimated = item.get('감정가', 0)
        predicted = item.get('predicted_price', 0)
        created = item.get('created_at', '')

        print(f"{idx:<4} {case_no:<20} {estimated:>13,}원 {predicted:>13,}원 {created:<20}")

    print("-" * 100)


def interactive_verify():
    """
    대화형 검증 모드
    """
    print("\n🔍 실제 낙찰 결과 검증")
    print("=" * 50)

    # 미검증 예측 목록 표시
    show_unverified_predictions(10)

    print("\n옵션:")
    print("1. 수동 입력")
    print("2. CSV 파일 업로드")
    print("3. 종료")

    choice = input("\n선택 (1-3): ").strip()

    if choice == '1':
        # 수동 입력
        case_no = input("사건번호: ").strip()
        actual_price = int(input("실제 낙찰가 (원): ").strip())
        actual_date = input("낙찰일자 (YYYY-MM-DD, 선택): ").strip() or None

        verify_manual(case_no, actual_price, actual_date)

    elif choice == '2':
        # CSV 업로드
        csv_path = input("CSV 파일 경로: ").strip()

        if Path(csv_path).exists():
            verify_from_csv(csv_path)
        else:
            print(f"파일을 찾을 수 없습니다: {csv_path}")

    elif choice == '3':
        print("종료합니다.")
        return

    else:
        print("잘못된 선택입니다.")


def show_accuracy_report():
    """
    정확도 리포트 출력
    """
    stats = db.get_accuracy_stats(days=30)

    print("\n📊 AI 모델 정확도 리포트 (최근 30일)")
    print("=" * 60)
    print(f"총 예측 건수:     {stats.get('total_predictions', 0):>5}건")
    print(f"검증 완료:        {stats.get('verified_predictions', 0):>5}건")
    print(f"검증률:          {stats.get('verification_rate', 0):>5.1f}%")
    print("-" * 60)
    print(f"평균 오차율:      {stats.get('avg_error_rate', 0):>5.2f}%")
    print(f"평균 오차 금액:   {stats.get('avg_error_amount', 0):>13,}원")
    print(f"최고 정확도:      {stats.get('best_accuracy', 0) or 0:>5.2f}%")
    print(f"최저 정확도:      {stats.get('worst_accuracy', 0) or 0:>5.2f}%")
    print("=" * 60)

    # 검증된 예측 목록
    verified = db.get_recent_predictions(limit=10, verified_only=True)

    if verified:
        print(f"\n✅ 최근 검증된 예측 ({len(verified)}건)")
        print("-" * 100)
        print(f"{'사건번호':<20} {'예측가':<15} {'실제가':<15} {'오차':<15} {'오차율':<10}")
        print("-" * 100)

        for item in verified:
            case_no = item.get('사건번호') or item.get('case_no')
            predicted = item.get('predicted_price', 0)
            actual = item.get('actual_price', 0)
            error = item.get('error_amount', 0)
            error_rate = item.get('error_rate', 0)

            print(f"{case_no:<20} {predicted:>13,}원 {actual:>13,}원 {error:>13,}원 {error_rate:>8.2f}%")

        print("-" * 100)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "report":
            # 정확도 리포트
            show_accuracy_report()

        elif command == "list":
            # 미검증 목록
            show_unverified_predictions(20)

        elif command == "verify" and len(sys.argv) >= 4:
            # 수동 검증
            case_no = sys.argv[2]
            actual_price = int(sys.argv[3])
            actual_date = sys.argv[4] if len(sys.argv) > 4 else None

            verify_manual(case_no, actual_price, actual_date)

        elif command == "csv" and len(sys.argv) >= 3:
            # CSV 업로드
            csv_path = sys.argv[2]
            verify_from_csv(csv_path)

        else:
            print("사용법:")
            print("  python verify_results.py report                              # 정확도 리포트")
            print("  python verify_results.py list                                # 미검증 목록")
            print("  python verify_results.py verify <사건번호> <낙찰가> [날짜]   # 수동 검증")
            print("  python verify_results.py csv <파일경로>                      # CSV 업로드")

    else:
        # 대화형 모드
        interactive_verify()
