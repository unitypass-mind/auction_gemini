import requests
import json

url = "https://auction-ai.kr/accuracy"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()

    # 최근 검증 결과 확인
    recent = data.get('recent_verified', [])

    print("=== 최근 검증 결과 ===")
    for item in recent[:10]:
        case_no = item.get('case_no') or item.get('사건번호', '')
        if '1562' in case_no:
            print(f"\n사건번호: {case_no}")
            print(f"예측: {item.get('predicted_price'):,}원")
            print(f"실제: {item.get('actual_price'):,}원")
            print(f"생성일: {item.get('created_at')}")
            print(json.dumps(item, ensure_ascii=False, indent=2))
            break
else:
    print(f"Error: {response.status_code}")
