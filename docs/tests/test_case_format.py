import requests

print("=" * 80)
print("사건번호 형식 처리 테스트")
print("=" * 80)

test_cases = [
    "2024타경579705",  # 전체 사건번호 (6자리)
    "2024579705",      # 숫자만 (연도+6자리)
    "579705",          # 숫자만 (6자리, 연도 없음)
    "2025타경32529",   # 전체 사건번호 (5자리)
    "202532529",       # 숫자만 (연도+5자리)
]

for case_no in test_cases:
    print(f"\n{'='*80}")
    print(f"테스트: {case_no}")
    print("-" * 80)

    url = f"http://localhost:8000/auction?case_no={case_no}&bidders=10"

    try:
        response = requests.get(url, timeout=60)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                info = data['data']['auction_info']
                print(f"✓ 성공")
                print(f"  변환된 사건번호: {info.get('사건번호')}")
                print(f"  데이터소스: {info.get('데이터소스')}")
                print(f"  감정가: {info.get('감정가')}")
            else:
                print(f"✗ 실패: {data}")
        elif response.status_code == 404:
            print(f"✓ 404 에러 (정상 - 사건번호 없음)")
            error = response.json()
            print(f"  메시지: {error['detail']['message']}")
        else:
            print(f"✗ HTTP {response.status_code}")

    except Exception as e:
        print(f"✗ 예외: {e}")

print("\n" + "=" * 80)
print("테스트 완료")
print("=" * 80)
