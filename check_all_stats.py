import requests
import json

url = "https://auction-ai.kr/accuracy"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()

    # 최근 검증 결과 확인
    recent = data.get('recent_verified', [])

    print(f"=== 최근 검증 결과 ({len(recent)}건) ===\n")

    # Case 11674 찾기
    found = False
    for item in recent:
        case_no = item.get('case_no') or item.get('사건번호', '')
        if '11674' in str(case_no):
            found = True
            print(f"사건번호: {case_no}")
            print(f"예측가: {item.get('predicted_price'):,}원")
            print(f"실제가: {item.get('actual_price'):,}원")
            error_rate = item.get('error_rate', 0)
            print(f"오차율: {error_rate:.2f}%")
            print(f"생성일: {item.get('created_at')}")
            print()
            break

    if not found:
        print("Case 11674를 찾을 수 없습니다.")
        print("\n최근 10건:")
        for i, item in enumerate(recent[:10], 1):
            case_no = item.get('case_no') or item.get('사건번호', '')
            print(f"{i}. {case_no}: 예측={item.get('predicted_price'):,}, 실제={item.get('actual_price'):,}")

else:
    print(f"Error: {response.status_code}")
