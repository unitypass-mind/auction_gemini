# -*- coding: utf-8 -*-
"""
Playwright - JavaScript로 직접 검색 API 호출
브라우저 내부에서 fetch() 사용하여 CSRF 토큰 자동 포함
"""

import asyncio
import json
import sys
import io
from playwright.async_api import async_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TARGET_CASE = "2024타경579705"
TARGET_YEAR = "2024"
TARGET_NUMBER = "579705"
TARGET_COURT_CODE = "B000240"  # 인천지방법원

BASE_URL = "https://www.courtauction.go.kr"

all_network = []

async def run():
    async with async_playwright() as p:
        print("=" * 70)
        print("JavaScript fetch API로 법원 경매사건검색")
        print("=" * 70)

        browser = await p.chromium.launch(headless=True, args=['--lang=ko-KR'])
        context = await browser.new_context(locale='ko-KR')
        page = await context.new_page()

        # 모든 네트워크 응답 캡처
        async def on_response(response):
            url = response.url
            if 'courtauction.go.kr' in url and '.on' in url:
                try:
                    body = await response.text()
                    is_json = body.strip().startswith('{') or body.strip().startswith('[')
                    if is_json and len(body) > 10:
                        post_data = ""
                        try:
                            post_data = response.request.post_data or ""
                        except:
                            pass
                        all_network.append({
                            'path': url.replace(BASE_URL, ''),
                            'post_data': post_data[:300],
                            'body': body,
                        })
                        if '579705' in body or TARGET_CASE in body:
                            print(f"\n*** 목표 사건번호 발견! ***")
                            print(f"경로: {url.replace(BASE_URL, '')}")
                            print(f"응답: {body[:600]}")
                except:
                    pass

        page.on('response', on_response)

        # 메인 페이지 방문 및 JS 환경 초기화
        print("\n[1] 메인 페이지 방문 및 JS 초기화")
        await page.goto(f"{BASE_URL}/pgj/index.on", wait_until='networkidle', timeout=30000)
        await asyncio.sleep(3)
        print(f"  URL: {page.url}, 캡처된 API: {len(all_network)}개")

        # 경매사건검색 탭 클릭 (JavaScript로 직접)
        print("\n[2] 경매사건검색 탭 JavaScript 클릭")
        try:
            result = await page.evaluate("""
                () => {
                    const allLinks = document.querySelectorAll('a, button, li, div, span');
                    for (const el of allLinks) {
                        const text = el.textContent.trim();
                        if (text === '경매사건검색' || text.includes('경매사건검색')) {
                            el.click();
                            return '클릭: ' + text;
                        }
                    }
                    return '못찾음';
                }
            """)
            print(f"  결과: {result}")
            await asyncio.sleep(3)
        except Exception as e:
            print(f"  오류: {e}")

        prev_count = len(all_network)

        # JavaScript로 검색 API 직접 호출
        print("\n[3] JavaScript fetch()로 검색 API 직접 호출")

        # 경매사건 검색 API 경로 후보들
        search_paths = [
            "/pgj/pgj159/selectAuctnCsrchRslt.on",
            "/pgj/pgj15/selectAuctnCsSrchRslt.on",
            "/pgj/pgj15af/selectAuctnCsSrchRslt.on",
            "/pgj/pgj15af00/selectAuctnCsSrchRslt.on",
        ]

        payloads = [
            json.dumps({"cortOfcCd": TARGET_COURT_CODE, "auctnYear": TARGET_YEAR, "csNo": TARGET_NUMBER}),
            json.dumps({"cortOfcCd": TARGET_COURT_CODE, "saNo": TARGET_CASE}),
            json.dumps({"auctnYear": TARGET_YEAR, "csNo": TARGET_NUMBER}),
            json.dumps({"saNo": TARGET_CASE}),
        ]

        for search_path in search_paths:
            for payload_str in payloads[:2]:
                try:
                    result = await page.evaluate(f"""
                        async () => {{
                            try {{
                                const resp = await fetch('{search_path}', {{
                                    method: 'POST',
                                    headers: {{
                                        'Content-Type': 'application/json',
                                        'X-Requested-With': 'XMLHttpRequest'
                                    }},
                                    body: '{payload_str}'
                                }});
                                const text = await resp.text();
                                return {{
                                    path: '{search_path}',
                                    status: resp.status,
                                    size: text.length,
                                    isJson: text.trim().startsWith('{{') || text.trim().startsWith('['),
                                    body: text.substring(0, 500)
                                }};
                            }} catch(e) {{
                                return {{error: e.toString()}};
                            }}
                        }}
                    """)

                    if result.get('isJson'):
                        print(f"\n  *** JSON 응답! {search_path} ***")
                        print(f"  payload: {payload_str}")
                        print(f"  응답: {result.get('body', '')[:400]}")
                    elif result.get('size', 0) not in [0, 29030, 2478]:
                        print(f"\n  다른 응답 ({result.get('size')}bytes): {search_path}")
                        print(f"  {result.get('body', '')[:200]}")

                except Exception as e:
                    pass

        # 4. 직접 폼 요소 조작 (탭 전환 후)
        print("\n[4] 폼 직접 조작 시도")
        try:
            form_result = await page.evaluate("""
                async () => {
                    // 법원 SELECT 찾기
                    const courtSel = document.querySelector('[id*="auctnCsSrchCortOfc"]') ||
                                    document.querySelector('[id*="CortOfc"]');
                    const yearSel = document.querySelector('[id*="auctnCsSrchCsYear"]') ||
                                   document.querySelector('[id*="CsYear"]');
                    const noInput = document.querySelector('[id*="auctnCsSrchCsNo"]') ||
                                   document.querySelector('[id*="CsNo"]');
                    const searchBtn = document.querySelector('[id*="auctnCsSrchBtn"]') ||
                                     document.querySelector('[id*="SrchBtn"]');

                    return {
                        courtFound: !!courtSel,
                        courtId: courtSel ? courtSel.id : null,
                        yearFound: !!yearSel,
                        yearId: yearSel ? yearSel.id : null,
                        noFound: !!noInput,
                        noId: noInput ? noInput.id : null,
                        btnFound: !!searchBtn,
                        btnId: searchBtn ? searchBtn.id : null,
                        allSelectIds: Array.from(document.querySelectorAll('select')).map(s => s.id).slice(0, 10),
                        allInputIds: Array.from(document.querySelectorAll('input')).map(i => ({id: i.id, type: i.type})).filter(i => i.type !== 'hidden').slice(0, 15)
                    };
                }
            """)
            print(f"  폼 요소 탐색:")
            print(f"    법원 SELECT: {form_result.get('courtId', '없음')}")
            print(f"    연도 SELECT: {form_result.get('yearId', '없음')}")
            print(f"    번호 INPUT: {form_result.get('noId', '없음')}")
            print(f"    검색 BTN: {form_result.get('btnId', '없음')}")
            print(f"    모든 SELECT IDs: {form_result.get('allSelectIds', [])}")
            print(f"    모든 INPUT IDs:")
            for inp in form_result.get('allInputIds', []):
                print(f"      - {inp}")

        except Exception as e:
            print(f"  오류: {e}")

        # 5. 발견된 IDs로 실제 검색 수행
        if form_result.get('noId'):
            print(f"\n[5] 발견된 ID로 실제 검색 수행")
            no_id = form_result['noId']
            btn_id = form_result.get('btnId')

            try:
                # 법원 선택
                if form_result.get('courtId'):
                    court_id = form_result['courtId']
                    await page.select_option(f'#{court_id}', TARGET_COURT_CODE)
                    await asyncio.sleep(0.5)
                    print(f"  법원 선택 완료")

                # 연도 선택
                if form_result.get('yearId'):
                    year_id = form_result['yearId']
                    await page.select_option(f'#{year_id}', TARGET_YEAR)
                    await asyncio.sleep(0.5)
                    print(f"  연도 선택 완료")

                # 번호 입력
                await page.fill(f'#{no_id}', TARGET_NUMBER)
                await asyncio.sleep(0.5)
                print(f"  번호 입력 완료: {TARGET_NUMBER}")

                # 검색
                if btn_id:
                    await page.click(f'#{btn_id}')
                else:
                    await page.keyboard.press('Enter')
                print(f"  검색 실행!")

                await page.wait_for_load_state('networkidle', timeout=15000)
                await asyncio.sleep(3)

                # 결과 확인
                new_apis = all_network[prev_count:]
                print(f"  새로 캡처된 JSON API: {len(new_apis)}개")

                for api in new_apis:
                    print(f"\n  경로: {api['path']}")
                    print(f"  요청: {api['post_data'][:150]}")
                    print(f"  응답: {api['body'][:400]}")

                page_text = await page.inner_text('body')
                if '579705' in page_text:
                    idx = page_text.find('579705')
                    print(f"\n  *** 사건번호 발견! ***")
                    print(f"  {page_text[max(0,idx-50):idx+200]}")
                else:
                    await page.screenshot(path='court_js_result.png')
                    print("  사건번호 미발견. 스크린샷 -> court_js_result.png")

            except Exception as e:
                print(f"  검색 오류: {e}")

        await browser.close()

        # 결과 요약
        print(f"\n\n{'='*70}")
        print(f"최종 결과 요약")
        print("=" * 70)
        print(f"캡처된 JSON API: {len(all_network)}개")
        for api in all_network:
            if '579705' in api['body'] or TARGET_CASE in api['body']:
                print(f"\n*** 목표 사건번호 포함 API ***")
                print(f"경로: {api['path']}")
                print(f"전체 응답:\n{api['body'][:1000]}")


if __name__ == "__main__":
    asyncio.run(run())
