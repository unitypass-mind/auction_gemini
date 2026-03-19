import requests
import json
import urllib3
urllib3.disable_warnings()

url = 'https://49.50.131.190/auction'
params = {'case_no': '2024타경579705'}

response = requests.get(url, params=params, verify=False)
print('Status:', response.status_code)
data = response.json()

# 권리분석 정보만 출력
if data.get('success'):
    auction_info = data.get('data', {}).get('auction_info', {})
    rights = auction_info.get('권리분석', {})
    print('\n=== 권리분석 데이터 ===')
    for key, value in rights.items():
        print(f"{key}: {value}")

    print('\n=== 권리분석_원문 ===')
    print(rights.get('권리분석_원문', '(비어있음)'))
else:
    print('Error:', data.get('message'))
