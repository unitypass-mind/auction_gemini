import requests
import json

# 낙찰 완료된 물건 테스트
case_no = "20251562"
url = f"https://auction-ai.kr/auction?case_no={case_no}"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()

    # 경매 정보
    auction_info = data.get('data', {}).get('auction_info', {})
    print("=== 경매 정보 ===")
    print(f"사건번호: {auction_info.get('사건번호')}")
    print(f"실제 낙찰가: {auction_info.get('낙찰가'):,}원")

    # AI 예측가 (과거 예측값 또는 실제 낙찰가)
    predicted_price = data.get('data', {}).get('predicted_price')
    print(f"\n=== AI 예측 ===")
    print(f"예측가: {predicted_price:,}원")

    # 오차 계산
    actual = auction_info.get('낙찰가', 0)
    if actual > 0 and predicted_price > 0:
        error = abs(predicted_price - actual) / actual * 100
        print(f"오차율: {error:.2f}%")

    # 입찰 전략
    bidding = data.get('data', {}).get('advanced_analysis', {}).get('bidding_strategy', {})
    print(f"\n=== 입찰 전략 ===")
    print(f"Recommendation: {bidding.get('recommendation')}")
    print(f"Message: {bidding.get('message')}")

else:
    print(f"Error: {response.status_code}")
    print(response.text)
