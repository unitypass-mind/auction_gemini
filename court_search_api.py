# -*- coding: utf-8 -*-
"""
법원 경매 사이트 - 실제 검색 API 찾기
발견된 패턴: /pgj/pgj002/ 경로
목표: 경매사건검색 API 찾아 2024타경579705 조회
"""

import asyncio
import json
import sys
import io
from playwright.async_api import async_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TARGET_CASE = "2024타경579705"
BASE_URL = "https://www.courtauction.go.kr"

# 검색 관련 API 캡처용
search_responses = []

async def run():
    async with async_playwright() as p:
        print("=" * 70)
        print("법원 경매 사이트 - 경매사건검색 API 탐색")
        print("=" * 70)

        browser = await p.chromium.launch(headless=True, args=['--lang=ko-KR'])
        context = await browser.new_context(
            locale='ko-KR',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        # 모든 JSON 응답 캡처
        async def on_response(response):
            url = response.url
            if 'courtauction.go.kr' in url and '.on' in url:
                try:
                    ctype = response.headers.get('content-type', '')
                    body = await response.text()
                    if body.strip().startswith('{') or body.strip().startswith('[') or 'json' in ctype:
                        path = url.replace(BASE_URL, '')
                        post_data = ""
                        try:
                            req = response.request
                            post_data = req.post_data or ""
                        except:
                            pass

                        search_responses.append({
                            'path': path,
                            'url': url,
                            'status': response.status,
                            'body_preview': body[:300],
                            'post_data': post_data[:200],
                        })
                except:
                    pass

        page.on('response', on_response)

        # 1. 메인 페이지
        print("\n[1] 메인 페이지 방문")
        await page.goto(f"{BASE_URL}/pgj/index.on", wait_until='networkidle', timeout=30000)
        print(f"  URL: {page.url}")
        print(f"  캡처된 API: {len(search_responses)}개")

        await asyncio.sleep(1)
        prev_count = len(search_responses)

        # 2. 경매물건검색 페이지 직접 접근 (PGJ159 패턴 기반)
        print("\n[2] 경매사건검색 페이지 접근 시도")
        search_paths = [
            "/pgj/pgj159/index.on",
            "/pgj/pgj15/index.on",
            "/pgj/pgj15af/index.on",
            "/pgj/pgj159m01/index.on",
            "/pgj/pgj002/index.on",
        ]

        working_path = None
        for path in search_paths:
            try:
                r = await page.goto(f"{BASE_URL}{path}", timeout=8000)
                if r and r.status == 200 and "/pgj" in page.url and "error" not in page.url:
                    print(f"  ✓ 성공: {path} -> {page.url}")
                    working_path = path
                    await asyncio.sleep(2)
                    break
                else:
                    print(f"  ✗ {path} -> {r.status if r else 'None'}")
            except:
                print(f"  ✗ {path} -> 오류")

        # 3. 메인에서 검색 메뉴 클릭 시도
        if not working_path:
            print("\n[3] 메인에서 검색 메뉴 탐색")
            await page.goto(f"{BASE_URL}/pgj/index.on", wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            # 링크 찾기
            links = await page.query_selector_all('a[href]')
            search_links = []
            for link in links:
                href = await link.get_attribute('href') or ''
                text = await link.inner_text()
                if any(kw in text for kw in ['검색', '사건', '물건']) or 'pgj15' in href.lower():
                    search_links.append({'href': href, 'text': text.strip()})

            print(f"  검색 관련 링크: {len(search_links)}개")
            for sl in search_links[:10]:
                print(f"    [{sl['text']}] -> {sl['href']}")

            # 첫 번째 검색 링크 클릭
            if search_links:
                first_link = search_links[0]
                print(f"\n  '{first_link['text']}' 클릭 중...")
                try:
                    await page.click(f"a[href='{first_link['href']}']")
                    await page.wait_for_load_state('networkidle', timeout=15000)
                    await asyncio.sleep(3)
                    print(f"  이동 후 URL: {page.url}")
                except Exception as e:
                    print(f"  클릭 오류: {e}")

        # 4. 현재 페이지에서 입력 필드 찾아 검색
        print(f"\n[4] 현재 페이지 검색 시도 (URL: {page.url})")
        await asyncio.sleep(2)
        new_count = len(search_responses)
        print(f"  새로 캡처된 API: {new_count - prev_count}개")

        # 입력 필드 탐색
        all_inputs = await page.query_selector_all('input')
        print(f"  입력 필드 수: {len(all_inputs)}개")

        for inp in all_inputs[:10]:
            name = await inp.get_attribute('name') or ''
            placeholder = await inp.get_attribute('placeholder') or ''
            inp_type = await inp.get_attribute('type') or 'text'
            if inp_type not in ['hidden', 'button', 'submit', 'checkbox', 'radio']:
                print(f"    - name={name}, placeholder={placeholder}, type={inp_type}")

        # 5. 직접 검색 API 호출 (캡처된 쿠키 활용)
        print(f"\n[5] 세션 쿠키로 검색 API 직접 호출")

        cookies = await context.cookies()
        cookie_dict = {c['name']: c['value'] for c in cookies}
        print(f"  쿠키 목록: {list(cookie_dict.keys())}")

        # 검색 API 후보 경로들
        search_api_paths = [
            "/pgj/pgj159/selectAuctnCsrchRslt.on",
            "/pgj/pgj15/selectAuctnCsrchRslt.on",
            "/pgj/pgj15af/selectAuctnCsrchRslt.on",
            "/pgj/selectAuctnCsrchRslt.on",
        ]

        # requests로 시도
        import requests as req_lib

        session = req_lib.Session()
        for c in cookies:
            session.cookies.set(c['name'], c['value'], domain=c.get('domain', 'www.courtauction.go.kr'))

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'ko-KR,ko;q=0.9',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'{BASE_URL}/pgj/index.on',
            'Origin': BASE_URL,
        }

        # 인천지방법원 코드: B000240 (스크린샷에서 확인)
        # 사건번호 형식: csNo "20240130579705" = 2024 + B000240? + 579705
        # 법원코드 B000240에서 0240이 인천?

        payloads = [
            # 시도 1: 사건번호 직접 (한글 포함)
            {"saNo": TARGET_CASE},
            # 시도 2: 숫자 형식
            {"csNo": "20240130579705"},
            # 시도 3: 법원코드 + 사건번호
            {"cortOfcCd": "B000240", "saNo": TARGET_CASE},
            # 시도 4: 스크린샷 Response에서 보인 형식 그대로
            {"cortOfcCd": "B000240", "csNo": "20240130579705", "dvsCd": "36"},
        ]

        for api_path in search_api_paths:
            for payload in payloads[:2]:  # 처음 2개만 테스트
                try:
                    r = session.post(
                        BASE_URL + api_path,
                        headers=headers,
                        json=payload,
                        timeout=10
                    )
                    ctype = r.headers.get('Content-Type', '')
                    is_json = r.text.strip().startswith('{') or r.text.strip().startswith('[') or 'json' in ctype

                    if is_json and len(r.text) != 29030:
                        print(f"\n  ✓ JSON 응답! POST {api_path}")
                        print(f"    payload: {payload}")
                        print(f"    response: {r.text[:400]}")
                    elif len(r.text) != 29030:
                        print(f"\n  다른 응답 ({len(r.text)}bytes): POST {api_path}")
                        print(f"    {r.text[:200]}")

                except Exception as e:
                    pass  # 조용히 실패

        # 6. Playwright 직접 API 호출 (페이지 context 활용)
        print(f"\n[6] Playwright fetch API로 직접 호출")

        try:
            # 현재 페이지에서 fetch 실행
            result = await page.evaluate("""
                async () => {
                    const url = '/pgj/pgj159/selectAuctnCsrchRslt.on';
                    const payload = JSON.stringify({
                        "cortOfcCd": "B000240",
                        "saNo": "2024타경579705"
                    });

                    try {
                        const resp = await fetch(url, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-Requested-With': 'XMLHttpRequest'
                            },
                            body: payload
                        });

                        const text = await resp.text();
                        return {
                            status: resp.status,
                            contentType: resp.headers.get('Content-Type'),
                            body: text.substring(0, 500),
                            size: text.length
                        };
                    } catch(e) {
                        return {error: e.toString()};
                    }
                }
            """)
            print(f"  결과: {json.dumps(result, ensure_ascii=False, indent=2)}")
        except Exception as e:
            print(f"  fetch 오류: {e}")

        # 다양한 경로 시도
        paths_to_try = [
            "/pgj/pgj159/selectAuctnCsrchRslt.on",
            "/pgj/pgj15/selectAuctnCsrchRslt.on",
            "/pgj/selectAuctnCsrchRslt.on",
        ]

        for path in paths_to_try[1:]:
            try:
                result = await page.evaluate(f"""
                    async () => {{
                        try {{
                            const resp = await fetch('{path}', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}},
                                body: JSON.stringify({{"saNo": "2024타경579705"}})
                            }});
                            const text = await resp.text();
                            return {{status: resp.status, size: text.length, body: text.substring(0, 300)}};
                        }} catch(e) {{
                            return {{error: e.toString()}};
                        }}
                    }}
                """)
                if result.get('size', 0) != 29030:
                    print(f"  다른 응답: {path}")
                    print(f"  {result}")
            except:
                pass

        await browser.close()

        # 최종 결과
        print(f"\n\n{'='*70}")
        print(f"캡처된 전체 API 목록 ({len(search_responses)}개)")
        print("=" * 70)
        seen_paths = set()
        for resp in search_responses:
            if resp['path'] not in seen_paths:
                seen_paths.add(resp['path'])
                print(f"\n경로: {resp['path']}")
                if resp['post_data']:
                    print(f"  요청: {resp['post_data']}")
                print(f"  응답: {resp['body_preview'][:150]}")


if __name__ == "__main__":
    asyncio.run(run())
