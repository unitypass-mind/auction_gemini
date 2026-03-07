# -*- coding: utf-8 -*-
"""
법원 경매 사이트 API 분석
DevTools에서 발견한 엔드포인트 테스트
"""

import requests
import json

class CourtAuctionAPI:
    """법원 경매 API 테스트"""

    def __init__(self):
        self.base_url = "https://www.courtauction.go.kr"
        self.session = requests.Session()

        # 실제 브라우저처럼 보이도록 헤더 설정
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-Requested-With': 'XMLHttpRequest',  # AJAX 요청 표시
            'Referer': 'https://www.courtauction.go.kr/',
            'Origin': 'https://www.courtauction.go.kr'
        })

    def test_endpoint(self, endpoint, method="GET", params=None, data=None):
        """
        API 엔드포인트 테스트

        Args:
            endpoint: API 엔드포인트 (예: "/selectAuctnCsrchRslt.on")
            method: HTTP 메서드 (GET 또는 POST)
            params: URL 파라미터 (GET)
            data: POST 데이터
        """
        url = f"{self.base_url}{endpoint}"

        print(f"\n{'='*80}")
        print(f"테스트: {method} {endpoint}")
        print(f"URL: {url}")
        print("-" * 80)

        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=30)
            else:
                response = self.session.post(url, data=data, timeout=30)

            print(f"Status Code: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"Content-Length: {len(response.text)}")

            # JSON 응답인지 확인
            if 'application/json' in response.headers.get('Content-Type', ''):
                try:
                    json_data = response.json()
                    print(f"\n✓ JSON 응답 성공!")
                    print(f"응답 구조: {json.dumps(json_data, indent=2, ensure_ascii=False)[:500]}...")
                    return json_data
                except:
                    print(f"JSON 파싱 실패")
            else:
                # HTML/XML 응답
                print(f"\n응답 미리보기:")
                print(response.text[:500])

            return response.text

        except Exception as e:
            print(f"오류: {e}")
            return None

    def search_by_case_number(self, case_no="2024타경579705"):
        """
        사건번호로 검색 시도
        DevTools에서 발견한 엔드포인트 기반
        """
        print("=" * 80)
        print(f"법원 경매 사이트 API 검색 테스트: {case_no}")
        print("=" * 80)

        # DevTools에서 발견한 것으로 보이는 엔드포인트들
        endpoints_to_test = [
            {
                "name": "경매사건검색 결과",
                "endpoint": "/selectAuctnCsrchRslt.on",
                "method": "POST",
                "data": {
                    "saNo": case_no,  # 사건번호
                    "page": "1"
                }
            },
            {
                "name": "법원사무소 목록",
                "endpoint": "/selectCortOfcList.on",
                "method": "POST",
                "data": {}
            },
            {
                "name": "물건 상세 조회",
                "endpoint": "/RetrieveRealEstInfo.laf",
                "method": "POST",
                "data": {
                    "saNo": case_no
                }
            },
            {
                "name": "사건 기본 내역",
                "endpoint": "/InitMulSrch.laf",
                "method": "GET",
                "params": {
                    "saNo": case_no
                }
            },
            {
                "name": "경매 물건 목록",
                "endpoint": "/CaseList.laf",
                "method": "POST",
                "data": {
                    "saNo": case_no
                }
            },
        ]

        results = {}

        for test_case in endpoints_to_test:
            print(f"\n\n[{test_case['name']}]")

            result = self.test_endpoint(
                endpoint=test_case['endpoint'],
                method=test_case['method'],
                params=test_case.get('params'),
                data=test_case.get('data')
            )

            results[test_case['name']] = result

        return results

    def extract_case_details(self, case_no="2024타경579705"):
        """
        사건번호로 상세 정보 추출 시도
        """
        print(f"\n\n{'='*80}")
        print(f"상세 정보 추출 시도: {case_no}")
        print("=" * 80)

        # 다양한 파라미터 형식 시도
        param_formats = [
            {"saNo": case_no},
            {"saNo": case_no.replace("타경", "")},  # 숫자만
            {"caseNo": case_no},
            {"itemNo": case_no},
            {"searchWord": case_no},
            {"srnID": case_no},
        ]

        for params in param_formats:
            print(f"\n파라미터: {params}")
            self.test_endpoint(
                endpoint="/RetrieveRealEstInfo.laf",
                method="POST",
                data=params
            )


def main():
    """메인 실행"""
    api = CourtAuctionAPI()

    # 테스트 1: 알려진 사건번호로 검색
    print("\n" * 2)
    print("=" * 80)
    print("법원 경매 사이트 API 크롤링 가능성 분석")
    print("=" * 80)
    print("\nDevTools에서 발견한 엔드포인트를 기반으로 테스트합니다.")
    print("\n")

    results = api.search_by_case_number("2024타경579705")

    # 테스트 2: 다양한 파라미터 형식 시도
    api.extract_case_details("2024타경579705")

    # 결과 요약
    print("\n\n" + "=" * 80)
    print("테스트 결과 요약")
    print("=" * 80)

    success_count = sum(1 for r in results.values() if r is not None)
    total_count = len(results)

    print(f"\n성공한 엔드포인트: {success_count}/{total_count}")

    if success_count > 0:
        print("\n✓ 법원 경매 사이트 크롤링 가능!")
        print("  → JSON API가 발견되었습니다.")
        print("  → 자동 데이터 수집이 가능합니다.")
    else:
        print("\n✗ 추가 분석 필요")
        print("  → DevTools에서 실제 요청 URL과 파라미터를 확인해주세요.")
        print("  → Network 탭에서 'selectAuctnCsrchRslt.on' 요청을 찾아")
        print("    Headers → Request Payload를 복사해주세요.")

    print("\n" + "=" * 80)
    print("다음 단계")
    print("=" * 80)
    print("""
DevTools에서 확인이 필요한 정보:

1. Network 탭에서 'selectAuctnCsrchRslt.on' 요청 클릭
2. Headers 탭 → Request Headers 전체 복사
3. Payload 탭 → Form Data 또는 Request Payload 복사
4. Response 탭 → 응답 JSON 구조 확인

위 정보를 제공해주시면 정확한 크롤링 스크립트를 작성할 수 있습니다.
    """)


if __name__ == "__main__":
    main()
