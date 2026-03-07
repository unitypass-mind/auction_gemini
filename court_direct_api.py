# -*- coding: utf-8 -*-
"""
법원 경매 - 발견된 API 직접 호출
API: /pgj/pgj15A/selectAuctnCsSrchRslt.on
요청: {"dma_srchCsDtlInf":{"cortOfcCd":"B000240","csNo":"2024타경579705"}}
"""

import asyncio
import json
import sys
import io
from playwright.async_api import async_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TARGET_CASE = "2024타경579705"
TARGET_COURT_CODE = "B000240"  # 인천지방법원

BASE_URL = "https://www.courtauction.go.kr"
API_PATH = "/pgj/pgj15A/selectAuctnCsSrchRslt.on"

async def run():
    async with async_playwright() as p:
        print("=" * 70)
        print("법원 경매 API 직접 호출")
        print(f"목표: {TARGET_CASE} (인천지방법원 {TARGET_COURT_CODE})")
        print(f"API: {API_PATH}")
        print("=" * 70)

        browser = await p.chromium.launch(headless=True, args=['--lang=ko-KR'])
        context = await browser.new_context(locale='ko-KR')
        page = await context.new_page()

        # 세션 초기화
        print("\n[1] 세션 초기화")
        await page.goto(f"{BASE_URL}/pgj/index.on", wait_until='networkidle', timeout=30000)
        await asyncio.sleep(2)

        # Playwright fetch로 API 직접 호출 (세션/쿠키 자동 포함)
        print("\n[2] API 직접 호출")

        payload = {"dma_srchCsDtlInf": {"cortOfcCd": TARGET_COURT_CODE, "csNo": TARGET_CASE}}
        payload_str = json.dumps(payload, ensure_ascii=False)
        print(f"  요청: {payload_str}")

        result = await page.evaluate(f"""
            async () => {{
                const resp = await fetch('{BASE_URL}{API_PATH}', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Referer': '{BASE_URL}/pgj/index.on'
                    }},
                    body: JSON.stringify({payload_str})
                }});
                const text = await resp.text();
                return {{
                    status: resp.status,
                    contentType: resp.headers.get('content-type'),
                    body: text
                }};
            }}
        """)

        print(f"\n  응답 Status: {result['status']}")
        print(f"  Content-Type: {result['contentType']}")

        try:
            data = json.loads(result['body'])
            print(f"\n  JSON 파싱 성공!")
            print(f"  status: {data.get('status')}")
            print(f"  message: {data.get('message')}")

            if data.get('data'):
                d = data['data']
                print(f"\n  데이터 구조:")
                for key, val in d.items():
                    if val is not None:
                        print(f"    {key}: {json.dumps(val, ensure_ascii=False)[:200]}")

                # 핵심 데이터 추출
                cs_bas_inf = d.get('dma_csBasInf')
                if cs_bas_inf:
                    print(f"\n  *** 사건 기본 정보 ***")
                    print(json.dumps(cs_bas_inf, indent=2, ensure_ascii=False))

                dspsl_obj = d.get('dlt_dspslGdsDspslObjctLst')
                if dspsl_obj:
                    print(f"\n  *** 매각 목적물 목록 ***")
                    for item in dspsl_obj[:3]:
                        print(json.dumps(item, indent=2, ensure_ascii=False)[:300])
            else:
                print(f"\n  data: null (사건을 찾을 수 없음)")
                print(f"  전체 응답: {result['body'][:300]}")

        except json.JSONDecodeError as e:
            print(f"  JSON 파싱 실패: {e}")
            print(f"  응답: {result['body'][:500]}")

        # 3. 다른 법원 코드도 시도 (만약 인천이 아닐 경우)
        print("\n\n[3] 법원 코드 목록 조회")
        court_result = await page.evaluate("""
            async () => {
                const resp = await fetch('/pgj/pgj002/selectCortOfcLst.on', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({"cortExecrOfcDvsCd":"00079B"})
                });
                return await resp.json();
            }
        """)

        courts = court_result.get('data', {}).get('cortOfcLst', [])
        incheon_courts = [c for c in courts if '인천' in c.get('name', '') or '부천' in c.get('name', '')]
        print(f"  인천/부천 관련 법원:")
        for c in incheon_courts:
            print(f"    {c['code']} - {c['name']}")

        # 4. 인천 관련 법원 코드로 순차 검색
        print(f"\n\n[4] 인천 법원 코드로 검색 시도")
        for court in incheon_courts:
            court_code = court['code']
            court_name = court['name']
            payload2 = {"dma_srchCsDtlInf": {"cortOfcCd": court_code, "csNo": TARGET_CASE}}

            result2 = await page.evaluate(f"""
                async () => {{
                    const resp = await fetch('{BASE_URL}{API_PATH}', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}},
                        body: JSON.stringify({json.dumps(payload2, ensure_ascii=False)})
                    }});
                    return {{status: resp.status, body: await resp.text()}};
                }}
            """)

            try:
                data2 = json.loads(result2['body'])
                msg = data2.get('message', '')
                cs_inf = data2.get('data', {})
                has_data = cs_inf and cs_inf.get('dma_csBasInf') is not None

                print(f"\n  {court_code} ({court_name}): Status={result2['status']}, Message={msg[:50]}")
                if has_data:
                    print(f"  *** 데이터 있음! ***")
                    print(f"  사건기본정보: {json.dumps(cs_inf.get('dma_csBasInf'), ensure_ascii=False)[:400]}")
                    break

            except:
                print(f"  {court_code} ({court_name}): 파싱 오류")

        await browser.close()

async def get_court_auction_info(case_no: str) -> dict:
    """
    법원 경매 사이트에서 사건 정보 조회
    실제 서비스에 통합하기 위한 함수
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # 세션 초기화
        await page.goto("https://www.courtauction.go.kr/pgj/index.on",
                       wait_until='networkidle', timeout=30000)
        await asyncio.sleep(2)

        # 법원 목록 조회
        courts = await page.evaluate("""
            async () => {
                const resp = await fetch('/pgj/pgj002/selectCortOfcLst.on', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({"cortExecrOfcDvsCd":"00079B"})
                });
                const data = await resp.json();
                return data.data?.cortOfcLst || [];
            }
        """)

        # 모든 법원에서 검색
        for court in courts:
            payload = {"dma_srchCsDtlInf": {"cortOfcCd": court['code'], "csNo": case_no}}
            result = await page.evaluate(f"""
                async () => {{
                    const resp = await fetch('/pgj/pgj15A/selectAuctnCsSrchRslt.on', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({json.dumps(payload, ensure_ascii=False)})
                    }});
                    return await resp.json();
                }}
            """)

            if result.get('data', {}).get('dma_csBasInf'):
                await browser.close()
                return result['data']

        await browser.close()
        return {}


if __name__ == "__main__":
    asyncio.run(run())
