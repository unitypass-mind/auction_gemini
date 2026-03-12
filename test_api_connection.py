"""
API 연동 테스트 스크립트
Flutter 앱의 API 서비스 기능을 테스트합니다.
"""
import requests
import json

BASE_URL = "http://49.50.131.190"

def test_health():
    """서버 헬스 체크"""
    print("=" * 60)
    print("1. 서버 헬스 체크")
    print("=" * 60)

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"상태 코드: {response.status_code}")
        print(f"응답: {response.json()}")
        return True
    except Exception as e:
        print(f"오류: {e}")
        return False

def test_register():
    """회원가입 테스트"""
    print("\n" + "=" * 60)
    print("2. 회원가입 테스트")
    print("=" * 60)

    # 새로운 이메일로 테스트
    user_data = {
        "email": f"testuser{int(time.time())}@example.com",
        "password": "test1234",
        "name": "테스트사용자"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=user_data,
            timeout=10
        )
        print(f"상태 코드: {response.status_code}")
        print(f"응답: {response.json()}")

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"[OK] Registration successful!")
                print(f"User ID: {data['user']['id']}")
                print(f"Email: {data['user']['email']}")
                print(f"Access Token: {data['access_token'][:50]}...")
                return data['access_token']
            else:
                print(f"[FAIL] Registration failed: {data.get('message')}")
        else:
            print(f"[ERROR] HTTP error: {response.status_code}")

        return None
    except Exception as e:
        print(f"오류: {e}")
        return None

def test_login(email="test@example.com", password="test1234"):
    """로그인 테스트"""
    print("\n" + "=" * 60)
    print("3. 로그인 테스트")
    print("=" * 60)

    login_data = {
        "email": email,
        "password": password
    }

    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=login_data,
            timeout=10
        )
        print(f"상태 코드: {response.status_code}")
        print(f"응답: {response.json()}")

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"[OK] Login successful!")
                print(f"User: {data['user']['email']}")
                return data['access_token']
            else:
                print(f"[FAIL] Login failed: {data.get('message')}")
        else:
            print(f"[ERROR] HTTP error: {response.status_code}")

        return None
    except Exception as e:
        print(f"오류: {e}")
        return None

def test_my_info(token):
    """내 정보 조회 테스트"""
    print("\n" + "=" * 60)
    print("4. 내 정보 조회 테스트")
    print("=" * 60)

    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(
            f"{BASE_URL}/auth/me",
            headers=headers,
            timeout=10
        )
        print(f"상태 코드: {response.status_code}")
        print(f"응답: {response.json()}")

        if response.status_code == 200:
            print("[OK] Token authentication successful!")
        else:
            print("[FAIL] Token authentication failed")

    except Exception as e:
        print(f"오류: {e}")

def test_search():
    """경매 검색 테스트 (사건번호 검색)"""
    print("\n" + "=" * 60)
    print("5. 경매 검색 테스트 (사건번호)")
    print("=" * 60)

    try:
        # 사건번호로 검색 (스크린샷에 있던 번호)
        params = {
            "query": "2024타경579705",
            "limit": 5
        }
        response = requests.get(
            f"{BASE_URL}/search-case",
            params=params,
            timeout=10
        )
        print(f"상태 코드: {response.status_code}")
        data = response.json()

        print(f"응답 데이터: {json.dumps(data, ensure_ascii=False, indent=2)}")
        print(f"검색 결과 수: {data.get('count', 0)}개")

        if data.get('count', 0) > 0:
            print("[OK] Auction search successful!")
            if data.get('results'):
                print(f"첫 번째 결과: {data['results'][0]}")
        else:
            print("[INFO] No search results (ValueAuction API may have no data for this case)")

    except Exception as e:
        print(f"오류: {e}")

def test_search_local():
    """경매 검색 테스트 (로컬 DB - 지역 필터)"""
    print("\n" + "=" * 60)
    print("6. 경매 검색 테스트 (로컬 DB - 지역 필터)")
    print("=" * 60)

    try:
        # 지역으로 검색
        params = {
            "region": "서울",
            "limit": 5
        }
        response = requests.get(
            f"{BASE_URL}/auctions/search",
            params=params,
            timeout=10
        )
        print(f"상태 코드: {response.status_code}")
        data = response.json()

        print(f"검색 결과 수: {data.get('count', 0)}개 / 전체: {data.get('total', 0)}개")

        if data.get('count', 0) > 0:
            print("[OK] Local DB search successful!")
            if data.get('items'):
                first = data['items'][0]
                print(f"첫 번째 결과:")
                print(f"  - 사건번호: {first.get('사건번호')}")
                print(f"  - 물건종류: {first.get('물건종류')}")
                print(f"  - 지역: {first.get('지역')}")
                print(f"  - 감정가: {first.get('감정가_formatted')}")
        else:
            print("[WARN] No search results in local DB")

    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    import time
    import sys
    import io

    # UTF-8 encoding for Windows console
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("\nFlutter API Test Starting\n")

    # 1. Health check
    if not test_health():
        print("\nCannot connect to server. Aborting test.")
        exit(1)

    # 2. Registration test
    token = test_register()

    # 3. Login test (if registration failed)
    if not token:
        print("\nTrying login with existing user...")
        token = test_login()

    # 4. Get my info (if token exists)
    if token:
        test_my_info(token)

    # 5. Auction search (ValueAuction API)
    test_search()

    # 6. Local DB search
    test_search_local()

    print("\n" + "=" * 60)
    print("API Test Completed")
    print("=" * 60)
