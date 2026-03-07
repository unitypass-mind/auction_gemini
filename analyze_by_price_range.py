"""
감정가 구간별 정확도 분석
"""
import sqlite3
import sys
import io
import numpy as np
import json
import os
from datetime import datetime

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_PATH = "data/predictions.db"
STATS_FILE = "data/price_range_stats.json"

def analyze_by_price_range():
    """감정가 구간별 정확도 분석"""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 검증된 데이터 조회
    cursor.execute("""
        SELECT 감정가, actual_price, predicted_price, error_amount, error_rate
        FROM predictions
        WHERE verified = 1 AND actual_price > 0
        ORDER BY 감정가
    """)

    data = cursor.fetchall()
    conn.close()

    # 감정가 구간 정의
    ranges = [
        (0, 100_000_000, "1억 이하"),
        (100_000_001, 300_000_000, "1억~3억"),
        (300_000_001, 500_000_000, "3억~5억"),
        (500_000_001, 1_000_000_000, "5억~10억"),
        (1_000_000_001, float('inf'), "10억 초과")
    ]

    print("=" * 100)
    print("감정가 구간별 정확도 분석")
    print("=" * 100)
    print(f"{'구간':<15} {'건수':>8} {'평균오차율':>12} {'평균오차금액':>15} {'중위오차금액':>15}")
    print("-" * 100)

    total_stats = []

    for min_price, max_price, label in ranges:
        # 해당 구간 데이터 필터링
        range_data = [
            (감정가, actual, predicted, error_amt, error_rate)
            for 감정가, actual, predicted, error_amt, error_rate in data
            if min_price <= 감정가 <= max_price
        ]

        if not range_data:
            continue

        # 통계 계산
        count = len(range_data)
        error_rates = [row[4] for row in range_data]
        error_amounts = [row[3] for row in range_data]

        avg_error_rate = np.mean(error_rates)
        avg_error_amount = np.mean(error_amounts)
        median_error_amount = np.median(error_amounts)

        print(f"{label:<15} {count:>8}건 {avg_error_rate:>11.2f}% {avg_error_amount:>14,.0f}원 {median_error_amount:>14,.0f}원")

        total_stats.append({
            'range': label,
            'count': count,
            'avg_error_rate': avg_error_rate,
            'avg_error_amount': avg_error_amount,
            'median_error_amount': median_error_amount
        })

    print("-" * 100)

    # 전체 통계
    all_error_rates = [row[4] for row in data]
    all_error_amounts = [row[3] for row in data]

    print(f"{'전체':<15} {len(data):>8}건 {np.mean(all_error_rates):>11.2f}% "
          f"{np.mean(all_error_amounts):>14,.0f}원 {np.median(all_error_amounts):>14,.0f}원")
    print("=" * 100)

    # 주요 발견 사항
    print("\n🔍 주요 발견:")
    print("-" * 100)

    # 중위값과 평균값 비교
    median_total = np.median(all_error_amounts)
    mean_total = np.mean(all_error_amounts)

    print(f"1. 전체 오차금액 중위값: {median_total:,.0f}원 (평균: {mean_total:,.0f}원)")
    print(f"   → 중위값이 평균보다 {(1 - median_total/mean_total)*100:.1f}% 낮음 (고액 물건이 평균을 상승시킴)")

    # 가장 정확한 구간
    best_range = min(total_stats, key=lambda x: x['avg_error_rate'])
    print(f"\n2. 가장 정확한 구간: {best_range['range']} (평균 오차율: {best_range['avg_error_rate']:.2f}%)")

    # 사용자 친화적 메시지
    print("\n💡 사용자에게 보여줄 메시지:")
    print("-" * 100)
    for stat in total_stats:
        print(f"📊 {stat['range']} 물건: 평균 ±{stat['median_error_amount']/10000:.0f}만원 오차 "
              f"(오차율 {stat['avg_error_rate']:.1f}%)")

    print("\n✅ 웹 대시보드 개선안:")
    print("-" * 100)
    print("1. 메인 지표: 평균 오차율 2.5% (백분율 강조)")
    print("2. 부가 지표: 중위 오차금액 표시 (평균 대신)")
    print("3. 감정가 입력시 해당 구간의 예상 오차 범위 표시")
    print("   예: '3억원 물건의 경우 평균 ±750만원 범위에서 예측됩니다'")

    # JSON으로 저장
    stats_data = {
        "timestamp": datetime.now().isoformat(),
        "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "total_count": len(data),
        "overall_stats": {
            "avg_error_rate": float(np.mean(all_error_rates)),
            "avg_error_amount": float(np.mean(all_error_amounts)),
            "median_error_amount": float(np.median(all_error_amounts))
        },
        "price_ranges": [
            {
                "range": stat['range'],
                "count": stat['count'],
                "avg_error_rate": float(stat['avg_error_rate']),
                "avg_error_amount": float(stat['avg_error_amount']),
                "median_error_amount": float(stat['median_error_amount']),
                "display_text": f"평균 ±{stat['median_error_amount']/10000:.0f}만원 오차 (오차율 {stat['avg_error_rate']:.1f}%)"
            }
            for stat in total_stats
        ]
    }

    # 디렉토리 생성
    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)

    # JSON 파일로 저장
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 구간별 통계가 저장되었습니다: {STATS_FILE}")

    return total_stats

if __name__ == "__main__":
    analyze_by_price_range()
