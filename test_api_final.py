# -*- coding: utf-8 -*-
import requests
import json
import urllib3
urllib3.disable_warnings()

url = 'https://49.50.131.190/auction'
params = {'case_no': '2024타경579705'}

response = requests.get(url, params=params, verify=False, timeout=30)
data = response.json()

print(f"Status: {response.status_code}")
print(f"Success: {data.get('success')}")

if data.get('success'):
    auction_info = data.get('data', {}).get('auction_info', {})
    rights = auction_info.get('권리분석', {})
    rights_text = rights.get('권리분석_원문', '')

    print('\n=== 권리분석 데이터 ===')
    print(f"청구금액: {rights.get('청구금액', 0):,}원")
    print(f"청구금액비율: {rights.get('청구금액비율', 0)*100:.1f}%")
    print(f"\n권리분석_원문: {rights_text if rights_text else '(비어있음)'}")

    if rights_text:
        tags = rights_text.split(' / ')
        print(f"\n태그 개수: {len(tags)}")
        print("태그 목록:")
        for i, tag in enumerate(tags, 1):
            print(f"  {i}. {tag}")
else:
    print(f"Error: {data.get('message', 'Unknown error')}")
    print(f"Full response: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
