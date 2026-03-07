# -*- coding: utf-8 -*-
"""
법원 경매 사이트 크롤링 가능성 검토
대법원 경매정보: https://www.courtauction.go.kr
"""

import requests
from bs4 import BeautifulSoup
import json

class CourtAuctionCrawler:
    """법원 경매 사이트 크롤러 테스트"""

    def __init__(self):
        self.base_url = "https://www.courtauction.go.kr"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        })

    def test_main_page(self):
        """메인 페이지 접근 테스트"""
        print("=" * 80)
        print("[테스트 1] 메인 페이지 접근")
        print("=" * 80)

        try:
            response = self.session.get(self.base_url, timeout=10)
            print(f"Status Code: {response.status_code}")
            print(f"URL (리다이렉트 후): {response.url}")
            print(f"Content-Length: {len(response.text)}")

            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title')
            print(f"페이지 제목: {title.string if title else 'N/A'}")

            # 검색 폼 찾기
            forms = soup.find_all('form')
            print(f"\nForm 개수: {len(forms)}")

            if forms:
                print("\n주요 Form 정보:")
                for idx, form in enumerate(forms[:3], 1):
                    print(f"  Form {idx}:")
                    print(f"    action: {form.get('action', 'N/A')}")
                    print(f"    method: {form.get('method', 'N/A')}")

                    inputs = form.find_all('input')
                    print(f"    input 필드 수: {len(inputs)}")

                    for inp in inputs[:5]:
                        print(f"      - {inp.get('name', 'N/A')}: {inp.get('type', 'text')}")

            return True

        except Exception as e:
            print(f"오류: {e}")
            return False

    def test_search_by_case_no(self, case_no="2024타경579705"):
        """사건번호로 검색 테스트"""
        print("\n" + "=" * 80)
        print(f"[테스트 2] 사건번호 검색: {case_no}")
        print("=" * 80)

        # 일반적인 법원 경매 검색 엔드포인트 시도
        search_endpoints = [
            "/RetrieveRealEstInfo.laf",
            "/InitMulSrch.laf",
            "/CaseList.laf",
            "/srch/srch.jsp",
        ]

        for endpoint in search_endpoints:
            url = f"{self.base_url}{endpoint}"
            print(f"\n시도 중: {url}")

            try:
                # GET 시도
                response = self.session.get(url, params={'saNo': case_no}, timeout=10)
                print(f"  GET - Status: {response.status_code}")

                if response.status_code == 200:
                    print(f"  성공! URL: {response.url}")
                    print(f"  Content-Length: {len(response.text)}")

                    # 간단한 데이터 확인
                    if case_no in response.text or "감정가" in response.text:
                        print("  → 관련 데이터 발견 가능성 있음")
                        return True

                # POST 시도
                response = self.session.post(url, data={'saNo': case_no}, timeout=10)
                print(f"  POST - Status: {response.status_code}")

                if response.status_code == 200 and len(response.text) > 1000:
                    print(f"  성공! 데이터 길이: {len(response.text)}")

            except Exception as e:
                print(f"  오류: {e}")

        return False

    def check_robots_txt(self):
        """robots.txt 확인"""
        print("\n" + "=" * 80)
        print("[테스트 3] robots.txt 확인")
        print("=" * 80)

        try:
            response = self.session.get(f"{self.base_url}/robots.txt", timeout=10)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                print("\nrobots.txt 내용:")
                print("-" * 80)
                print(response.text[:500])
                print("-" * 80)
            else:
                print("robots.txt 없음 (크롤링 제한 없을 가능성)")

        except Exception as e:
            print(f"오류: {e}")

    def analyze_page_structure(self):
        """페이지 구조 분석"""
        print("\n" + "=" * 80)
        print("[테스트 4] 페이지 구조 분석")
        print("=" * 80)

        try:
            # 메인 페이지 가져오기
            response = self.session.get(self.base_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # JavaScript 파일 찾기
            scripts = soup.find_all('script', src=True)
            print(f"\n외부 JavaScript 파일 수: {len(scripts)}")

            # iframe 찾기
            iframes = soup.find_all('iframe')
            print(f"iframe 수: {len(iframes)}")

            if iframes:
                print("iframe src:")
                for iframe in iframes[:3]:
                    print(f"  - {iframe.get('src', 'N/A')}")

            # 링크 분석
            links = soup.find_all('a', href=True)
            auction_links = [link for link in links if 'auction' in link.get('href', '').lower() or
                             'search' in link.get('href', '').lower() or
                             'retrieve' in link.get('href', '').lower()]

            print(f"\n경매 관련 링크 수: {len(auction_links)}")
            if auction_links:
                print("주요 링크:")
                for link in auction_links[:5]:
                    print(f"  - {link.get('href')} : {link.text.strip()[:30]}")

        except Exception as e:
            print(f"오류: {e}")


def main():
    """메인 실행"""
    print("\n")
    print("=" * 80)
    print("법원 경매 사이트 크롤링 가능성 검토")
    print("=" * 80)
    print("\n대법원 경매정보: https://www.courtauction.go.kr")
    print("\n이 스크립트는 다음을 테스트합니다:")
    print("1. 메인 페이지 접근 가능성")
    print("2. 사건번호 검색 엔드포인트 탐색")
    print("3. robots.txt 크롤링 정책")
    print("4. 페이지 구조 (JavaScript, iframe 등)")
    print("\n")

    crawler = CourtAuctionCrawler()

    # 테스트 실행
    crawler.test_main_page()
    crawler.check_robots_txt()
    crawler.analyze_page_structure()
    crawler.test_search_by_case_no("2024타경579705")

    print("\n" + "=" * 80)
    print("검토 결과 요약")
    print("=" * 80)
    print("""
[결론]

법원 경매 사이트 크롤링은 **기술적으로 가능**하지만:

✓ 가능한 점:
  - 공개된 정부 사이트 (법적 문제 적음)
  - HTML 기반 데이터 제공
  - robots.txt 제한 가능성 낮음

✗ 어려운 점:
  - 복잡한 세션 관리
  - JavaScript 동적 로딩
  - 불분명한 API 엔드포인트
  - 예측 불가능한 HTML 구조
  - 서버 부하 시 차단 가능성

권장 사항:
1. ValueAuction API 우선 사용 (안정적)
2. 법원 사이트는 보조 수단
3. Selenium 등 브라우저 자동화 도구 필요할 수 있음
4. 캐싱 및 요청 제한 (서버 부담 최소화)
    """)


if __name__ == "__main__":
    main()
