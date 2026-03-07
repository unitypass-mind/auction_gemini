# -*- coding: utf-8 -*-
"""
법원 경매 - 인천지방법원으로 폼 방식 검색
법원 SELECT를 w2ui 컴포넌트 방식으로 올바르게 선택
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
INCHEON_CODE = "B000240"

BASE_URL = "https://www.courtauction.go.kr"
results = []

async def run():
    async with async_playwright() as p:
        print("=" * 70)
        print("법원 경매사건검색 - 인천지방법원으로 검색")
        print("=" * 70)

        browser = await p.chromium.launch(headless=True, args=['--lang=ko-KR'])
        context = await browser.new_context(locale='ko-KR')
        page = await context.new_page()

        # 모든 API 캡처
        async def on_response(response):
            url = response.url
            if 'courtauction.go.kr' in url and 'pgj15' in url.lower():
                try:
                    body = await response.text()
                    is_json = body.strip().startswith('{') or body.strip().startswith('[')
                    if is_json:
                        post_data = ""
                        try:
                            post_data = response.request.post_data or ""
                        except:
                            pass
                        results.append({
                            'path': url.replace(BASE_URL, ''),
                            'post_data': post_data,
                            'body': body,
                            'status': response.status
                        })
                        print(f"\n[API] {url.replace(BASE_URL, '')}")
                        print(f"  요청: {post_data[:150]}")
                        data = json.loads(body)
                        print(f"  Status: {data.get('status')}, Msg: {data.get('message', '')[:80]}")
                        if data.get('data', {}).get('dma_csBasInf'):
                            print(f"\n  *** 사건 정보 발견! ***")
                except:
                    pass

        page.on('response', on_response)

        # 메인 페이지 방문
        print("\n[1] 메인 페이지 방문")
        await page.goto(f"{BASE_URL}/pgj/index.on", wait_until='networkidle', timeout=30000)
        await asyncio.sleep(3)

        # 경매사건검색 탭 클릭
        print("\n[2] 경매사건검색 탭 클릭")
        await page.evaluate("""
            () => {
                const links = document.querySelectorAll('a');
                for (const link of links) {
                    if (link.textContent.trim() === '경매사건검색') {
                        link.click();
                        return;
                    }
                }
            }
        """)
        await asyncio.sleep(4)

        # 입력 필드 대기
        print("\n[3] 입력 필드 대기")
        try:
            await page.wait_for_selector('#mf_wfm_mainFrame_ibx_auctnCsSrchCsNo', state='visible', timeout=10000)
            print("  입력 필드 로드 완료!")
        except:
            print("  입력 필드 미발견")

        # w2ui 컴포넌트를 JavaScript로 직접 제어
        print(f"\n[4] 인천지방법원({INCHEON_CODE}) 선택 - w2ui 방식")
        court_set = await page.evaluate(f"""
            () => {{
                // 방법 1: 직접 value 설정
                const sel = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc');
                if (!sel) return 'SELECT 없음';

                // 옵션 목록 확인
                const options = Array.from(sel.options).map(o => o.value + ':' + o.text);

                // value 직접 설정
                for (const opt of sel.options) {{
                    if (opt.value === '{INCHEON_CODE}') {{
                        opt.selected = true;
                        // 모든 이벤트 트리거
                        sel.dispatchEvent(new Event('change', {{bubbles: true}}));
                        sel.dispatchEvent(new Event('input', {{bubbles: true}}));
                        sel.dispatchEvent(new MouseEvent('click', {{bubbles: true}}));

                        // w2ui 업데이트 시도
                        if (sel.w2field) sel.w2field.set('{INCHEON_CODE}');
                        if (window.w2ui) {{
                            const widgetId = sel.getAttribute('data-widget-id');
                            if (widgetId && w2ui[widgetId]) w2ui[widgetId].value = '{INCHEON_CODE}';
                        }}
                        return '선택됨: ' + opt.text + ' (' + sel.value + ')';
                    }}
                }}
                return '인천 코드 없음. 옵션: ' + options.slice(0, 5).join(', ');
            }}
        """)
        print(f"  결과: {court_set}")
        await asyncio.sleep(1)

        # 현재 선택된 값 확인
        current_court = await page.evaluate("""
            () => {
                const sel = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc');
                return sel ? {value: sel.value, text: sel.options[sel.selectedIndex]?.text} : null;
            }
        """)
        print(f"  현재 선택: {current_court}")

        # 연도 선택
        print(f"\n[5] 연도 선택: {TARGET_YEAR}")
        year_set = await page.evaluate(f"""
            () => {{
                const sel = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCsYear');
                if (!sel) return 'SELECT 없음';
                for (const opt of sel.options) {{
                    if (opt.value === '{TARGET_YEAR}' || opt.text === '{TARGET_YEAR}') {{
                        opt.selected = true;
                        sel.dispatchEvent(new Event('change', {{bubbles: true}}));
                        return '선택됨: ' + opt.text;
                    }}
                }}
                return '연도 없음';
            }}
        """)
        print(f"  결과: {year_set}")

        # 번호 입력
        print(f"\n[6] 번호 입력: {TARGET_NUMBER}")
        await page.evaluate(f"""
            () => {{
                const inp = document.getElementById('mf_wfm_mainFrame_ibx_auctnCsSrchCsNo');
                if (inp) {{
                    inp.value = '{TARGET_NUMBER}';
                    inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                    inp.dispatchEvent(new Event('change', {{bubbles: true}}));
                }}
            }}
        """)
        current_val = await page.evaluate("""
            () => document.getElementById('mf_wfm_mainFrame_ibx_auctnCsSrchCsNo')?.value
        """)
        print(f"  현재 값: {current_val}")

        # 검색 실행
        print("\n[7] 검색 실행")
        prev_count = len(results)
        await page.evaluate("""
            () => {
                const btn = document.getElementById('mf_wfm_mainFrame_btn_auctnCsSrchBtn');
                if (btn) btn.click();
            }
        """)
        await page.wait_for_load_state('networkidle', timeout=20000)
        await asyncio.sleep(3)

        # 결과 확인
        new_results = results[prev_count:]
        print(f"\n[8] 검색 후 캡처 API: {len(new_results)}개")

        # 페이지 텍스트 확인
        page_text = await page.inner_text('body')
        if '579705' in page_text:
            idx = page_text.find('579705')
            ctx = page_text[max(0,idx-100):idx+300]
            print(f"\n페이지에서 발견!")
            print(ctx)

        # 추가: fetch로 직접 API 호출 (폼 방식 후 IP 해제 확인)
        print(f"\n\n[9] 검색 API 직접 호출 (폼 후)")
        await asyncio.sleep(2)
        direct_result = await page.evaluate(f"""
            async () => {{
                const payload = {{
                    "dma_srchCsDtlInf": {{
                        "cortOfcCd": "{INCHEON_CODE}",
                        "csNo": "{TARGET_CASE}"
                    }}
                }};
                const resp = await fetch('/pgj/pgj15A/selectAuctnCsSrchRslt.on', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}},
                    body: JSON.stringify(payload)
                }});
                return {{status: resp.status, body: await resp.text()}};
            }}
        """)

        print(f"  Status: {direct_result['status']}")
        try:
            data = json.loads(direct_result['body'])
            print(f"  status: {data.get('status')}")
            print(f"  message: {data.get('message')}")
            ipcheck = data.get('data', {}).get('ipcheck', True)
            print(f"  ipcheck: {ipcheck}")

            if not ipcheck:
                print("  => IP 차단 지속됨!")
            elif data.get('data', {}).get('dma_csBasInf') is not None:
                print(f"\n  *** 사건 정보 발견! ***")
                print(json.dumps(data['data']['dma_csBasInf'], indent=2, ensure_ascii=False))
            else:
                print(f"  => 사건번호 없음 (조회 결과 없음)")
                print(f"  data keys: {list(data.get('data', {}).keys())}")
        except:
            print(f"  응답: {direct_result['body'][:300]}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
