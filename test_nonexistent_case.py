import requests

# 존재하지 않는 사건번호로 테스트
case_no = "2024타경999999999"  # 확실히 존재하지 않을 사건번호
url = f"https://auction-ai.kr/auction?case_no={case_no}"

response = requests.get(url)

print(f"Status Code: {response.status_code}")
print(f"Headers: {response.headers}")
print(f"\nResponse Body:")
print(response.text)

try:
    data = response.json()
    print(f"\nJSON Data:")
    import json
    print(json.dumps(data, ensure_ascii=False, indent=2))
except:
    print("Not JSON response")
