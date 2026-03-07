# -*- coding: utf-8 -*-
"""
법원 경매 - SELECT value는 이름, 코드가 아님!
'인천지방법원'으로 선택해야 함
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
TARGET_COURT_NAME = "인천지방법원"  # 코드가 아닌 이름!

BASE_URL = "https://www.courtauction.go.kr"
results = []

async def run():
    async with async_playwright() as p:
        print("=" * 70)
        print(f"인천지방법원으로 {TARGET_CASE} 검색")
        print("=" * 70)

        browser = await p.chromium.launch(headless=True, args=['--lang=ko-KR'])
        context = await browser.new_context(locale='ko-KR')
        page = await context.new_page()

        async def on_response(response):
            url = response.url
            if 'pgj15' in url.lower():
                try:
                    body = await response.text()
                    if body.strip().startswith('{'):
                        post_data = ""
                        try:
                            post_data = response.request.post_data or ""
                        except:
                            pass
                        results.append({'path': url.replace(BASE_URL, ''), 'post_data': post_data, 'body': body, 'status': response.status})
                        data = json.loads(body)
                        print(f"\n[캡처] {url.replace(BASE_URL, '')}")
                        print(f"  요청: {post_data[:100]}")
                        print(f"  Status: {data.get('status')}, Msg: {data.get('message', '')[:70]}")
                        if data.get('data', {}) and data['data'].get('dma_csBasInf') is not None:
                            print(f"  *** 사건 정보 있음! ***")
                        elif not data.get('data', {}).get('ipcheck', True):
                            print(f"  => IP 차단!")
                except:
                    pass

        page.on('response', on_response)

        # 메인 페이지 방문
        await page.goto(f"{BASE_URL}/pgj/index.on", wait_until='networkidle', timeout=30000)
        await asyncio.sleep(3)

        # 탭 클릭
        await page.evaluate("""
            () => {
                for (const a of document.querySelectorAll('a')) {
                    if (a.textContent.trim() === '경매사건검색') { a.click(); return; }
                }
            }
        """)
        await asyncio.sleep(4)

        # 입력 필드 대기
        try:
            await page.wait_for_selector('#mf_wfm_mainFrame_ibx_auctnCsSrchCsNo', timeout=8000)
        except:
            print("  입력 필드 로드 실패")
            await browser.close()
            return

        # SELECT value 구조 확인
        select_info = await page.evaluate("""
            () => {
                const sel = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc');
                if (!sel) return null;
                return {
                    currentValue: sel.value,
                    options: Array.from(sel.options).map(o => ({value: o.value, text: o.text})).slice(0, 5)
                };
            }
        """)
        print(f"\n법원 SELECT 구조: {json.dumps(select_info, ensure_ascii=False, indent=2)}")

        # 인천지방법원 선택 (이름으로)
        print(f"\n인천지방법원 선택 중...")
        court_set = await page.evaluate(f"""
            () => {{
                const sel = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc');
                if (!sel) return 'SELECT 없음';

                // 이름으로 찾기
                for (const opt of sel.options) {{
                    if (opt.text === '{TARGET_COURT_NAME}' || opt.value === '{TARGET_COURT_NAME}') {{
                        opt.selected = true;
                        sel.dispatchEvent(new Event('change', {{bubbles: true}}));
                        return '선택됨: ' + opt.text + ' (value=' + opt.value + ')';
                    }}
                }}

                // 부분 매칭
                for (const opt of sel.options) {{
                    if (opt.text.includes('인천') || opt.value.includes('인천')) {{
                        opt.selected = true;
                        sel.dispatchEvent(new Event('change', {{bubbles: true}}));
                        return '부분매칭: ' + opt.text + ' (value=' + opt.value + ')';
                    }}
                }}

                // 전체 옵션 목록
                return '인천 못찾음. 전체: ' + Array.from(sel.options).map(o=>o.text).join(',').substring(0, 200);
            }}
        """)
        print(f"결과: {court_set}")
        await asyncio.sleep(1)

        # 연도 선택
        await page.evaluate(f"""
            () => {{
                const sel = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCsYear');
                if (sel) {{
                    for (const opt of sel.options) {{
                        if (opt.text === '{TARGET_YEAR}' || opt.value === '{TARGET_YEAR}') {{
                            opt.selected = true;
                            sel.dispatchEvent(new Event('change', {{bubbles: true}}));
                        }}
                    }}
                }}
            }}
        """)

        # 번호 입력
        await page.evaluate(f"""
            () => {{
                const inp = document.getElementById('mf_wfm_mainFrame_ibx_auctnCsSrchCsNo');
                if (inp) {{
                    inp.value = '{TARGET_NUMBER}';
                    inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                }}
            }}
        """)

        # 현재 상태 확인
        state = await page.evaluate("""
            () => ({
                court: document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc')?.value,
                year: document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCsYear')?.value,
                no: document.getElementById('mf_wfm_mainFrame_ibx_auctnCsSrchCsNo')?.value
            })
        """)
        print(f"\n현재 입력 상태: {json.dumps(state, ensure_ascii=False)}")

        # 검색 버튼 클릭
        print("\n검색 실행...")
        prev = len(results)
        await page.evaluate("""
            () => {
                const btn = document.getElementById('mf_wfm_mainFrame_btn_auctnCsSrchBtn');
                if (btn) btn.click();
            }
        """)
        await page.wait_for_load_state('networkidle', timeout=20000)
        await asyncio.sleep(3)

        # 결과 확인
        new_results = results[prev:]
        print(f"\n검색 후 API: {len(new_results)}개")

        page_text = await page.inner_text('body')
        if '579705' in page_text:
            idx = page_text.find('579705')
            ctx = page_text[max(0,idx-50):idx+200]
            print(f"\n페이지 결과:\n{ctx}")

        await browser.close()

        # 분석
        if new_results:
            print(f"\n\n{'='*70}")
            print("검색 결과 API 분석")
            print("=" * 70)
            for r in new_results:
                try:
                    data = json.loads(r['body'])
                    print(f"\n경로: {r['path']}")
                    print(f"요청: {r['post_data']}")
                    print(f"Status: {data.get('status')}")
                    print(f"Message: {data.get('message')}")
                    d = data.get('data', {})
                    if d:
                        for k, v in d.items():
                            if v is not None:
                                print(f"  {k}: {json.dumps(v, ensure_ascii=False)[:300]}")
                except:
                    pass


if __name__ == "__main__":
    asyncio.run(run())
