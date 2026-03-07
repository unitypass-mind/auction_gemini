# -*- coding: utf-8 -*-
"""
Playwright로 실제 법원 경매 검색 폼 사용
- 메인 페이지에서 사건번호 입력 필드 찾아 직접 검색
- 검색 결과 API 캡처
"""

import asyncio
import json
import sys
import io
from playwright.async_api import async_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TARGET_CASE = "2024타경579705"
BASE_URL = "https://www.courtauction.go.kr"

all_api_calls = []

async def run():
    async with async_playwright() as p:
        print("=" * 70)
        print("Playwright - 실제 검색 폼 사용하여 사건번호 조회")
        print("=" * 70)

        browser = await p.chromium.launch(headless=True, args=['--lang=ko-KR'])
        context = await browser.new_context(
            locale='ko-KR',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        # 모든 .on API 응답 캡처
        async def on_response(response):
            url = response.url
            if 'courtauction.go.kr' in url and '.on' in url:
                try:
                    body = await response.text()
                    ctype = response.headers.get('content-type', '')
                    is_json = body.strip().startswith('{') or body.strip().startswith('[') or 'json' in ctype
                    post_data = ""
                    try:
                        post_data = response.request.post_data or ""
                    except:
                        pass

                    all_api_calls.append({
                        'url': url,
                        'path': url.replace(BASE_URL, ''),
                        'method': response.request.method,
                        'status': response.status,
                        'is_json': is_json,
                        'size': len(body),
                        'post_data': post_data[:300],
                        'body': body[:400] if is_json else '',
                    })
                except:
                    pass

        page.on('response', on_response)

        # 1. 메인 페이지 방문 및 로드
        print("\n[1] 메인 페이지 방문")
        await page.goto(f"{BASE_URL}/pgj/index.on", wait_until='networkidle', timeout=30000)
        await asyncio.sleep(2)
        print(f"  URL: {page.url}")

        # 2. 페이지 내 모든 입력 필드 분석
        print("\n[2] 페이지 입력 필드 분석")
        inputs_info = await page.evaluate("""
            () => {
                const inputs = document.querySelectorAll('input, select, textarea');
                return Array.from(inputs).map(el => ({
                    tag: el.tagName,
                    type: el.type || '',
                    name: el.name || '',
                    id: el.id || '',
                    placeholder: el.placeholder || '',
                    className: el.className.substring(0, 50),
                    value: el.value || ''
                })).filter(el => el.type !== 'hidden');
            }
        """)

        print(f"  총 입력 필드: {len(inputs_info)}개")
        for inp in inputs_info:
            if inp['type'] not in ['button', 'submit', 'checkbox', 'radio', 'image']:
                print(f"    [{inp['tag']}] name={inp['name']}, id={inp['id']}, placeholder={inp['placeholder'][:30]}")

        # 3. 탭 구조 분석 (경매사건검색 탭 찾기)
        print("\n[3] 탭 및 메뉴 구조 분석")
        tabs = await page.evaluate("""
            () => {
                const tabs = document.querySelectorAll('a, button, li[class*="tab"], div[class*="tab"]');
                return Array.from(tabs)
                    .filter(el => el.textContent.includes('사건') || el.textContent.includes('검색') || el.textContent.includes('경매'))
                    .map(el => ({
                        tag: el.tagName,
                        text: el.textContent.trim().substring(0, 30),
                        href: el.href || '',
                        onclick: (el.getAttribute('onclick') || '').substring(0, 100)
                    }))
                    .slice(0, 15);
            }
        """)

        print(f"  검색 관련 탭/링크: {len(tabs)}개")
        for tab in tabs:
            print(f"    [{tab['tag']}] '{tab['text']}' href={tab['href'][:50]} onclick={tab['onclick'][:60]}")

        # 4. 사건번호 검색 탭 클릭
        print("\n[4] '경매사건검색' 탭 클릭 시도")
        prev_api_count = len(all_api_calls)

        # 다양한 방법으로 사건번호 탭 찾기
        search_tab_clicked = False

        # 방법 A: 텍스트로 클릭
        tab_keywords = ['사건번호', '경매사건', '사건검색']
        for kw in tab_keywords:
            try:
                elem = page.get_by_text(kw, exact=False)
                if await elem.count() > 0:
                    await elem.first.click()
                    await asyncio.sleep(2)
                    print(f"  '{kw}' 클릭 성공!")
                    search_tab_clicked = True
                    break
            except:
                pass

        if not search_tab_clicked:
            print("  직접 탭 클릭 실패. JavaScript로 탭 전환 시도...")
            # JavaScript로 탭 전환
            try:
                await page.evaluate("""
                    () => {
                        // 다양한 탭 전환 방법 시도
                        const links = document.querySelectorAll('a');
                        for (const link of links) {
                            if (link.textContent.includes('사건') || link.textContent.includes('번호')) {
                                link.click();
                                return link.textContent;
                            }
                        }
                        return null;
                    }
                """)
                await asyncio.sleep(2)
            except:
                pass

        # 5. 사건번호 입력 필드 찾아 검색
        print("\n[5] 사건번호 입력 및 검색")

        # 사건번호 관련 필드 찾기
        case_input_selectors = [
            'input[name*="saNo"]',
            'input[name*="csNo"]',
            'input[name*="caseNo"]',
            'input[name*="case"]',
            'input[name*="Sa"]',
            'input[placeholder*="사건"]',
            'input[placeholder*="번호"]',
            '#saNo', '#csNo', '#caseNo',
        ]

        case_input = None
        for selector in case_input_selectors:
            try:
                elem = await page.query_selector(selector)
                if elem and await elem.is_visible():
                    case_input = elem
                    print(f"  사건번호 입력 필드 발견: {selector}")
                    break
            except:
                continue

        if case_input:
            # 입력 및 검색
            await case_input.clear()
            await case_input.type(TARGET_CASE)
            await asyncio.sleep(1)

            # 검색 버튼 찾기
            search_btns = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("검색")',
                '.btn-search', '#btnSearch', '#btn_search',
                'button[onclick*="search"]',
                'a[onclick*="search"]',
            ]

            for btn_sel in search_btns:
                try:
                    btn = await page.query_selector(btn_sel)
                    if btn and await btn.is_visible():
                        print(f"  검색 버튼 클릭: {btn_sel}")
                        await btn.click()
                        await page.wait_for_load_state('networkidle', timeout=15000)
                        await asyncio.sleep(3)
                        break
                except:
                    continue
            else:
                print("  Enter로 검색")
                await case_input.press('Enter')
                await page.wait_for_load_state('networkidle', timeout=15000)
                await asyncio.sleep(3)

        else:
            print("  입력 필드를 찾지 못함")
            # 현재 페이지 HTML 저장
            html = await page.content()
            with open('court_main_page.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print("  HTML -> court_main_page.html 저장")

        # 6. 검색 후 캡처된 API 분석
        new_apis = all_api_calls[prev_api_count:]
        print(f"\n[6] 검색 후 캡처된 새 API: {len(new_apis)}개")

        for api in new_apis:
            if api['is_json']:
                print(f"\n  [JSON] {api['path']}")
                print(f"    요청: {api['post_data'][:100]}")
                print(f"    응답: {api['body'][:250]}")
                if "579705" in api['body'] or TARGET_CASE in api['body']:
                    print(f"\n  *** 목표 사건번호 발견! ***")

        # 7. 검색 결과 확인
        print("\n[7] 검색 결과 확인")
        page_text = await page.inner_text('body')
        if "579705" in page_text:
            print(f"  *** 페이지에 사건번호 발견! ***")
            # 주변 텍스트 추출
            idx = page_text.find("579705")
            print(f"  컨텍스트: ...{page_text[max(0,idx-50):idx+100]}...")
        else:
            print("  사건번호 미발견. 스크린샷 저장...")
            await page.screenshot(path='court_result.png')
            print("  -> court_result.png 저장")

        await browser.close()

        # 최종 결과
        print(f"\n\n{'='*70}")
        print("최종 결과 - 캡처된 모든 JSON API")
        print("=" * 70)

        json_apis = [a for a in all_api_calls if a['is_json']]
        print(f"\nJSON API {len(json_apis)}개 발견:")
        seen = set()
        for api in json_apis:
            if api['path'] not in seen:
                seen.add(api['path'])
                print(f"\n경로: {api['path']}")
                print(f"  POST 데이터: {api['post_data'][:150]}")
                print(f"  응답 미리보기: {api['body'][:200]}")


if __name__ == "__main__":
    asyncio.run(run())
