import requests
import json

# 2025타경63180 물건의 예측 정보 확인
response = requests.get('http://localhost:8000/auction?case_no=2025타경63180&site=고양지원')
data = response.json()

info = data.get('data', {}).get('auction_info', {})

print('=== 경매 기본 정보 ===')
print(f"사건번호: {info.get('사건번호')}")
print(f"감정가: {info.get('감정가')}")
print(f"감정가_숫자: {info.get('감정가_숫자'):,}원")
print(f"최저입찰가: {info.get('최저입찰가'):,}원")
print(f"경매회차: {info.get('경매회차')}")

# 원본데이터에서 유찰 정보 확인
raw = info.get('원본데이터', {})
if raw:
    print(f"\n=== 원본데이터 유찰 정보 ===")
    histories = raw.get('histories', [])
    print(f"이력 개수: {len(histories)}")

    for i, hist in enumerate(histories, 1):
        print(f"\n[{i}회차]")
        print(f"  날짜: {hist.get('date')}")

        # price가 dict인지 int인지 확인
        price_data = hist.get('price', {})
        if isinstance(price_data, dict):
            selling = price_data.get('selling_price', 0)
            lowest = price_data.get('lowest_price', 0)
        else:
            selling = price_data
            lowest = 0

        print(f"  입찰가: {selling:,}원" if selling else "  입찰가: 없음")
        print(f"  최저입찰가: {lowest:,}원" if lowest else "  최저입찰가: 없음")
        print(f"  입찰자수: {hist.get('bidders', 0)}")
        print(f"  낙찰여부: {'낙찰' if hist.get('winning_info') else '유찰'}")

# 예측 정보 확인
prediction = data.get('data', {}).get('prediction', {})
print(f"\n=== 예측 정보 ===")
print(f"예측 낙찰가: {prediction.get('predicted_price_formatted')}")
print(f"예측 모드: {prediction.get('prediction_mode')}")

# 실제 낙찰 정보 확인
print(f"\n=== 실제 낙찰 정보 ===")
print(f"낙찰가: {info.get('낙찰가'):,}원" if info.get('낙찰가') else "낙찰가: (미낙찰)")
