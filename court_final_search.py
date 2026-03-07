# -*- coding: utf-8 -*-
"""
법원 경매사건검색 - 최종 버전
발견된 정확한 selector 사용:
- 번호 입력: #mf_wfm_mainFrame_ibx_auctnCsSrchCsNo
- 검색 버튼: #mf_wfm_mainFrame_btn_auctnCsSrchBtn
- 탭 클릭 후 동적 로드 대기 필요
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

search_results = []

async def run():
    async with async_playwright() as p:
        print("=" * 70)
        print("법원 경매사건검색 - 최종 자동화")
        print(f"목표: {TARGET_CASE}")
        print("=" * 70)

        browser = await p.chromium.launch(headless=True, args=['--lang=ko-KR'])
        context = await browser.new_context(locale='ko-KR')
        page = await context.new_page()

        # 모든 JSON API 캡처
        async def on_response(response):
            url = response.url
            if 'courtauction.go.kr' in url and '.on' in url:
                try:
                    body = await response.text()
                    if body.strip().startswith('{') or body.strip().startswith('['):
                        path = url.replace(BASE_URL, '')
                        post_data = ""
                        try:
                            post_data = response.request.post_data or ""
                        except:
                            pass
                        search_results.append({
                            'path': path,
                            'post_data': post_data,
                            'body': body
                        })
                        if '579705' in body:
                            print(f"\n[*** 목표 발견! ***] {path}")
                            print(f"응답: {body[:600]}")
                except:
                    pass

        page.on('response', on_response)

        # 1. 메인 페이지 방문
        print("\n[1] 메인 페이지 방문")
        await page.goto(f"{BASE_URL}/pgj/index.on", wait_until='networkidle', timeout=30000)
        await asyncio.sleep(2)

        # 2. 경매사건검색 탭 클릭 (정확한 링크 텍스트 사용)
        print("\n[2] 경매사건검색 탭 클릭")
        try:
            # 정확히 '경매사건검색' 링크 찾아 클릭
            result = await page.evaluate("""
                () => {
                    const links = document.querySelectorAll('a');
                    let found = null;
                    for (const link of links) {
                        const text = link.textContent.trim();
                        if (text === '경매사건검색') {
                            link.click();
                            found = link.href || link.getAttribute('onclick') || 'clicked';
                            break;
                        }
                    }
                    return found;
                }
            """)
            print(f"  탭 클릭: {result}")
            await asyncio.sleep(4)  # 동적 로드 대기

        except Exception as e:
            print(f"  탭 클릭 오류: {e}")

        # 3. 입력 필드 대기 (동적 로드)
        print("\n[3] 입력 필드 로드 대기")
        try:
            # 검색 폼이 DOM에 나타날 때까지 대기
            await page.wait_for_selector(
                '#mf_wfm_mainFrame_ibx_auctnCsSrchCsNo',
                state='visible',
                timeout=10000
            )
            print("  입력 필드 로드 완료!")
        except Exception as e:
            print(f"  대기 실패 ({e}). 현재 입력 필드 상태 확인...")
            # 현재 상태에서 유사한 ID 찾기
            found_ids = await page.evaluate("""
                () => {
                    const all = document.querySelectorAll('[id*="auctnCs"]');
                    return Array.from(all).map(el => ({
                        id: el.id,
                        tag: el.tagName,
                        visible: el.offsetParent !== null
                    }));
                }
            """)
            print(f"  'auctnCs' 포함 요소: {found_ids}")

        # 4. 법원 선택
        print(f"\n[4] 법원 선택 (인천지방법원 {TARGET_COURT_CODE})")
        try:
            court_select = page.locator('#mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc')
            await court_select.wait_for(state='visible', timeout=5000)
            await court_select.select_option(TARGET_COURT_CODE)
            await asyncio.sleep(0.5)
            print("  완료!")
        except Exception as e:
            print(f"  법원 선택 오류: {e}")
            # 대안: JavaScript로 직접 선택
            try:
                await page.evaluate(f"""
                    () => {{
                        const sel = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCortOfc');
                        if (sel) {{
                            sel.value = '{TARGET_COURT_CODE}';
                            sel.dispatchEvent(new Event('change'));
                        }}
                    }}
                """)
                print("  JavaScript로 선택 완료!")
            except Exception as e2:
                print(f"  JS 선택도 실패: {e2}")

        # 5. 연도 선택
        print(f"\n[5] 연도 선택 ({TARGET_YEAR})")
        try:
            year_select = page.locator('#mf_wfm_mainFrame_sbx_auctnCsSrchCsYear')
            await year_select.wait_for(state='visible', timeout=5000)
            await year_select.select_option(TARGET_YEAR)
            await asyncio.sleep(0.5)
            print("  완료!")
        except Exception as e:
            print(f"  연도 선택 오류: {e}")
            try:
                await page.evaluate(f"""
                    () => {{
                        const sel = document.getElementById('mf_wfm_mainFrame_sbx_auctnCsSrchCsYear');
                        if (sel) {{
                            sel.value = '{TARGET_YEAR}';
                            sel.dispatchEvent(new Event('change'));
                        }}
                    }}
                """)
                print("  JavaScript로 선택 완료!")
            except:
                pass

        # 6. 번호 입력
        print(f"\n[6] 번호 입력 ({TARGET_NUMBER})")
        try:
            no_input = page.locator('#mf_wfm_mainFrame_ibx_auctnCsSrchCsNo')
            await no_input.wait_for(state='visible', timeout=5000)
            await no_input.clear()
            await no_input.fill(TARGET_NUMBER)
            await asyncio.sleep(0.5)
            val = await no_input.input_value()
            print(f"  입력된 값: {val}")
        except Exception as e:
            print(f"  번호 입력 오류: {e}")
            try:
                await page.evaluate(f"""
                    () => {{
                        const inp = document.getElementById('mf_wfm_mainFrame_ibx_auctnCsSrchCsNo');
                        if (inp) {{
                            inp.value = '{TARGET_NUMBER}';
                            inp.dispatchEvent(new Event('input'));
                        }}
                    }}
                """)
                print("  JavaScript로 입력 완료!")
            except:
                pass

        # 7. 검색 버튼 클릭
        print("\n[7] 검색 버튼 클릭")
        prev_count = len(search_results)
        try:
            btn = page.locator('#mf_wfm_mainFrame_btn_auctnCsSrchBtn')
            await btn.wait_for(state='visible', timeout=5000)
            await btn.click()
            print("  클릭 완료!")
        except Exception as e:
            print(f"  버튼 클릭 오류: {e}")
            try:
                await page.evaluate("""
                    () => {
                        const btn = document.getElementById('mf_wfm_mainFrame_btn_auctnCsSrchBtn');
                        if (btn) {
                            btn.click();
                            return '클릭됨';
                        }
                        return '버튼 없음';
                    }
                """)
                print("  JavaScript로 클릭!")
            except:
                pass

        # 검색 결과 대기
        await page.wait_for_load_state('networkidle', timeout=15000)
        await asyncio.sleep(3)

        # 8. 결과 분석
        new_results = search_results[prev_count:]
        print(f"\n[8] 검색 후 캡처된 API: {len(new_results)}개")

        for r in new_results:
            print(f"\n  경로: {r['path']}")
            print(f"  요청: {r['post_data'][:200]}")
            try:
                data = json.loads(r['body'])
                print(f"  Status: {data.get('status')}, Message: {data.get('message')}")
                if data.get('data'):
                    print(f"  Data keys: {list(data['data'].keys()) if isinstance(data['data'], dict) else str(type(data['data']))}")
                    print(f"  Data: {json.dumps(data['data'], ensure_ascii=False)[:400]}")
            except:
                print(f"  응답: {r['body'][:300]}")

        # 9. 페이지 텍스트 확인
        print("\n[9] 페이지 결과 확인")
        page_text = await page.inner_text('body')
        if '579705' in page_text:
            idx = page_text.find('579705')
            print(f"  *** 사건번호 발견! ***")
            print(f"  주변 텍스트: {page_text[max(0,idx-100):idx+300]}")
        else:
            print("  사건번호 미발견")
            await page.screenshot(path='court_final_result.png')
            print("  스크린샷 -> court_final_result.png")

        await browser.close()

        # 최종 요약
        print(f"\n\n{'='*70}")
        print("전체 캡처 결과")
        print("=" * 70)
        print(f"총 JSON API 캡처: {len(search_results)}개")

        unique_paths = set(r['path'] for r in search_results)
        for path in sorted(unique_paths):
            r = next(x for x in search_results if x['path'] == path)
            print(f"\n{path}")
            try:
                data = json.loads(r['body'])
                print(f"  Status: {data.get('status')}, Message: {data.get('message', '')[:60]}")
            except:
                print(f"  {r['body'][:100]}")


if __name__ == "__main__":
    asyncio.run(run())
