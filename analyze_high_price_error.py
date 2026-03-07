"""
10억 초과 구간 오차율 분석
"""
import sqlite3
import sys
import io
import numpy as np
import pandas as pd

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = "data/predictions.db"

def analyze_high_price_errors():
    """10억 초과 구간의 높은 오차율 원인 분석"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 10억 초과 데이터 조회
    cursor.execute("""
        SELECT 감정가, actual_price, predicted_price, error_amount, error_rate
        FROM predictions
        WHERE verified = 1 AND actual_price > 0 AND 감정가 > 1000000000
        ORDER BY 감정가
    """)

    high_price_data = cursor.fetchall()

    # 전체 데이터 조회 (비교용)
    cursor.execute("""
        SELECT 감정가, actual_price, predicted_price, error_amount, error_rate
        FROM predictions
        WHERE verified = 1 AND actual_price > 0
    """)

    all_data = cursor.fetchall()
    conn.close()

    print("=" * 100)
    print("10억 초과 구간 오차율 분석")
    print("=" * 100)

    # 기본 통계
    print(f"\n📊 기본 통계:")
    print(f"  - 10억 초과 건수: {len(high_price_data)}건")
    print(f"  - 전체 건수: {len(all_data)}건")
    print(f"  - 비율: {len(high_price_data)/len(all_data)*100:.1f}%")

    # 오차율 분포
    high_error_rates = [row[4] for row in high_price_data]
    all_error_rates = [row[4] for row in all_data]

    print(f"\n📈 오차율 비교:")
    print(f"  10억 초과 구간:")
    print(f"    - 평균: {np.mean(high_error_rates):.2f}%")
    print(f"    - 중위값: {np.median(high_error_rates):.2f}%")
    print(f"    - 최소: {np.min(high_error_rates):.2f}%")
    print(f"    - 최대: {np.max(high_error_rates):.2f}%")
    print(f"    - 표준편차: {np.std(high_error_rates):.2f}%")

    print(f"\n  전체 구간:")
    print(f"    - 평균: {np.mean(all_error_rates):.2f}%")
    print(f"    - 중위값: {np.median(all_error_rates):.2f}%")
    print(f"    - 표준편차: {np.std(all_error_rates):.2f}%")

    # 이상치 분석
    print(f"\n🔍 이상치 분석:")
    # 오차율 10% 이상인 경우
    high_errors = [row for row in high_price_data if row[4] > 10]
    print(f"  - 오차율 10% 이상: {len(high_errors)}건 ({len(high_errors)/len(high_price_data)*100:.1f}%)")

    # 오차율 30% 이상인 경우
    very_high_errors = [row for row in high_price_data if row[4] > 30]
    print(f"  - 오차율 30% 이상: {len(very_high_errors)}건 ({len(very_high_errors)/len(high_price_data)*100:.1f}%)")

    if very_high_errors:
        print(f"\n  극단적 이상치 예시 (오차율 30% 이상):")
        for i, (appraisal, actual, predicted, error_amt, error_rate) in enumerate(very_high_errors[:5], 1):
            print(f"    {i}. 감정가: {appraisal:,}원 | 실제: {actual:,}원 | 예측: {predicted:,}원 | 오차율: {error_rate:.1f}%")

    # 감정가 vs 실제 낙찰가 비율
    print(f"\n💰 감정가 대비 낙찰가 비율:")
    actual_ratios = [(row[1] / row[0]) * 100 for row in high_price_data]
    print(f"  - 평균: {np.mean(actual_ratios):.1f}%")
    print(f"  - 중위값: {np.median(actual_ratios):.1f}%")
    print(f"  - 최소: {np.min(actual_ratios):.1f}%")
    print(f"  - 최대: {np.max(actual_ratios):.1f}%")
    print(f"  - 표준편차: {np.std(actual_ratios):.1f}%")

    # 비교: 5억~10억 구간
    cursor = sqlite3.connect(DB_PATH).cursor()
    cursor.execute("""
        SELECT 감정가, actual_price, predicted_price, error_amount, error_rate
        FROM predictions
        WHERE verified = 1 AND actual_price > 0
        AND 감정가 > 500000000 AND 감정가 <= 1000000000
    """)
    mid_price_data = cursor.fetchall()

    mid_actual_ratios = [(row[1] / row[0]) * 100 for row in mid_price_data]
    print(f"\n  [비교] 5억~10억 구간:")
    print(f"    - 평균: {np.mean(mid_actual_ratios):.1f}%")
    print(f"    - 표준편차: {np.std(mid_actual_ratios):.1f}%")

    # 학습 데이터 불균형
    print(f"\n📚 학습 데이터 분포:")
    cursor.execute("""
        SELECT COUNT(*) as cnt,
               AVG(감정가) as avg_appraisal
        FROM predictions
        WHERE verified = 1 AND actual_price > 0
        AND 감정가 <= 1000000000
    """)
    low_count, low_avg = cursor.fetchone()

    print(f"  - 10억 이하: {low_count}건 (평균 감정가: {low_avg:,.0f}원)")
    print(f"  - 10억 초과: {len(high_price_data)}건")
    print(f"  - 데이터 불균형 비율: 1 : {low_count/len(high_price_data):.1f}")

    # 주요 원인 분석
    print(f"\n" + "=" * 100)
    print("🎯 높은 오차율의 주요 원인")
    print("=" * 100)

    print(f"\n1. ⚠️ 데이터 부족 (희소성)")
    print(f"   - 10억 초과 물건은 전체의 {len(high_price_data)/len(all_data)*100:.1f}%에 불과")
    print(f"   - 학습 데이터 {len(high_price_data)}건으로는 패턴 학습 어려움")

    print(f"\n2. 📊 변동성 증가")
    print(f"   - 낙찰가 비율 표준편차: {np.std(actual_ratios):.1f}% (5억~10억: {np.std(mid_actual_ratios):.1f}%)")
    print(f"   - 고가 물건일수록 시장 변동성이 큼")

    if very_high_errors:
        print(f"\n3. 🔴 극단적 이상치 존재")
        print(f"   - 오차율 30% 이상: {len(very_high_errors)}건 ({len(very_high_errors)/len(high_price_data)*100:.1f}%)")
        print(f"   - 이상치가 평균을 크게 상승시킴")

        # 이상치 제거 시 평균
        normal_errors = [rate for rate in high_error_rates if rate <= 30]
        if normal_errors:
            print(f"   - 이상치 제거 시 평균 오차율: {np.mean(normal_errors):.2f}%")

    print(f"\n4. 🏠 고가 물건의 특수성")
    print(f"   - 희귀성, 위치, 시장 심리 등 복잡한 요인")
    print(f"   - 단순 회귀 모델로 예측 한계")

    print("\n" + "=" * 100)
    print("💡 개선 방안")
    print("=" * 100)

    print("\n1. 더 많은 고가 데이터 수집")
    print("   - 현재 60건 → 목표 200건 이상")

    print("\n2. 이상치 처리")
    print("   - 극단적 이상치 제거 또는 별도 처리")

    print("\n3. 구간별 별도 모델 학습")
    print("   - 10억 초과는 전용 모델 사용")

    print("\n4. 앙상블 기법 적용")
    print("   - 여러 모델 결합으로 안정성 향상")

    print("\n5. 사용자에게 불확실성 명시")
    print("   - '10억 초과 물건은 예측 정확도가 낮을 수 있습니다' 안내")

if __name__ == "__main__":
    analyze_high_price_errors()
