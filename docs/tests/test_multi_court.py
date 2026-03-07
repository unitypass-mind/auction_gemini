# -*- coding: utf-8 -*-
"""
다중 법원 순차 검색 디버깅 테스트
_court_site_search_async 로직을 그대로 재현하되 각 단계 상세 출력
"""
import asyncio
import json
import re
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TARGET_CASE = "2024타경579705"
BASE_URL = "https://www.courtauction.go.kr"
MAX_COURTS = 10  # 최대 10개 법원만 테스트


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

        print("[2] 법원 목록 API...")
        court_list_result = await page.evaluate("""
            async () => {
                const resp = await fetch('/pgj/pgj002/selectCortOfcLst.on', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'},
                    body: JSON.stringify({"cortExecrOfcDvsCd": "00079B"})
                });
                return await resp.json();
            }
        """)

        court_code_to_name = {}
        all_court_codes = []
        if court_list_result and court_list_result.get('data'):
            courts_data = court_list_result['data'].get('cortOfcLst', [])
            for c in courts_data:
                code = c.get('code', '')
                name = c.get('name', '')
                if code:
                    court_code_to_name[code] = name
                    all_court_codes.append(code)
        print(f"  -> {len(all_court_codes)}개 법원 코드")

        # 인천지방법원(B000240)부터 테스트
        courts_to_try = ["B000240", "B000241", "B000210"]

        print("[3] 탭 클릭...")
        await page.evaluate("""
            () => {
                for (const a of document.querySelectorAll('a')) {
                    if (a.textContent.trim() === '경매사건검색') { a.click(); return; }
                }
            }
        """)
        await asyncio.sleep(4)
        await page.wait_for_selector('#mf_wfm_mainFrame_ibx_auctnCsSrchCsNo', state='visible', timeout=10000)
        print("  -> 폼 로드됨")

        print("[4] 연도/번호 입력 (year change 이벤트 포함)...")
        await page.evaluate("""
            (args) => {
                const yr = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCsYear');
                if (yr) {
                    for (const opt of yr.options) {
                        if (opt.text === args.year || opt.value === args.year) {
                            opt.selected = true;
                            yr.dispatchEvent(new Event('change', {bubbles: true}));
                            break;
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

        # year change 이벤트로 AJAX가 발생하여 court SELECT가 재구성될 수 있음
        # 재구성이 완료될 때까지 court SELECT가 다시 나타날 때까지 대기
        print("[4.5] year change AJAX 완료 대기 (court SELECT 재등장)...")
        try:
            await page.wait_for_selector(
                '#mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc',
                state='visible', timeout=8000
            )
            print("  -> court SELECT 재등장 확인")
        except Exception as e:
            print(f"  -> court SELECT 대기 실패: {e}")

        court_select_count = await page.evaluate("""
            () => {
                const sel = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc');
                return sel ? sel.options.length : 0;
            }
        """)
        print(f"[5] 법원 SELECT: {court_select_count}개 옵션")

        print(f"\n[6] 법원 순차 검색 (최대 {MAX_COURTS}개)...")
        for i, court_code in enumerate(courts_to_try[:MAX_COURTS]):
            court_name = court_code_to_name.get(court_code, court_code)
            print(f"\n  [{i+1}] {court_name}({court_code})")

            if i > 0:
                print(f"     탭 재클릭...")
                await page.evaluate("""
                    () => {
                        for (const a of document.querySelectorAll('a')) {
                            if (a.textContent.trim() === '경매사건검색') { a.click(); return; }
                        }
                    }
                """)
                try:
                    await page.wait_for_selector('#mf_wfm_mainFrame_ibx_auctnCsSrchCsNo', state='visible', timeout=8000)
                    await page.wait_for_selector('#mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc', state='visible', timeout=8000)
                    print(f"     -> 폼 재로드 완료")
                except Exception as e:
                    print(f"     -> 폼 재로드 실패: {e}")
                    break

                await page.evaluate("""
                    (args) => {
                        const yr = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCsYear');
                        if (yr) {
                            for (const opt of yr.options) {
                                if (opt.text === args.year || opt.value === args.year) {
                                    opt.selected = true; break;
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
                print(f"     -> 연도/번호 재입력 완료")

            # 법원 SELECT 상태 확인
            sel_info = await page.evaluate("""
                () => {
                    const sel = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc');
                    if (!sel) return null;
                    return {count: sel.options.length, first_few: Array.from(sel.options).slice(0,3).map(o => o.text)};
                }
            """)
            if sel_info:
                print(f"     SELECT: {sel_info['count']}개 옵션, 샘플: {sel_info['first_few']}")
            else:
                print(f"     SELECT: 없음!")

            # test_court_hybrid.py 방식 그대로: 분리된 evaluate 호출
            # 1단계: 법원 선택 + change 이벤트 (test_court_hybrid.py와 동일)
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
            print(f"     선택결과: {sel_result}")

            if 'NOT_FOUND' in sel_result or 'NO_SELECT' in sel_result:
                print(f"     -> 건너뜀")
                continue

            # 2단계: 검색 버튼 클릭 (test_court_hybrid.py와 동일, 별도 evaluate)
            print(f"     검색 버튼 클릭...")
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
                resp_data = json.loads(body)
                case_data = resp_data.get('data', {})
                ipcheck = case_data.get('ipcheck') if case_data else 'N/A'
                has_data = bool(case_data and case_data.get('dma_csBasInf') is not None)

                print(f"     응답: ipcheck={ipcheck}, 데이터={has_data}")
                if has_data:
                    print(f"\n  *** 성공! {court_name}에서 사건 발견! ***")
                    info = case_data.get('dma_csBasInf', {})
                    print(f"  소재지: {info.get('trnsfRealRqstUseAdr', 'N/A')}")
                    break
                elif ipcheck is False:
                    print("     -> IP 차단!")
                    break

            except Exception as e:
                print(f"     -> 오류: {type(e).__name__}: {str(e)[:100]}")

        await browser.close()
        print("\n완료!")


if __name__ == "__main__":
    asyncio.run(run())
