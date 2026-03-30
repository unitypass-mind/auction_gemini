"""
ValueAuction API 페이지네이션 테스트
"""
import requests
import json
import time

api_url = "https://valueauction.co.kr/api/search"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Content-Type": "application/json",
    "Referer": "https://valueauction.co.kr/",
    "Origin": "https://valueauction.co.kr"
}

print("=== 페이지네이션 테스트 ===\n")

# 첫 페이지
payload = {
    "auctionType": "auction",
    "limit": 100,
    "offset": 0
}

response = requests.post(api_url, json=payload, headers=headers, timeout=30)
if response.status_code == 200:
    data = response.json()
    print(f"limit: {data.get('limit')}")
    print(f"offset: {data.get('offset')}")
    print(f"count: {data.get('count')} (이번 응답의 결과 수)")
    print(f"estimateTotal: {data.get('estimateTotal')} (예상 전체 결과 수)")
    print(f"실제 results 길이: {len(data.get('results', []))}")

    # 낙찰가 있는 항목 수
    winning_count = 0
    for item in data.get('results', []):
        histories = item.get('histories', [])
        for history in histories:
            if history.get('winning_price', 0) > 0:
                winning_count += 1
                break

    print(f"낙찰가 있는 항목: {winning_count}/{len(data.get('results', []))}")

    estimate_total = data.get('estimateTotal', 0)
    print(f"\n예상 필요 페이지 수 (limit=100): {(estimate_total // 100) + 1}")

print("\n=== offset=100 테스트 ===\n")
time.sleep(1)

payload = {
    "auctionType": "auction",
    "limit": 100,
    "offset": 100
}

response = requests.post(api_url, json=payload, headers=headers, timeout=30)
if response.status_code == 200:
    data = response.json()
    print(f"두 번째 페이지 결과 수: {len(data.get('results', []))}")

    winning_count = 0
    for item in data.get('results', []):
        histories = item.get('histories', [])
        for history in histories:
            if history.get('winning_price', 0) > 0:
                winning_count += 1
                break

    print(f"낙찰가 있는 항목: {winning_count}/{len(data.get('results', []))}")
