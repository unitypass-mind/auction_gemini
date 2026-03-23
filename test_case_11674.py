import requests
import json

# 사건번호 11674 테스트
case_no = "2025타경11674"
url = f"https://auction-ai.kr/auction?case_no={case_no}"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()

    # 경매 정보
    auction_info = data.get('data', {}).get('auction_info', {})
    print("=== 경매 정보 ===")
    print(f"사건번호: {auction_info.get('사건번호')}")
    print(f"실제 낙찰가: {auction_info.get('낙찰가'):,}원" if auction_info.get('낙찰가') else "낙찰가: 없음")

    # AI 예측가
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

    # case_no 확인
    print(f"\n=== 디버그 정보 ===")
    print(f"API로 받은 case_no: {auction_info.get('case_no')}")

else:
    print(f"Error: {response.status_code}")
    print(response.text)
