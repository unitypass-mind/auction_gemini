"""
이상치 데이터 안전 정리 스크립트 (낙찰률 800% 초과만)
"""
import sqlite3
import sys
import io
import numpy as np

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = "data/predictions.db"

def fix_outliers_safe():
    """낙찰률 800% 초과 데이터만 verified=0으로 변경"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 100)
    print("이상치 데이터 안전 정리 (낙찰률 800% 초과만)")
    print("=" * 100)

    # 처리 전 통계
    cursor.execute("""
        SELECT COUNT(*) FROM predictions
        WHERE verified = 1 AND actual_price > 0
    """)
    before_count = cursor.fetchone()[0]
    print(f"\n처리 전 검증 데이터: {before_count}건")

    # 낙찰률 800% 초과 데이터 확인
    print("\n[처리 대상] 낙찰률 800% 초과 데이터")
    cursor.execute("""
        SELECT
            id, 감정가, actual_price,
            (actual_price * 100.0 / 감정가) as 낙찰률,
            error_rate
        FROM predictions
        WHERE verified = 1
        AND actual_price > 0
        AND (actual_price * 100.0 / 감정가) > 800
        ORDER BY 낙찰률 DESC
    """)

    outliers = cursor.fetchall()
    print(f"  발견: {len(outliers)}건\n")

    if outliers:
        for id_, 감정가, actual, 낙찰률, error_rate in outliers:
            print(f"  ID {id_}: 감정가 {감정가:,}원 → 낙찰가 {actual:,}원 (낙찰률 {낙찰률:.1f}%, 오차율 {error_rate:.1f}%)")

        # verified=0으로 변경
        cursor.execute("""
            UPDATE predictions
            SET verified = 0
            WHERE verified = 1
            AND actual_price > 0
            AND (actual_price * 100.0 / 감정가) > 800
        """)
        conn.commit()
        print(f"\n  ✅ {len(outliers)}건을 학습 데이터에서 제외 (verified=0)")
    else:
        print("  처리 대상 없음")

    # 처리 후 통계
    print("\n" + "=" * 100)
    print("처리 후 통계")
    print("=" * 100)

    cursor.execute("""
        SELECT COUNT(*) FROM predictions
        WHERE verified = 1 AND actual_price > 0
    """)
    after_count = cursor.fetchone()[0]
    print(f"\n처리 후 검증 데이터: {after_count}건 (제거: {before_count - after_count}건)")

    # 10억 초과 구간 재분석
    cursor.execute("""
        SELECT error_rate
        FROM predictions
        WHERE verified = 1
        AND actual_price > 0
        AND 감정가 > 1000000000
    """)
    error_rates_10b = [row[0] for row in cursor.fetchall()]

    if error_rates_10b:
        print(f"\n10억 초과 구간:")
        print(f"  - 건수: {len(error_rates_10b)}건")
        print(f"  - 평균 오차율: {np.mean(error_rates_10b):.2f}%")
        print(f"  - 중위 오차율: {np.median(error_rates_10b):.2f}%")
        print(f"  - 최대 오차율: {np.max(error_rates_10b):.2f}%")
    else:
        print(f"\n10억 초과 구간: 데이터 없음")

    # 전체 오차율
    cursor.execute("""
        SELECT AVG(error_rate)
        FROM predictions
        WHERE verified = 1 AND actual_price > 0
    """)
    overall_error = cursor.fetchone()[0]

    if overall_error:
        print(f"\n전체 평균 오차율: {overall_error:.2f}%")

    conn.close()

    print("\n" + "=" * 100)
    print("✅ 이상치 데이터 정리 완료!")
    print("=" * 100)
    print("\n⚠️ 다음 단계:")
    print("  1. python auto_pipeline.py --skip-collect")
    print("  2. 10억 초과 구간 오차율 재확인")

if __name__ == "__main__":
    fix_outliers_safe()
