# -*- coding: utf-8 -*-
"""
법원 경매 - 경매사건검색 폼 자동화
발견된 selector:
- 법원: #mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc
- 연도: #mf_wfm_mainFrame_sbx_auctnCsSrchCsYear
- 번호: #mf_wfm_mainFrame_ibx_auctnCsSrchCsNo (maxlength=7)
- 검색: #mf_wfm_mainFrame_btn_auctnCsSrchBtn
"""

import asyncio
import json
import sys
import io
from playwright.async_api import async_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 인천지방법원 코드 (DevTools에서 확인: B000240)
TARGET_CASE = "2024타경579705"
TARGET_YEAR = "2024"
TARGET_NUMBER = "579705"  # maxlength=7
TARGET_COURT_CODE = "B000240"  # 인천지방법원

BASE_URL = "https://www.courtauction.go.kr"
captured_search_results = []

async def run():
    async with async_playwright() as p:
        print("=" * 70)
        print("법원 경매사건검색 - 자동화 검색")
        print(f"목표: {TARGET_CASE}")
        print("=" * 70)

        browser = await p.chromium.launch(headless=True, args=['--lang=ko-KR'])
        context = await browser.new_context(
            locale='ko-KR',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        # 검색 결과 API 캡처
        async def on_response(response):
            url = response.url
            if 'courtauction.go.kr' in url and ('.on' in url or '.json' in url):
                try:
                    body = await response.text()
                    ctype = response.headers.get('content-type', '')
                    is_json = body.strip().startswith('{') or body.strip().startswith('[') or 'json' in ctype
                    if is_json and len(body) > 50:
                        path = url.replace(BASE_URL, '')
                        post_data = ""
                        try:
                            post_data = response.request.post_data or ""
                        except:
                            pass
                        captured_search_results.append({
                            'path': path,
                            'post_data': post_data,
                            'body': body,
                        })
                except:
                    pass

        page.on('response', on_response)

        # 1. 메인 페이지 방문
        print("\n[1] 메인 페이지 방문")
        await page.goto(f"{BASE_URL}/pgj/index.on", wait_until='networkidle', timeout=30000)
        await asyncio.sleep(2)

        # 2. 경매사건검색 탭 클릭
        print("\n[2] 경매사건검색 탭 클릭")
        try:
            await page.get_by_text("경매사건검색", exact=True).click()
            await asyncio.sleep(2)
            print("  탭 클릭 성공!")
        except Exception as e:
            print(f"  탭 클릭 실패: {e}")

        # 3. 법원 선택
        print(f"\n[3] 법원 선택: 인천지방법원 ({TARGET_COURT_CODE})")
        try:
            # SELECT 박스 옵션 확인
            court_options = await page.evaluate("""
                () => {
                    const sel = document.querySelector('#mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc');
                    if (!sel) return [];
                    return Array.from(sel.options || []).map(o => ({
                        value: o.value,
                        text: o.text,
                        selected: o.selected
                    })).slice(0, 20);
                }
            """)
            print(f"  법원 옵션 수: {len(court_options)}")
            for opt in court_options[:10]:
                print(f"    [{opt['value']}] {opt['text']}")

            # 인천지방법원 선택
            await page.select_option('#mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc', TARGET_COURT_CODE)
            await asyncio.sleep(1)
            print(f"  인천지방법원 선택 완료")

        except Exception as e:
            print(f"  법원 선택 오류: {e}")

        # 4. 연도 선택
        print(f"\n[4] 연도 선택: {TARGET_YEAR}")
        try:
            year_options = await page.evaluate("""
                () => {
                    const sel = document.querySelector('#mf_wfm_mainFrame_sbx_auctnCsSrchCsYear');
                    if (!sel) return [];
                    return Array.from(sel.options || []).map(o => ({
                        value: o.value,
                        text: o.text
                    }));
                }
            """)
            print(f"  연도 옵션: {[o['text'] for o in year_options[:10]]}")

            await page.select_option('#mf_wfm_mainFrame_sbx_auctnCsSrchCsYear', TARGET_YEAR)
            await asyncio.sleep(0.5)
            print(f"  {TARGET_YEAR}년 선택 완료")

        except Exception as e:
            print(f"  연도 선택 오류: {e}")

        # 5. 사건번호 입력
        print(f"\n[5] 사건번호 입력: {TARGET_NUMBER}")
        try:
            case_input = page.locator('#mf_wfm_mainFrame_ibx_auctnCsSrchCsNo')
            await case_input.clear()
            await case_input.type(TARGET_NUMBER)
            await asyncio.sleep(0.5)

            current_val = await case_input.input_value()
            print(f"  입력된 값: {current_val}")

        except Exception as e:
            print(f"  번호 입력 오류: {e}")

        # 6. 검색 버튼 클릭
        print("\n[6] 검색 버튼 클릭")
        prev_count = len(captured_search_results)
        try:
            search_btn = page.locator('#mf_wfm_mainFrame_btn_auctnCsSrchBtn')
            await search_btn.click()
            print("  검색 버튼 클릭 성공!")

            # 결과 대기
            await page.wait_for_load_state('networkidle', timeout=15000)
            await asyncio.sleep(3)

        except Exception as e:
            print(f"  검색 버튼 오류: {e}")

        # 7. 검색 결과 분석
        new_results = captured_search_results[prev_count:]
        print(f"\n[7] 검색 후 캡처된 JSON API: {len(new_results)}개")

        for result in new_results:
            print(f"\n  경로: {result['path']}")
            print(f"  요청: {result['post_data'][:150]}")

            try:
                data = json.loads(result['body'])
                print(f"  응답 status: {data.get('status')}")
                print(f"  메시지: {data.get('message')}")

                # 검색 결과 분석
                if 'data' in data and data['data']:
                    result_data = data['data']
                    print(f"  데이터 키: {list(result_data.keys()) if isinstance(result_data, dict) else type(result_data).__name__}")

                    # 사건번호 찾기
                    body_str = result['body']
                    if '579705' in body_str or '2024' in body_str:
                        print(f"\n  *** 관련 데이터 발견! ***")
                        print(f"  응답: {body_str[:600]}")

            except:
                print(f"  응답: {result['body'][:300]}")

        # 8. 페이지 텍스트에서 결과 확인
        print("\n[8] 페이지에서 결과 확인")
        page_text = await page.inner_text('body')

        if '579705' in page_text:
            idx = page_text.find('579705')
            context_text = page_text[max(0, idx-100):idx+200]
            print(f"  *** 사건번호 발견! ***")
            print(f"  컨텍스트:\n{context_text}")
        elif TARGET_CASE in page_text:
            idx = page_text.find(TARGET_CASE)
            print(f"  *** 사건번호 발견! ***")
            print(f"  컨텍스트: {page_text[max(0,idx-50):idx+150]}")
        else:
            print("  사건번호 미발견")
            # 스크린샷
            await page.screenshot(path='court_case_result.png')
            print("  스크린샷 -> court_case_result.png")

            # 일부 텍스트
            result_area_text = ""
            try:
                result_area = await page.query_selector('.result, #result, [class*="result"], [class*="list"], table')
                if result_area:
                    result_area_text = await result_area.inner_text()
            except:
                pass

            if result_area_text:
                print(f"  결과 영역 텍스트: {result_area_text[:300]}")
            else:
                print(f"  페이지 텍스트 일부: {page_text[500:800]}")

        # 9. 전체 캡처 결과 요약
        print(f"\n\n{'='*70}")
        print("검색 결과 요약")
        print("=" * 70)

        all_json = captured_search_results
        print(f"총 캡처된 JSON API: {len(all_json)}개")
        print(f"검색 후 새 API: {len(new_results)}개")

        if new_results:
            print("\n검색 결과 API 전체:")
            for r in new_results:
                data_str = r['body']
                print(f"\n--- {r['path']} ---")
                print(f"요청 데이터: {r['post_data']}")
                print(f"응답 (처음 800자):\n{data_str[:800]}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(run())
