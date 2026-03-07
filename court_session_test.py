# -*- coding: utf-8 -*-
"""
법원 경매 사이트 세션 기반 API 테스트
1. 메인 페이지로 세션/쿠키 초기화
2. 실제 검색 요청 전송
"""

import requests
import json
import re
import sys

# 인코딩 문제 해결
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TARGET_CASE = "2024타경579705"
BASE_URL = "https://www.courtauction.go.kr"

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept-Language': 'ko-KR,ko;q=0.9',
})

print("=" * 70)
print("법원 경매 사이트 세션 기반 API 테스트")
print("=" * 70)

# 1단계: 메인 페이지 방문하여 세션/쿠키 초기화
print("\n[1단계] 메인 페이지 방문 - 세션 초기화")
print("-" * 70)
try:
    r = session.get(BASE_URL, timeout=15)
    print(f"Status: {r.status_code}")
    print(f"Cookies: {dict(session.cookies)}")
    print(f"Redirect URL: {r.url}")
except Exception as e:
    print(f"오류: {e}")

# 2단계: 검색 페이지 방문
print("\n[2단계] 경매사건검색 페이지 방문")
print("-" * 70)
search_page_urls = [
    "/PGJ15AF00.on",
    "/newIndexFront.on",
    "/index.on",
]
for path in search_page_urls:
    try:
        r = session.get(BASE_URL + path, timeout=10)
        print(f"GET {path} => Status: {r.status_code}, Length: {len(r.text)}")
        if r.status_code == 200 and len(r.text) > 5000:
            print("  => 페이지 로드 성공!")
            break
    except Exception as e:
        print(f"GET {path} => 오류: {e}")

# 3단계: 실제 검색 API 호출 (스크린샷에서 확인된 엔드포인트)
print("\n[3단계] selectAuctnCsrchRslt.on - 경매사건검색 API 호출")
print("-" * 70)

# 스크린샷 DevTools에서 확인된 csNo 형식: "20240130579705" (타경 없이 숫자만)
# 형식: [연도 4자리][법원코드? 2자리][사건번호 6자리] 또는 [연도 4자리][사건번호]
# 예: "20240130579705" = 2024 + 0130 + 579705 (인천지방법원 코드?)

# DevTools Response에서 보인 데이터:
# "csNo": "20240130579705"
# "reltCortOfccCd": "B000240" (법원코드)
# "reltCsNo": "20250130001106"

# 인천지방법원 코드: B000240 기반으로 사건번호 형식 추정
# cortOfcCd: 법원 코드, csNo: 사건번호, dvsVd: 구분코드

payloads = [
    # 시도 1: 사건번호 직접 검색
    {
        "name": "사건번호 직접 검색",
        "headers": {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': BASE_URL + '/newIndexFront.on',
        },
        "data": {
            "saNo": TARGET_CASE,
        }
    },
    # 시도 2: csNo 형식으로 시도 (DevTools에서 본 형식)
    {
        "name": "csNo 숫자 형식",
        "headers": {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': BASE_URL + '/newIndexFront.on',
        },
        "data": {
            "csNo": "20240130579705",
            "cortOfcCd": "B000240",
        }
    },
    # 시도 3: 법원 코드 + 사건번호 분리
    {
        "name": "cortOfcCd + saNo 분리",
        "headers": {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': BASE_URL + '/newIndexFront.on',
        },
        "data": {
            "cortOfcCd": "B000240",   # 인천지방법원
            "saNo": "2024타경579705",
            "srnID": "PGJ159M01",
        }
    },
    # 시도 4: 파라미터 없이 (기본 요청)
    {
        "name": "기본 요청 (파라미터 없음)",
        "headers": {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': BASE_URL + '/newIndexFront.on',
        },
        "data": {}
    },
]

for test in payloads:
    print(f"\n--- {test['name']} ---")
    print(f"데이터: {test['data']}")
    try:
        r = session.post(
            BASE_URL + "/selectAuctnCsrchRslt.on",
            headers={**session.headers, **test['headers']},
            data=test['data'],
            timeout=15
        )
        ctype = r.headers.get('Content-Type', '')
        print(f"Status: {r.status_code}")
        print(f"Content-Type: {ctype}")
        print(f"Content-Length: {len(r.text)}")

        if 'json' in ctype or r.text.strip().startswith('{') or r.text.strip().startswith('['):
            print("=> JSON 응답 감지!")
            try:
                j = r.json()
                print(json.dumps(j, indent=2, ensure_ascii=False)[:800])
            except:
                print(r.text[:500])
        else:
            # HTML 응답 - 의미있는 텍스트 추출 시도
            text = r.text
            # JSON-like 부분 찾기
            json_match = re.search(r'\{.*?"status"\s*:\s*\d+.*?\}', text, re.DOTALL)
            if json_match:
                print("=> HTML 안에 JSON 발견!")
                print(json_match.group()[:300])
            else:
                # 사건번호가 응답에 있는지 확인
                if "579705" in text or "2024타경" in text.replace("&#xD0C0;&#xACBD;", "타경"):
                    print("=> 응답에 사건번호 포함!")
                else:
                    print("=> 일반 HTML (사건번호 없음)")
                    print(f"   미리보기: {text[200:400].strip()[:100]}")

    except Exception as e:
        print(f"오류: {e}")

# 4단계: DevTools에서 보인 다른 엔드포인트들 시도
print("\n\n[4단계] DevTools에서 발견한 추가 엔드포인트 분석")
print("-" * 70)

additional_endpoints = [
    "/PGJ159M01.on",     # 스크린샷에서 .xml이 아닌 .on 버전
    "/PGJ15AF01.on",
    "/PGJ15AF02.on",
    "/PGJ15AF03.on",
    "/selectCortOfcList.on",
]

for ep in additional_endpoints:
    try:
        r = session.post(
            BASE_URL + ep,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': BASE_URL + '/newIndexFront.on',
            },
            data={},
            timeout=10
        )
        ctype = r.headers.get('Content-Type', '')
        is_json = 'json' in ctype or (len(r.text) > 0 and r.text.strip()[0] in '{[')
        print(f"POST {ep} => {r.status_code}, {len(r.text)}bytes, JSON={is_json}")
        if is_json:
            print(f"  => {r.text[:200]}")
    except Exception as e:
        print(f"POST {ep} => 오류: {type(e).__name__}")

print("\n\n" + "=" * 70)
print("분석 결론")
print("=" * 70)
print("""
스크린샷 DevTools 분석:
- 엔드포인트: selectAuctnCsrchRslt.on
- 응답: JSON (status:200, message: "최고 공고 목록이 조회되었습니다.")
- 데이터 필드: csNo, reltCortOfccCd, reltCsNo, reltCsDvsCd

다음 단계:
1. DevTools에서 selectAuctnCsrchRslt.on 요청의 Payload 탭 확인
2. 정확한 파라미터 이름과 값 확인 필요
""")
