# -*- coding: utf-8 -*-
"""
서버 실거래가 조회 테스트
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests

url = "http://localhost:8000/auction"
params = {"case_no": "2024타경579705"}

print("=" * 80)
print("실거래가 조회 테스트")
print("=" * 80)

try:
    resp = requests.get(url, params=params, timeout=60)
    print(f"HTTP Status: {resp.status_code}\n")

    if resp.status_code == 200:
        data = resp.json()

        if 'data' in data and 'auction_info' in data['data']:
            info = data['data']['auction_info']
            print("=" * 60)
            print("사건번호:", info.get('사건번호'))
            print("소재지:", info.get('소재지'))
            print("건물면적:", info.get('건물면적'))
            print("감정가:", info.get('감정가'))
            print("최저입찰가:", info.get('최저입찰가'))
            print("-" * 60)

            if 'real_transactions' in data['data'] and data['data']['real_transactions']:
                trans = data['data']['real_transactions']
                print(f"✅ 실거래가 데이터: {len(trans)}건")
                for i, t in enumerate(trans[:5], 1):
                    print(f"  [{i}] {t.get('아파트명')} {t.get('전용면적')}㎡ {t.get('거래금액'):,}원 ({t.get('거래년월')})")
            else:
                print("❌ 실거래가 데이터: 없음")

            print("-" * 60)

            if 'prediction' in data['data']:
                pred = data['data']['prediction']
                print(f"시세: {pred.get('market_price'):,}원")
                print(f"예상낙찰가: {pred.get('predicted_price'):,}원")

            print("=" * 60)
        else:
            print("Error:", data)
    else:
        print(f"Error: {resp.status_code}")
        print(resp.text[:500])

except Exception as e:
    print(f"Exception: {type(e).__name__}: {e}")
