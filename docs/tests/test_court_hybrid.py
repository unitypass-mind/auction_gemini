# -*- coding: utf-8 -*-
"""
하이브리드 법원 검색 테스트
1. 법원 목록 API (IP 차단 없음)
2. 폼 버튼 클릭 + expect_response 방식
"""
import asyncio
import json
import re
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TARGET_CASE = "2024타경579705"
BASE_URL = "https://www.courtauction.go.kr"


async def run():
    from playwright.async_api import async_playwright

    m = re.match(r'(\d{4})타경(\d+)', TARGET_CASE)
    case_year = m.group(1)
    case_number = m.group(2)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--lang=ko-KR'])
        context = await browser.new_context(locale='ko-KR')
        page = await context.new_page()

        print("[1] 세션 초기화...")
        await page.goto(f"{BASE_URL}/pgj/index.on", wait_until='networkidle', timeout=30000)
        await asyncio.sleep(2)
        print("  -> 완료")

        print("[2] 법원 목록 API 조회...")
        court_list = await page.evaluate("""
            async () => {
                const resp = await fetch('/pgj/pgj002/selectCortOfcLst.on', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'},
                    body: JSON.stringify({"cortExecrOfcDvsCd": "00079B"})
                });
                const data = await resp.json();
                return data.data?.cortOfcLst || [];
            }
        """)
        court_map = {c['code']: c['name'] for c in court_list}
        print(f"  -> {len(court_list)}개 법원 코드 획득")

        print("[3] 경매사건검색 탭 클릭...")
        await page.evaluate("""
            () => {
                for (const a of document.querySelectorAll('a')) {
                    if (a.textContent.trim() === '경매사건검색') { a.click(); return; }
                }
            }
        """)
        await asyncio.sleep(4)

        print("[4] 입력 필드 대기...")
        try:
            await page.wait_for_selector(
                '#mf_wfm_mainFrame_ibx_auctnCsSrchCsNo',
                state='visible', timeout=10000
            )
            print("  -> 로드 완료")
        except Exception as e:
            print(f"  -> 실패: {e}")
            await browser.close()
            return

        print(f"[5] 연도({case_year})/번호({case_number}) 입력...")
        await page.evaluate("""
            (args) => {
                const yr = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCsYear');
                if (yr) {
                    for (const opt of yr.options) {
                        if (opt.value === args.year || opt.text === args.year) {
                            opt.selected = true;
                            yr.dispatchEvent(new Event('change', {bubbles: true}));
                        }
                    }
                }
                const no = document.getElementById('mf_wfm_mainFrame_ibx_auctnCsSrchCsNo');
                if (no) {
                    no.value = args.number;
                    no.dispatchEvent(new Event('input', {bubbles: true}));
                }
            }
        """, {"year": case_year, "number": case_number})

        # 드롭다운 value 구조 확인
        select_info = await page.evaluate("""
            () => {
                const sel = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc');
                if (!sel) return null;
                return {
                    currentValue: sel.value,
                    sampleOptions: Array.from(sel.options).slice(1, 4).map(o => ({value: o.value, text: o.text}))
                };
            }
        """)
        print(f"  드롭다운 구조: {json.dumps(select_info, ensure_ascii=False)}")

        # 인천 법원부터 테스트 (이름으로 선택 - value가 이름임)
        test_courts = ['B000240', 'B000241', 'B000210']

        for court_code in test_courts:
            court_name = court_map.get(court_code, court_code)
            print(f"\n[6] {court_name}({court_code}) 선택...")

            sel_result = await page.evaluate("""
                (name) => {
                    const sel = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc');
                    if (!sel) return 'NO_SELECT';
                    for (const opt of sel.options) {
                        if (opt.value === name || opt.text === name) {
                            opt.selected = true;
                            sel.dispatchEvent(new Event('change', {bubbles: true}));
                            return 'OK:' + opt.text + ' (value=' + opt.value + ')';
                        }
                    }
                    return 'NOT_FOUND in ' + sel.options.length + ' options';
                }
            """, court_name)
            print(f"  선택 결과: {sel_result}")

            if 'NOT_FOUND' in sel_result or 'NO_SELECT' in sel_result:
                print(f"  -> 건너뜀")
                continue

            print("  검색 버튼 클릭 + 응답 캡처...")
            try:
                async with page.expect_response(
                    lambda r: 'selectAuctnCsSrchRslt' in r.url,
                    timeout=10000
                ) as resp_info:
                    await page.evaluate("""
                        () => {
                            const btn = document.getElementById('mf_wfm_mainFrame_btn_auctnCsSrchBtn');
                            if (btn) btn.click();
                        }
                    """)

                resp = await resp_info.value
                body = await resp.text()
                data = json.loads(body)
                case_data = data.get('data', {})
                ipcheck = case_data.get('ipcheck', True) if case_data else 'N/A'
                has_data = bool(case_data and case_data.get('dma_csBasInf') is not None)

                print(f"  응답: ipcheck={ipcheck}, 데이터있음={has_data}")
                if has_data:
                    print("  *** 성공! 사건 정보 발견! ***")
                    print(json.dumps(case_data.get('dma_csBasInf'), ensure_ascii=False, indent=2)[:500])
                    break
                elif ipcheck is False:
                    print("  IP 차단 감지!")
                else:
                    print(f"  해당 법원에 사건 없음 (data keys: {list(case_data.keys()) if case_data else 'null'})")

            except Exception as e:
                print(f"  오류: {type(e).__name__}: {str(e)[:150]}")

        await browser.close()
        print("\n완료!")


if __name__ == "__main__":
    asyncio.run(run())
