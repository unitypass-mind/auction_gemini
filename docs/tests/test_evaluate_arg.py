# -*- coding: utf-8 -*-
"""
Playwright page.evaluate() 인자 유무에 따른 동작 차이 테스트
"""
import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

COURT_SELECT_ID = 'mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc'
BASE_URL = "https://www.courtauction.go.kr"

async def run():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--lang=ko-KR'])
        page = await browser.new_page()

        # 1. 메인 페이지
        print("[1] 메인 페이지...")
        await page.goto(f"{BASE_URL}/pgj/index.on", wait_until='networkidle', timeout=30000)
        await asyncio.sleep(2)

        # 2. 탭 클릭
        print("[2] 경매사건검색 탭 클릭...")
        await page.evaluate("""
            () => {
                for (const a of document.querySelectorAll('a')) {
                    if (a.textContent.trim() === '경매사건검색') { a.click(); return; }
                }
            }
        """)
        await asyncio.sleep(4)
        await page.wait_for_selector('#mf_wfm_mainFrame_ibx_auctnCsSrchCsNo', state='visible', timeout=10000)
        print("   -> 폼 로드됨")

        # 3. arg 없는 SELECT 확인
        r1 = await page.evaluate(f"""
            () => {{
                const s = document.getElementById('{COURT_SELECT_ID}');
                return s ? 'YES:' + s.options.length : 'NO';
            }}
        """)
        print(f"[3] arg 없는 evaluate: {r1}")

        # 4. arg 있는 SELECT 확인 (문자열 arg)
        r2 = await page.evaluate(f"""
            (x) => {{
                const s = document.getElementById('{COURT_SELECT_ID}');
                return s ? 'YES:' + s.options.length + ':arg=' + x : 'NO:arg=' + x;
            }}
        """, "test_value")
        print(f"[4] string arg evaluate: {r2}")

        # 5. arg 있는 SELECT 확인 (한국어 arg)
        r3 = await page.evaluate(f"""
            (name) => {{
                const s = document.getElementById('{COURT_SELECT_ID}');
                return s ? 'YES:' + s.options.length + ':name_len=' + name.length : 'NO:name_len=' + name.length;
            }}
        """, "서울중앙지방법원")
        print(f"[5] Korean arg evaluate: {r3}")

        # 6. dict arg 있는 SELECT 확인
        r4 = await page.evaluate(f"""
            (args) => {{
                const s = document.getElementById('{COURT_SELECT_ID}');
                return s ? 'YES:' + s.options.length + ':year=' + args.year : 'NO:year=' + args.year;
            }}
        """, {"year": "2024", "number": "579705"})
        print(f"[6] dict arg evaluate: {r4}")

        # 7. 연도/번호 입력 후 확인
        await page.evaluate("""
            (args) => {
                const yr = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCsYear');
                if (yr) {
                    for (const opt of yr.options) {
                        if (opt.value === args.year) {
                            opt.selected = true;
                            yr.dispatchEvent(new Event('change', {bubbles: true}));
                        }
                    }
                }
                const no = document.getElementById('mf_wfm_mainFrame_ibx_auctnCsSrchCsNo');
                if (no) { no.value = args.number; no.dispatchEvent(new Event('input', {bubbles: true})); }
            }
        """, {"year": "2024", "number": "579705"})

        # 8. 연도 입력 후 즉시 SELECT 확인
        r5 = await page.evaluate(f"""
            () => {{
                const s = document.getElementById('{COURT_SELECT_ID}');
                return s ? 'YES:' + s.options.length : 'NO';
            }}
        """)
        print(f"[8] 연도 입력 후 arg없음: {r5}")

        r6 = await page.evaluate(f"""
            (name) => {{
                const s = document.getElementById('{COURT_SELECT_ID}');
                return s ? 'YES:' + s.options.length : 'NO';
            }}
        """, "서울중앙지방법원")
        print(f"[9] 연도 입력 후 Korean arg: {r6}")

        await browser.close()
        print("\n완료!")

asyncio.run(run())
