import requests

# 실제 사건번호로 테스트 (ValueAuction에서 확인된 번호)
case_no = "2025타경32529"
url = f"http://localhost:8000/auction?case_no={case_no}&bidders=10"

print(f"Testing: {case_no}")
print(f"URL: {url}\n")

try:
    response = requests.get(url, timeout=60)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            info = data['data']['auction_info']
            print(f"\nSuccess!")
            print(f"  Source: {info.get('데이터소스')}")
            print(f"  Case: {info.get('사건번호')}")
            print(f"  Type: {info.get('물건종류')}")
            print(f"  Address: {info.get('소재지')[:50]}...")
            print(f"  Appraisal: {info.get('감정가')}")
            print(f"  Predicted: {data['data'].get('predicted_price_formatted')}")
        else:
            print(f"Failed: {data}")
    else:
        print(f"HTTP Error: {response.status_code}")
        print(response.text[:200])

except Exception as e:
    print(f"Exception: {e}")
