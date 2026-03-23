import requests
import json

# API 호출
url = "https://auction-ai.kr/auction?case_no=20251562"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()

    # 경매 정보 확인
    auction_info = data.get('data', {}).get('auction_info', {})
    print("=== 경매 정보 ===")
    print(f"사건번호: {auction_info.get('사건번호')}")
    print(f"낙찰가: {auction_info.get('낙찰가')}")
    print(f"데이터소스: {auction_info.get('데이터소스')}")

    # 입찰 전략 확인
    bidding_strategy = data.get('data', {}).get('advanced_analysis', {}).get('bidding_strategy', {})
    print("\n=== 입찰 전략 ===")
    print(f"Recommendation: {bidding_strategy.get('recommendation')}")
    print(f"Message: {bidding_strategy.get('message')}")

    # 전체 응답 출력
    print("\n=== 전체 응답 (bidding_strategy) ===")
    print(json.dumps(bidding_strategy, ensure_ascii=False, indent=2))
else:
    print(f"Error: {response.status_code}")
    print(response.text)
