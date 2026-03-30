#!/usr/bin/env python3
"""
알림 마스터 스위치 테스트 스크립트
"""
import requests
import json
import time

# 서버 URL
BASE_URL = "http://49.50.131.190:8000"

# 1. 로그인
print("=== 1. 로그인 ===")
login_response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "fcmtest@exam.com",
    "password": "1234"
})

login_data = login_response.json()
access_token = login_data["access_token"]
print(f"[OK] 로그인 성공")

headers = {
    "Authorization": f"Bearer {access_token}"
}

# 2. 현재 알림 설정 확인
print("\n=== 2. 현재 알림 설정 확인 ===")
settings_response = requests.get(f"{BASE_URL}/notifications/settings", headers=headers)
settings_data = settings_response.json()
print(json.dumps(settings_data, indent=2, ensure_ascii=False))

# 3. 알림 마스터 스위치 OFF
print("\n=== 3. 알림 마스터 스위치 OFF ===")
off_response = requests.post(
    f"{BASE_URL}/notifications/settings",
    headers=headers,
    params={"enabled": False}
)
off_data = off_response.json()
print(json.dumps(off_data, indent=2, ensure_ascii=False))

# 4. OFF 상태에서 테스트 알림 전송
print("\n=== 4. OFF 상태에서 테스트 알림 전송 ===")
test_response = requests.post(f"{BASE_URL}/notifications/test", headers=headers)
test_data = test_response.json()
print(json.dumps(test_data, indent=2, ensure_ascii=False))
print("\n[INFO] 알림이 핸드폰에 도착하지 않아야 합니다 (마스터 스위치 OFF)")

# 5초 대기
print("\n5초 대기 중...")
time.sleep(5)

# 5. 알림 마스터 스위치 다시 ON
print("\n=== 5. 알림 마스터 스위치 ON ===")
on_response = requests.post(
    f"{BASE_URL}/notifications/settings",
    headers=headers,
    params={"enabled": True}
)
on_data = on_response.json()
print(json.dumps(on_data, indent=2, ensure_ascii=False))

# 6. ON 상태에서 테스트 알림 전송
print("\n=== 6. ON 상태에서 테스트 알림 전송 ===")
test_response2 = requests.post(f"{BASE_URL}/notifications/test", headers=headers)
test_data2 = test_response2.json()
print(json.dumps(test_data2, indent=2, ensure_ascii=False))
print("\n[INFO] 알림이 핸드폰에 도착해야 합니다 (마스터 스위치 ON)")
