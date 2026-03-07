# -*- coding: utf-8 -*-
"""
Playwright로 법원 경매 사이트 API 캡처
- 실제 브라우저로 JS 세션 토큰 처리
- Network 요청 가로채기로 실제 API 파라미터 확인
"""

import asyncio
import json
import sys
import io
from playwright.async_api import async_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TARGET_CASE = "2024타경579705"
BASE_URL = "https://www.courtauction.go.kr"

captured_requests = []
captured_responses = []

async def run():
    async with async_playwright() as p:
        print("=" * 70)
        print("Playwright - 법원 경매 사이트 API 캡처")
        print("=" * 70)

        # 브라우저 실행 (headless=False이면 화면에 보임)
        browser = await p.chromium.launch(
            headless=True,  # 백그라운드로 실행
            args=['--lang=ko-KR']
        )

        context = await browser.new_context(
            locale='ko-KR',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        )

        page = await context.new_page()

        # 네트워크 요청 가로채기
        async def on_request(request):
            url = request.url
            if 'courtauction.go.kr' in url and any(ep in url for ep in [
                '.on', 'selectAuctn', 'PGJ15', 'search', 'list'
            ]):
                captured_requests.append({
                    'url': url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'post_data': request.post_data,
                })

        async def on_response(response):
            url = response.url
            if 'courtauction.go.kr' in url and any(ep in url for ep in [
                'selectAuctn', '.on'
            ]):
                try:
                    body = await response.text()
                    ctype = response.headers.get('content-type', '')
                    if 'json' in ctype or body.strip().startswith('{'):
                        captured_responses.append({
                            'url': url,
                            'status': response.status,
                            'content_type': ctype,
                            'body': body[:1000]
                        })
                        print(f"\n[JSON 응답 캡처!] {url}")
                        print(f"  Status: {response.status}")
                        print(f"  Body: {body[:400]}")
                except:
                    pass

        page.on('request', on_request)
        page.on('response', on_response)

        # 1. 메인 페이지 방문
        print("\n[1] 메인 페이지 방문 중...")
        await page.goto(BASE_URL, wait_until='networkidle', timeout=30000)
        print(f"  현재 URL: {page.url}")
        print(f"  제목: {await page.title()}")

        await asyncio.sleep(2)

        # 2. 경매사건검색 페이지로 이동
        print("\n[2] 경매사건검색 페이지 이동 중...")
        try:
            # 경매사건검색 메뉴 찾기
            await page.goto(f"{BASE_URL}/newIndexFront.on", wait_until='networkidle', timeout=20000)
            print(f"  현재 URL: {page.url}")
        except Exception as e:
            print(f"  오류: {e}")

        await asyncio.sleep(2)

        # 3. 검색 입력 및 실행
        print(f"\n[3] 사건번호 검색: {TARGET_CASE}")
        try:
            # 다양한 셀렉터 시도
            selectors = [
                'input[name="saNo"]',
                'input[name="caseNo"]',
                'input[placeholder*="사건"]',
                'input[type="text"]',
                '#saNo',
                '#caseNo',
            ]

            input_found = False
            for selector in selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        print(f"  입력 필드 발견: {selector}")
                        await elem.clear()
                        await elem.type(TARGET_CASE)
                        await asyncio.sleep(1)

                        # 검색 버튼 클릭 시도
                        search_btns = ['button[type="submit"]', 'input[type="submit"]', 'button.search', '.btn-search', '#btnSearch']
                        for btn in search_btns:
                            try:
                                btn_elem = await page.query_selector(btn)
                                if btn_elem:
                                    await btn_elem.click()
                                    print(f"  검색 버튼 클릭: {btn}")
                                    break
                            except:
                                continue
                        else:
                            await page.keyboard.press('Enter')
                            print("  Enter 키로 검색")

                        await page.wait_for_load_state('networkidle', timeout=15000)
                        await asyncio.sleep(3)
                        input_found = True
                        break
                except:
                    continue

            if not input_found:
                print("  입력 필드를 찾지 못함. 페이지 구조 분석...")
                # 페이지 HTML 저장
                html = await page.content()
                with open('court_page.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                print("  페이지 HTML을 court_page.html에 저장")

        except Exception as e:
            print(f"  검색 오류: {e}")

        # 4. 캡처된 요청/응답 분석
        print(f"\n\n{'='*70}")
        print(f"캡처된 API 요청 ({len(captured_requests)}개)")
        print("=" * 70)

        for i, req in enumerate(captured_requests[:10], 1):
            print(f"\n[요청 {i}] {req['method']} {req['url']}")
            if req['post_data']:
                print(f"  POST 데이터: {req['post_data'][:200]}")

        print(f"\n\n{'='*70}")
        print(f"캡처된 JSON 응답 ({len(captured_responses)}개)")
        print("=" * 70)

        for i, resp in enumerate(captured_responses[:5], 1):
            print(f"\n[응답 {i}] {resp['url']}")
            print(f"  Status: {resp['status']}")
            print(f"  Body: {resp['body'][:400]}")

        # 5. 직접 API 호출 테스트 (세션 쿠키 활용)
        print(f"\n\n{'='*70}")
        print("세션 쿠키를 사용한 직접 API 호출 테스트")
        print("=" * 70)

        # 현재 세션의 쿠키 가져오기
        cookies = await context.cookies()
        print(f"세션 쿠키: {[c['name'] for c in cookies]}")

        if cookies:
            import requests as req_lib

            cookie_header = '; '.join([f"{c['name']}={c['value']}" for c in cookies])

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'ko-KR,ko;q=0.9',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': BASE_URL + '/newIndexFront.on',
                'Cookie': cookie_header,
            }

            r = req_lib.post(
                f"{BASE_URL}/selectAuctnCsrchRslt.on",
                headers=headers,
                data={'saNo': TARGET_CASE},
                timeout=15
            )

            print(f"\nStatus: {r.status_code}")
            print(f"Content-Type: {r.headers.get('Content-Type', '')}")
            print(f"Size: {len(r.text)}")
            if r.text.strip().startswith('{') or 'json' in r.headers.get('Content-Type', ''):
                print("=> JSON 응답!")
                print(r.text[:600])
            else:
                print(f"=> HTML 응답 (size: {len(r.text)})")

        await browser.close()

        # 최종 결론
        print(f"\n\n{'='*70}")
        print("테스트 결론")
        print("=" * 70)

        if captured_responses:
            print(f"[성공] JSON 응답 {len(captured_responses)}개 캡처!")
            print("=> 법원 경매 사이트 크롤링 가능!")
        elif captured_requests:
            print(f"[부분] API 요청 {len(captured_requests)}개 캡처 (JSON 응답 없음)")
            print("=> 요청 구조는 파악됨, 추가 분석 필요")
        else:
            print("[실패] API 요청 캡처 안됨")
            print("=> Playwright headless=False로 수동 확인 필요")


if __name__ == "__main__":
    asyncio.run(run())
