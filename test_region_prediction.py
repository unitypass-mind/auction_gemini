# -*- coding: utf-8 -*-
import requests
import json
import urllib3
urllib3.disable_warnings()

url = 'https://49.50.131.190/predict/simple'

# 테스트 1: 인천
data_incheon = {
    'start_price': 300000000,
    'property_type': '아파트',
    'region': '인천',
    'area': 84.0,
    'auction_round': 1
}

# 테스트 2: 서울
data_seoul = {
    'start_price': 300000000,
    'property_type': '아파트',
    'region': '서울',
    'area': 84.0,
    'auction_round': 1
}

print("=" * 60)
print("테스트 1: 인천")
print("=" * 60)
response1 = requests.post(url, json=data_incheon, verify=False, timeout=30)
result1 = response1.json()
if result1.get('success'):
    data1 = result1.get('data', {})
    print(f"감정가: {data1.get('start_price'):,}원")
    print(f"예측 낙찰가: {data1.get('predicted_price'):,}원")
    print(f"낙찰률: {data1.get('bid_ratio')}%")

print("\n" + "=" * 60)
print("테스트 2: 서울")
print("=" * 60)
response2 = requests.post(url, json=data_seoul, verify=False, timeout=30)
result2 = response2.json()
if result2.get('success'):
    data2 = result2.get('data', {})
    print(f"감정가: {data2.get('start_price'):,}원")
    print(f"예측 낙찰가: {data2.get('predicted_price'):,}원")
    print(f"낙찰률: {data2.get('bid_ratio')}%")

print("\n" + "=" * 60)
print("결과 비교")
print("=" * 60)
if result1.get('success') and result2.get('success'):
    pred1 = result1['data']['predicted_price']
    pred2 = result2['data']['predicted_price']
    if pred1 == pred2:
        print("⚠️  문제: 인천과 서울의 예측가가 동일합니다!")
    else:
        print(f"✓ 정상: 예측가 차이 = {abs(pred1 - pred2):,}원")
