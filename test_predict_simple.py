# -*- coding: utf-8 -*-
import requests
import json
import urllib3
urllib3.disable_warnings()

url = 'https://49.50.131.190/predict/simple'
data = {
    'start_price': 300000000,  # 3억
    'property_type': '아파트',
    'region': '인천',
    'area': 84.0,
    'auction_round': 1
}

print(f"Testing POST {url}")
print(f"Data: {json.dumps(data, ensure_ascii=False, indent=2)}")
print("\n" + "="*60 + "\n")

try:
    response = requests.post(url, json=data, verify=False, timeout=30)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse:\n{json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get('success'):
            data_section = result.get('data', {})
            print("\n=== AI 예측 결과 ===")
            print(f"감정가: {data_section.get('start_price'):,}원")
            print(f"예측 낙찰가: {data_section.get('predicted_price'):,}원")
            print(f"예상 수익: {data_section.get('expected_profit'):,}원")
            print(f"수익률: {data_section.get('profit_rate')}%")
            print(f"낙찰률: {data_section.get('bid_ratio')}%")
    else:
        print(f"Error Response: {response.text}")

except Exception as e:
    print(f"Error: {e}")
