# -*- coding: utf-8 -*-
"""
상태 필터 제거 효과 검증
변경 전: "status": "낙찰" → 4,933건
변경 후: status 없음 → 31,567건
"""

import requests

api_url = "https://valueauction.co.kr/api/search"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

print("=" * 80)
print("ValueAuction API - 상태 필터 제거 효과 검증")
print("=" * 80)

# 변경 전: "낙찰" 상태만
print("\n[변경 전] status='낙찰'")
print("-" * 80)
payload_old = {
    "status": "낙찰",
    "limit": 1,
    "offset": 0
}

try:
    response = requests.post(api_url, json=payload_old, headers=headers, timeout=30)
    if response.status_code == 200:
        data = response.json()
        total_old = data.get('estimateTotal', 0)
        print(f"총 건수: {total_old:,}건")
except Exception as e:
    print(f"오류: {e}")

# 변경 후: 상태 필터 없음
print("\n[변경 후] status 필터 제거 (모든 상태)")
print("-" * 80)
payload_new = {
    "limit": 1,
    "offset": 0
}

try:
    response = requests.post(api_url, json=payload_new, headers=headers, timeout=30)
    if response.status_code == 200:
        data = response.json()
        total_new = data.get('estimateTotal', 0)
        print(f"총 건수: {total_new:,}건")

        # 증가율 계산
        if total_old > 0:
            increase = total_new - total_old
            increase_rate = (increase / total_old) * 100
            print(f"\n증가: +{increase:,}건 ({increase_rate:.1f}% 증가)")
except Exception as e:
    print(f"오류: {e}")

print("\n" + "=" * 80)
print("결론")
print("=" * 80)
print(f"""
변경 전: {total_old:,}건 (낙찰 상태만)
변경 후: {total_new:,}건 (모든 상태)
증가량: +{total_new - total_old:,}건

이제 주간 데이터 수집 시 6배 이상 많은 데이터를 수집할 수 있습니다.
""")
