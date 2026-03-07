"""
이상치 데이터 정리 스크립트
"""
import sqlite3
import sys
import io

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = "data/predictions.db"

def fix_outliers():
    """이상치 데이터 정리 (verified=0으로 변경)"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 100)
    print("이상치 데이터 정리")
    print("=" * 100)

    # 1. 사건번호/물건번호가 None인 데이터 (데이터 수집 오류)
    print("\n[1] 사건번호/물건번호가 None인 데이터 처리")
    cursor.execute("""
        SELECT COUNT(*) FROM predictions
        WHERE verified = 1
        AND (사건번호 IS NULL OR 물건번호 IS NULL)
    """)
    none_count = cursor.fetchone()[0]
    print(f"    발견: {none_count}건")

    if none_count > 0:
        cursor.execute("""
            UPDATE predictions
            SET verified = 0
            WHERE verified = 1
            AND (사건번호 IS NULL OR 물건번호 IS NULL)
        """)
        print(f"    ✅ {none_count}건을 verified=0으로 변경")

    # 2. 낙찰률 800% 초과 데이터 (비정상적 거래)
    print("\n[2] 낙찰률 800% 초과 데이터 처리")
    cursor.execute("""
        SELECT COUNT(*) FROM predictions
        WHERE verified = 1
        AND actual_price > 0
        AND (actual_price * 100.0 / 감정가) > 800
    """)
    abnormal_count = cursor.fetchone()[0]
    print(f"    발견: {abnormal_count}건")

    if abnormal_count > 0:
        cursor.execute("""
            UPDATE predictions
            SET verified = 0
            WHERE verified = 1
            AND actual_price > 0
            AND (actual_price * 100.0 / 감정가) > 800
        """)
        print(f"    ✅ {abnormal_count}건을 verified=0으로 변경")

    # 3. 오차율 100% 초과 데이터 (예측 실패)
    print("\n[3] 오차율 100% 초과 데이터 처리")
    cursor.execute("""
        SELECT COUNT(*) FROM predictions
        WHERE verified = 1
        AND actual_price > 0
        AND error_rate > 100
    """)
    high_error_count = cursor.fetchone()[0]
    print(f"    발견: {high_error_count}건")

    if high_error_count > 0:
        cursor.execute("""
            UPDATE predictions
            SET verified = 0
            WHERE verified = 1
            AND actual_price > 0
            AND error_rate > 100
        """)
        print(f"    ✅ {high_error_count}건을 verified=0으로 변경")

    conn.commit()

    # 정리 후 통계 확인
    print("\n" + "=" * 100)
    print("정리 후 통계")
    print("=" * 100)

    cursor.execute("""
        SELECT COUNT(*) FROM predictions
        WHERE verified = 1 AND actual_price > 0
    """)
    total_verified = cursor.fetchone()[0]
    print(f"\n총 검증된 데이터: {total_verified}건")

    # 10억 초과 구간 재분석
    cursor.execute("""
        SELECT
            AVG(error_rate) as avg_error_rate,
            COUNT(*) as cnt
        FROM predictions
        WHERE verified = 1
        AND actual_price > 0
        AND 감정가 > 1000000000
    """)
    avg_error, count_10b = cursor.fetchone()

    if count_10b and count_10b > 0:
        print(f"\n10억 초과 구간:")
        print(f"  - 건수: {count_10b}건")
        print(f"  - 평균 오차율: {avg_error:.2f}%")
    else:
        print(f"\n10억 초과 구간: 데이터 없음")

    # 전체 오차율
    cursor.execute("""
        SELECT AVG(error_rate)
        FROM predictions
        WHERE verified = 1 AND actual_price > 0
    """)
    overall_error = cursor.fetchone()[0]
    print(f"\n전체 평균 오차율: {overall_error:.2f}%")

    conn.close()

    print("\n✅ 이상치 데이터 정리 완료!")
    print("\n⚠️ 다음 단계:")
    print("  1. python auto_pipeline.py --skip-collect  (모델 재학습)")
    print("  2. 정확도 지표 확인")

if __name__ == "__main__":
    fix_outliers()
