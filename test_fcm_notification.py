#!/usr/bin/env python3
"""
FCM 테스트 알림 전송 스크립트
"""
import requests
import json

# 서버 URL
BASE_URL = "http://49.50.131.190:8000"

# 1. 로그인해서 토큰 가져오기
print("=== 1. 로그인 ===")
login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "fcmtest@exam.com",
    "password": "1234"
})

print(f"로그인 응답: {login_response.status_code}")
login_data = login_response.json()
print(json.dumps(login_data, indent=2, ensure_ascii=False))

if not login_data.get("success"):
    print("로그인 실패!")
    exit(1)

access_token = login_data["access_token"]
print(f"\n[OK] 토큰 획득: {access_token[:50]}...")

# 2. 테스트 알림 전송
print("\n=== 2. 테스트 알림 전송 ===")
headers = {
    "Authorization": f"Bearer {access_token}"
}

test_response = requests.post(
    f"{BASE_URL}/notifications/test",
    headers=headers
)

print(f"테스트 알림 응답: {test_response.status_code}")
test_data = test_response.json()
print(json.dumps(test_data, indent=2, ensure_ascii=False))

if test_data.get("success"):
    print(f"\n[OK] 성공: {test_data['message']}")
    print(f"   전송 성공: {test_data['success_count']}/{test_data['total_devices']}개")
else:
    print(f"\n[ERROR] 실패: {test_data.get('message', '알 수 없는 오류')}")
