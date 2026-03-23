import requests

# 2025타경579705 테스트
case_no = "2025타경579705"
url = f"https://auction-ai.kr/auction?case_no={case_no}"

try:
    response = requests.get(url, timeout=10)

    print(f"Status Code: {response.status_code}")
    print(f"\nResponse Body:")

    try:
        data = response.json()
        import json
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except:
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
