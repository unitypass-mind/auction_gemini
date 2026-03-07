"""
수집된 낙찰 데이터 통계 분석
"""
import sqlite3
import sys
import io

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def analyze_bid_rates():
    """물건종류별 낙찰률 통계 분석"""
    conn = sqlite3.connect('data/predictions.db')
    cursor = conn.cursor()

    # 검증된 데이터만 조회
    cursor.execute("""
        SELECT
            물건종류,
            COUNT(*) as count,
            AVG(actual_price * 100.0 / 감정가) as avg_rate,
            MIN(actual_price * 100.0 / 감정가) as min_rate,
            MAX(actual_price * 100.0 / 감정가) as max_rate
        FROM predictions
        WHERE verified = 1 AND 감정가 > 0
        GROUP BY 물건종류
        ORDER BY count DESC
    """)

    results = cursor.fetchall()

    print("=" * 80)
    print("물건종류별 낙찰률 통계 분석")
    print("=" * 80)
    print(f"{'물건종류':<15} {'건수':>8} {'평균낙찰률':>12} {'최소':>10} {'최대':>10}")
    print("-" * 80)

    rate_map = {}
    total_count = 0
    total_rate = 0

    for row in results:
        property_type, count, avg_rate, min_rate, max_rate = row
        rate_map[property_type] = avg_rate / 100.0  # 비율로 변환
        total_count += count
        total_rate += avg_rate * count

        print(f"{property_type:<15} {count:>8}건 {avg_rate:>11.2f}% {min_rate:>9.2f}% {max_rate:>9.2f}%")

    print("-" * 80)

    # 전체 평균
    overall_avg = total_rate / total_count if total_count > 0 else 0
    print(f"{'전체 평균':<15} {total_count:>8}건 {overall_avg:>11.2f}%")
    print("=" * 80)

    # Python dict 형태로 출력
    print("\n추천 낙찰률 맵 (Python dict):")
    print("rate_map = {")
    for property_type, rate in rate_map.items():
        print(f'    "{property_type}": {rate:.3f},  # {rate*100:.1f}%')
    print("}")

    conn.close()
    return rate_map

if __name__ == "__main__":
    analyze_bid_rates()
