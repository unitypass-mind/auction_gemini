"""
이상치 데이터 검증 스크립트
"""
import sqlite3
import sys
import io

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = "data/predictions.db"

def verify_outliers():
    """이상치 데이터 상세 검증"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 오차율 30% 이상인 10억 초과 데이터 조회 (모든 컬럼)
    cursor.execute("""
        SELECT
            id, 사건번호, 물건번호, 감정가, actual_price, predicted_price,
            error_amount, error_rate, 물건종류, 지역, created_at
        FROM predictions
        WHERE verified = 1
        AND actual_price > 0
        AND 감정가 > 1000000000
        AND error_rate > 30
        ORDER BY error_rate DESC
    """)

    outliers = cursor.fetchall()

    print("=" * 120)
    print("이상치 데이터 상세 검증 (오차율 30% 이상)")
    print("=" * 120)
    print(f"총 {len(outliers)}건 발견\n")

    for i, row in enumerate(outliers, 1):
        (id_, 사건번호, 물건번호, 감정가, actual, predicted,
         error_amt, error_rate, 물건종류, 지역, created_at) = row

        print(f"[{i}] ID: {id_}")
        print(f"    사건번호: {사건번호}")
        print(f"    물건번호: {물건번호}")
        print(f"    물건종류: {물건종류}")
        print(f"    지역: {지역}")
        print(f"    감정가: {감정가:,}원")
        print(f"    실제 낙찰가: {actual:,}원")
        print(f"    예측 낙찰가: {predicted:,}원")
        print(f"    오차금액: {error_amt:,}원")
        print(f"    오차율: {error_rate:.2f}%")
        print(f"    낙찰률: {(actual/감정가)*100:.1f}%")
        print(f"    생성일: {created_at}")
        print()

    # 중복 데이터 확인
    print("=" * 120)
    print("중복 데이터 분석")
    print("=" * 120)

    cursor.execute("""
        SELECT 사건번호, 물건번호, COUNT(*) as cnt
        FROM predictions
        WHERE verified = 1
        AND actual_price > 0
        AND 감정가 > 1000000000
        AND error_rate > 30
        GROUP BY 사건번호, 물건번호
        HAVING cnt > 1
        ORDER BY cnt DESC
    """)

    duplicates = cursor.fetchall()

    if duplicates:
        print(f"중복된 데이터 발견: {len(duplicates)}건\n")
        for 사건번호, 물건번호, cnt in duplicates:
            print(f"  사건번호: {사건번호}, 물건번호: {물건번호} - {cnt}건 중복")

            # 중복 상세 정보
            cursor.execute("""
                SELECT id, actual_price, predicted_price, created_at
                FROM predictions
                WHERE 사건번호 = ? AND 물건번호 = ?
                AND verified = 1
                ORDER BY created_at
            """, (사건번호, 물건번호))

            dup_details = cursor.fetchall()
            for id_, actual, predicted, created_at in dup_details:
                print(f"    - ID {id_}: 실제 {actual:,}원, 예측 {predicted:,}원 ({created_at})")
            print()
    else:
        print("중복 데이터 없음\n")

    # 낙찰률 800% 초과 데이터 확인
    print("=" * 120)
    print("비정상적 낙찰률 데이터 (낙찰률 800% 초과)")
    print("=" * 120)

    cursor.execute("""
        SELECT
            id, 사건번호, 물건번호, 감정가, actual_price,
            (actual_price * 100.0 / 감정가) as 낙찰률
        FROM predictions
        WHERE verified = 1
        AND actual_price > 0
        AND (actual_price * 100.0 / 감정가) > 800
        ORDER BY 낙찰률 DESC
    """)

    abnormal = cursor.fetchall()

    if abnormal:
        print(f"발견: {len(abnormal)}건\n")
        for id_, 사건번호, 물건번호, 감정가, actual, 낙찰률 in abnormal:
            print(f"  ID {id_}: 사건 {사건번호}-{물건번호}")
            print(f"    감정가: {감정가:,}원 → 낙찰가: {actual:,}원 (낙찰률 {낙찰률:.1f}%)")
            print(f"    ⚠️ 이는 감정가의 {낙찰률/100:.1f}배로 비정상적일 가능성 높음")
            print()
    else:
        print("비정상적 낙찰률 데이터 없음\n")

    # 권장 조치
    print("=" * 120)
    print("📋 권장 조치 사항")
    print("=" * 120)

    if duplicates:
        print("\n1. 중복 데이터 처리")
        print("   - 중복된 사건번호/물건번호의 최신 데이터만 유지")
        print("   - 또는 verified=0으로 변경하여 학습에서 제외")

    if abnormal:
        print("\n2. 비정상적 낙찰률 데이터 검증")
        print("   - 낙찰률 800% 초과 데이터는 입력 오류 가능성")
        print("   - 온비드 사이트에서 재확인 필요")
        print("   - 확인 불가능 시 verified=0으로 변경")

    if outliers:
        print("\n3. 이상치 처리 옵션")
        print("   a) 데이터 검증 후 오류 데이터 제거")
        print("   b) 오차율 50% 이상은 자동으로 verified=0 처리")
        print("   c) 10억 초과 구간 별도 모델 학습")

    conn.close()

if __name__ == "__main__":
    verify_outliers()
