# -*- coding: utf-8 -*-
"""
포항시 사건 테스트
"""
import sys
import io
sys.stdout.reconfigure(encoding='utf-8')

import requests

url = "http://localhost:8000/auction"
params = {"case_no": "2025타경299"}

print("="*80)
print("포항시 사건 테스트: 2025타경299")
print("="*80)

resp = requests.get(url, params=params, timeout=60)
data = resp.json()

if 'data' in data:
    print("\n[ 물건 정보 ]")
    info = data['data']['auction_info']
    print(f"사건번호: {info.get('사건번호')}")
    print(f"소재지: {info.get('소재지')}")
    print(f"면적: {info.get('면적', 'N/A')}")

    print("\n[ 가격 정보 ]")
    print(f"감정가: {info.get('감정가')}")
    print(f"시세: {data['data'].get('market_price', 0):,}원")
    print(f"예상낙찰가: {data['data'].get('predicted_price', 0):,}원")
    print(f"실거래 건수: {data['data'].get('transactions_count', 0)}건")

    # 시세 = 감정가면 실패
    market = data['data'].get('market_price', 0)
    appraisal_str = info.get('감정가', '0원').replace('원', '').replace(',', '')
    appraisal = int(appraisal_str)

    if market == appraisal:
        print("\n❌ 실거래가 조회 실패 (시세 = 감정가)")
    else:
        print("\n✅ 실거래가 조회 성공!")
        print(f"   차이: {abs(market - appraisal):,}원")
else:
    print("Error:", data)
