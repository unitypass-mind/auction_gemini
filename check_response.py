# -*- coding: utf-8 -*-
import sys
import io
sys.stdout.reconfigure(encoding='utf-8')

import requests
import json

resp = requests.get("http://localhost:8000/auction", params={"case_no": "2024타경579705"}, timeout=60)
data = resp.json()

print("="*80)
print("응답 최상위 키:", list(data.keys()))
print("="*80)

if 'data' in data:
    print("\ndata 키:", list(data['data'].keys()))

    # market_price 확인
    print(f"\n[ 가격 정보 ]")
    print(f"감정가: {data['data'].get('auction_info', {}).get('감정가', 'N/A')}")
    print(f"시세 (market_price): {data['data'].get('market_price', 0):,}원")
    print(f"시세 formatted: {data['data'].get('market_price_formatted', 'N/A')}")
    print(f"예상낙찰가: {data['data'].get('predicted_price', 0):,}원")
    print(f"거래건수: {data['data'].get('transactions_count', 0)}건")

    # profit_analysis 확인
    if 'profit_analysis' in data['data']:
        profit = data['data']['profit_analysis']
        print(f"\n[ 수익 분석 ]")
        print(f"예상수익: {profit.get('profit', 0):,}원")
        print(f"수익률: {profit.get('profit_rate', 0):.2f}%")

    # real_transactions 확인
    if 'real_transactions' in data['data']:
        trans = data['data']['real_transactions']
        print(f"\n[ 실거래가 데이터 ] {len(trans)}건")
        for i, t in enumerate(trans[:3], 1):
            print(f"  [{i}] {t}")
    else:
        print("\n⚠️ real_transactions 키 없음 (응답에 미포함)")
else:
    print("\n❌ data 키 없음")
    print("Full response:", json.dumps(data, indent=2, ensure_ascii=False)[:500])
