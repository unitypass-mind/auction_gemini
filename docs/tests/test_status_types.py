# -*- coding: utf-8 -*-
"""
ValueAuction API 상태별 검색 테스트
진행중 물건을 찾을 수 있는지 확인
"""

import requests
import json

api_url = "https://valueauction.co.kr/api/search"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Referer": "https://valueauction.co.kr/search",
    "Origin": "https://valueauction.co.kr"
}

print("=" * 80)
print("ValueAuction API 상태별 검색 테스트")
print("=" * 80)

# 다양한 상태 시도
status_options = [
    None,           # 상태 필터 없음 (전체)
    "전체",
    "낙찰",
    "진행중",
    "예정",
    "유찰",
    "취하",
    "매각",
    "진행",
    "upcoming",     # 영문으로 시도
    "ongoing",
    "sold",
]

for status in status_options:
    payload = {
        "limit": 5,
        "offset": 0,
        "order": "bidding_date",
        "direction": "desc"
    }

    if status is not None:
        payload["status"] = status

    status_label = f"'{status}'" if status else "없음 (전체)"

    print(f"\n{'='*80}")
    print(f"상태: {status_label}")
    print("-" * 80)

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            total = data.get('estimateTotal', 0)
            results = data.get('results', [])

            print(f"Status Code: 200 OK")
            print(f"총 건수: {total:,}건")
            print(f"반환: {len(results)}건")

            if results:
                print(f"\n예시 물건:")
                for item in results[:3]:
                    case_no = item.get('case', {}).get('name', 'N/A')
                    auction_status = item.get('auction', {}).get('status', 'N/A')
                    address = item.get('address', 'N/A')[:40]
                    appraisal = item.get('price', {}).get('appraisal_price', 0)
                    selling = item.get('price', {}).get('selling_price', 0)

                    print(f"  - {case_no}")
                    print(f"    상태: {auction_status}")
                    print(f"    주소: {address}...")
                    print(f"    감정가: {appraisal:,}원")
                    print(f"    낙찰가: {selling:,}원" if selling > 0 else f"    낙찰가: (미정)")
                    print()
        else:
            print(f"Status Code: {response.status_code}")
            print(f"Error: {response.text[:200]}")

    except Exception as e:
        print(f"오류: {e}")

print("\n" + "=" * 80)
print("특정 사건번호로 진행중 검색 테스트: 2024타경579705")
print("=" * 80)

# 진행중 상태에서 특정 사건번호 검색
for status in [None, "진행중", "예정", "진행"]:
    payload = {
        "query": "2024타경579705",
        "limit": 100,
        "offset": 0
    }

    if status:
        payload["status"] = status

    status_label = status if status else "전체"
    print(f"\n상태 '{status_label}'로 검색:")

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            total = data.get('estimateTotal', 0)
            results = data.get('results', [])

            print(f"  총 건수: {total:,}건")

            # 목표 사건번호 찾기
            for item in results:
                item_case_no = item.get('case', {}).get('name', '')
                if '579705' in item_case_no or '2024타경579705' in item_case_no:
                    print(f"  ✓ 찾았습니다!")
                    print(f"    사건번호: {item_case_no}")
                    print(f"    상태: {item.get('auction', {}).get('status', 'N/A')}")
                    print(f"    감정가: {item.get('price', {}).get('appraisal_price', 0):,}원")
                    break
            else:
                if results:
                    print(f"  찾지 못함")

    except Exception as e:
        print(f"  오류: {e}")

print("\n" + "=" * 80)
print("결론")
print("=" * 80)
print("""
ValueAuction API 상태 필드:
- 적절한 상태값을 찾아서 진행중 물건을 조회해야 함
- 2024타경579705가 진행중 상태로 등록되어 있는지 확인 필요
- 상태 필터 없이 검색하면 전체 데이터 조회 가능
""")
