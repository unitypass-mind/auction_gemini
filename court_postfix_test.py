# -*- coding: utf-8 -*-
"""
법원 경매 사이트 - postfix 파라미터 기반 API 테스트
스크린샷에서 보인 패턴: PGJ159M01.xml?postfix=17712... (타임스탬프)
"""

import requests
import json
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "https://www.courtauction.go.kr"

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept-Language': 'ko-KR,ko;q=0.9',
    'Accept': 'application/json, text/plain, */*',
})

print("=" * 70)
print("법원 경매 API - postfix 타임스탬프 방식 테스트")
print("=" * 70)

# 현재 타임스탬프 (밀리초)
ts = int(time.time() * 1000)
print(f"\n현재 타임스탬프: {ts}")

# 1. 메인 페이지 방문 (세션 초기화)
print("\n[1] 메인 페이지 방문")
r = session.get(BASE_URL, timeout=15)
print(f"Status: {r.status_code}")
print(f"쿠키 획득: {dict(session.cookies)}")

# 2. 스크린샷에서 본 XML 엔드포인트들 시도
print("\n[2] XML 엔드포인트 테스트 (postfix=타임스탬프)")
print("-" * 70)

xml_endpoints = [
    f"/PGJ159M01.xml?postfix={ts}",
    f"/side002.xml?postfix={ts}",
    f"/PGJ15AF01.xml?postfix={ts}",
    f"/PGJ15AF02.xml?postfix={ts}",
    f"/PGJ15AF03.xml?postfix={ts}",
]

for ep in xml_endpoints:
    try:
        r = session.get(BASE_URL + ep, timeout=10)
        ctype = r.headers.get('Content-Type', '')
        print(f"\nGET {ep[:50]}")
        print(f"  Status: {r.status_code}, Length: {len(r.text)}, Type: {ctype}")
        if r.status_code == 200 and len(r.text) != 29030:
            print(f"  => 다른 응답 감지!")
            print(f"  내용: {r.text[:300]}")
    except Exception as e:
        print(f"\nGET {ep[:50]} => 오류: {e}")

# 3. JSON API 직접 호출 시도 (Accept: application/json 헤더 추가)
print("\n\n[3] JSON Accept 헤더로 selectAuctnCsrchRslt.on 재시도")
print("-" * 70)

json_headers = {
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': f'{BASE_URL}/newIndexFront.on',
    'Origin': BASE_URL,
}

test_data = [
    {
        "name": "JSON Accept + 사건번호",
        "data": {
            "saNo": "2024타경579705",
            "pageNo": "1",
        }
    },
    {
        "name": "JSON Accept + csNo 형식",
        "data": {
            "csNo": "20240130579705",
        }
    },
    {
        "name": "JSON Accept + 검색어",
        "data": {
            "searchWord": "2024타경579705",
        }
    },
    {
        "name": "JSON Accept 파라미터 없음 (빈 요청)",
        "data": {}
    }
]

for test in test_data:
    print(f"\n--- {test['name']} ---")
    try:
        r = session.post(
            BASE_URL + "/selectAuctnCsrchRslt.on",
            headers={**session.headers, **json_headers},
            data=test['data'],
            timeout=15
        )
        ctype = r.headers.get('Content-Type', '')
        is_json = 'json' in ctype or r.text.strip().startswith('{') or r.text.strip().startswith('[')
        size = len(r.text)
        print(f"Status: {r.status_code}, Size: {size}, JSON: {is_json}")

        if is_json:
            print("=> JSON 응답!")
            print(r.text[:600])
        elif size != 29030:
            print(f"=> 다른 응답 감지 (기본={29030} vs 실제={size})!")
            print(r.text[:300])
        else:
            print("=> 기본 HTML 반환됨 (인증 필요)")

    except Exception as e:
        print(f"오류: {e}")

# 4. selectCortOfcList.on 에서 법원 목록 가져오기
print("\n\n[4] 법원 목록 조회 (selectCortOfcList.on)")
print("-" * 70)
try:
    r = session.post(
        BASE_URL + "/selectCortOfcList.on",
        headers={**session.headers, **json_headers},
        data={},
        timeout=15
    )
    ctype = r.headers.get('Content-Type', '')
    print(f"Status: {r.status_code}, Size: {len(r.text)}")
    print(f"Content-Type: {ctype}")
    if r.text.strip().startswith('{') or r.text.strip().startswith('[') or 'json' in ctype:
        print("=> JSON 응답!")
        print(r.text[:800])
    elif len(r.text) != 29030:
        print(f"=> 다른 응답! ({len(r.text)} bytes)")
        print(r.text[:300])
    else:
        print("=> 기본 HTML 반환")

except Exception as e:
    print(f"오류: {e}")

print("\n\n" + "=" * 70)
print("결론 및 다음 단계")
print("=" * 70)
print("""
현재 상황:
- 모든 요청이 29,030 bytes HTML 반환 (기본 페이지)
- 브라우저는 JSON 응답을 받지만 우리는 못 받음

이유 분석:
1. CSRF 토큰 - JavaScript가 동적으로 생성하는 토큰 필요
2. 세션 초기화 - JavaScript 실행 후에만 세션이 유효해짐
3. 방화벽/WAF - 봇 탐지로 차단 중

해결 방법 (2가지):
A. DevTools에서 직접 cURL 복사
   - selectAuctnCsrchRslt.on 우클릭 -> Copy as cURL
   - 정확한 헤더와 파라미터 확인 가능

B. Playwright/Selenium 사용
   - 실제 브라우저로 JavaScript 실행
   - 세션/토큰 자동 처리
   - 보다 안정적인 크롤링 가능
""")
