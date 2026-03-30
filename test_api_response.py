"""
ValueAuction API 응답 분석 스크립트
"""
import requests
import json

api_url = "https://valueauction.co.kr/api/search"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Content-Type": "application/json",
    "Referer": "https://valueauction.co.kr/",
    "Origin": "https://valueauction.co.kr"
}

payload = {
    "auctionType": "auction"
}

print("API 호출 중...")
response = requests.post(api_url, json=payload, headers=headers, timeout=30)
print(f"Status: {response.status_code}\n")

if response.status_code == 200:
    data = response.json()
    results = data.get('results', [])

    print(f"총 결과 수: {len(results)}")
    print(f"\n=== 처음 10개 항목 분석 ===")

    winning_count = 0
    for i, item in enumerate(results[:10]):
        case_name = item.get('case', {}).get('name', 'N/A')
        histories = item.get('histories', [])

        # winning_price 확인
        has_winning = False
        winning_price = 0
        for history in histories:
            wp = history.get('winning_price', 0)
            if wp and wp > 0:
                has_winning = True
                winning_price = wp
                break

        if has_winning:
            winning_count += 1

        print(f"{i+1}. {case_name}")
        print(f"   - has winning_price: {has_winning} ({winning_price:,}원)" if has_winning else f"   - has winning_price: {has_winning}")
        print(f"   - histories count: {len(histories)}")
        if histories:
            print(f"   - history keys: {list(histories[0].keys())[:5]}")

    print(f"\n낙찰가 있는 항목: {winning_count}/10")

    # 전체 결과에서 낙찰가 있는 항목 카운트
    total_winning = 0
    for item in results:
        histories = item.get('histories', [])
        for history in histories:
            if history.get('winning_price', 0) > 0:
                total_winning += 1
                break

    print(f"전체 낙찰가 있는 항목: {total_winning}/{len(results)}")

    # API 응답 구조 확인
    print(f"\n=== API 응답 구조 ===")
    print(f"응답 최상위 키: {list(data.keys())}")

    if 'pagination' in data:
        print(f"페이지네이션 정보: {data['pagination']}")
else:
    print(f"API 오류: {response.status_code}")
    print(response.text[:500])
