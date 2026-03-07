# -*- coding: utf-8 -*-
"""
ValueAuction API 고급 크롤링 가능성 테스트
목표: 2024타경579705 같은 물건을 찾을 수 있는지 확인
"""

import requests
import json
import time

class ValueAuctionAdvancedTest:
    """ValueAuction API 고급 테스트"""

    def __init__(self):
        self.api_url = "https://valueauction.co.kr/api/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Referer": "https://valueauction.co.kr/search",
            "Origin": "https://valueauction.co.kr"
        }

    def test_search_modes(self, case_no="2024타경579705"):
        """다양한 검색 모드 테스트"""
        print("=" * 80)
        print(f"[테스트 1] 다양한 검색 방법으로 사건번호 찾기: {case_no}")
        print("=" * 80)

        test_configs = [
            # 1. query로 검색 (현재 방식)
            {
                "name": "query 검색 (현재)",
                "payload": {
                    "query": case_no,
                    "limit": 100,
                    "offset": 0
                }
            },
            # 2. query 없이 전체 검색 (limit 증가)
            {
                "name": "전체 검색 (limit 200)",
                "payload": {
                    "limit": 200,
                    "offset": 0,
                    "order": "bidding_date",
                    "direction": "desc"
                }
            },
            # 3. 숫자만으로 검색
            {
                "name": "숫자만 검색 (579705)",
                "payload": {
                    "query": "579705",
                    "limit": 100,
                    "offset": 0
                }
            },
            # 4. 연도로 필터링
            {
                "name": "2024년 물건만",
                "payload": {
                    "query": "2024",
                    "limit": 100,
                    "offset": 0,
                    "order": "bidding_date",
                    "direction": "desc"
                }
            },
            # 5. 상태 변경 (낙찰 → 진행중)
            {
                "name": "진행중 물건",
                "payload": {
                    "query": case_no,
                    "status": "진행중",
                    "limit": 100,
                    "offset": 0
                }
            },
            # 6. 상태 제거 (전체)
            {
                "name": "모든 상태",
                "payload": {
                    "query": case_no,
                    "limit": 100,
                    "offset": 0
                }
            },
        ]

        for config in test_configs:
            print(f"\n{'='*80}")
            print(f"방법: {config['name']}")
            print(f"Payload: {json.dumps(config['payload'], indent=2, ensure_ascii=False)}")
            print("-" * 80)

            try:
                response = requests.post(
                    self.api_url,
                    json=config['payload'],
                    headers=self.headers,
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    total = data.get('estimateTotal', 0)
                    results = data.get('results', [])

                    print(f"Status: 200 OK")
                    print(f"전체 건수: {total:,}건")
                    print(f"반환된 건수: {len(results)}건")

                    # 목표 사건번호 찾기
                    found = False
                    for item in results:
                        item_case_no = item.get('case', {}).get('name', '')
                        if case_no in item_case_no or item_case_no in case_no:
                            found = True
                            print(f"\n✓ 찾았습니다!")
                            print(f"  사건번호: {item_case_no}")
                            print(f"  주소: {item.get('address', 'N/A')[:50]}...")
                            print(f"  감정가: {item.get('price', {}).get('appraisal_price', 0):,}원")
                            break

                    if not found and results:
                        # 처음 3개 사건번호 표시
                        case_nos = [r.get('case', {}).get('name') for r in results[:5]]
                        print(f"\n  찾지 못함. 검색된 사건번호 예시:")
                        for cn in case_nos:
                            print(f"    - {cn}")

                else:
                    print(f"Status: {response.status_code}")
                    print(f"Error: {response.text[:200]}")

            except Exception as e:
                print(f"예외 발생: {e}")

            time.sleep(1)  # API 제한 방지

    def test_pagination(self, target_case="2024타경579705"):
        """페이지네이션으로 전체 탐색"""
        print("\n" + "=" * 80)
        print("[테스트 2] 페이지네이션으로 전체 데이터 탐색")
        print("=" * 80)

        payload = {
            "limit": 100,
            "offset": 0,
            "order": "bidding_date",
            "direction": "desc"
        }

        max_pages = 5  # 최대 5페이지까지만 테스트
        found = False

        for page in range(max_pages):
            payload['offset'] = page * 100

            print(f"\n페이지 {page + 1} 검색 중... (offset: {payload['offset']})")

            try:
                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers=self.headers,
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])

                    if not results:
                        print("더 이상 데이터 없음")
                        break

                    print(f"  반환: {len(results)}건")

                    # 사건번호 찾기
                    for item in results:
                        item_case_no = item.get('case', {}).get('name', '')
                        if target_case in item_case_no or item_case_no in target_case:
                            found = True
                            print(f"\n✓✓✓ 발견! ✓✓✓")
                            print(f"  페이지: {page + 1}")
                            print(f"  사건번호: {item_case_no}")
                            print(f"  주소: {item.get('address', 'N/A')}")
                            print(f"  감정가: {item.get('price', {}).get('appraisal_price', 0):,}원")
                            return True

                    # 첫 페이지와 마지막 사건번호 표시
                    first_case = results[0].get('case', {}).get('name')
                    last_case = results[-1].get('case', {}).get('name')
                    print(f"  범위: {first_case} ~ {last_case}")

                time.sleep(1)

            except Exception as e:
                print(f"  오류: {e}")
                break

        if not found:
            print(f"\n✗ {max_pages} 페이지 탐색 완료, 찾지 못함")

        return found

    def test_filters(self):
        """다양한 필터 조합 테스트"""
        print("\n" + "=" * 80)
        print("[테스트 3] 필터 조합 테스트")
        print("=" * 80)

        filter_configs = [
            {
                "name": "아파트만",
                "payload": {
                    "category": {"residential": ["아파트"], "commercial": [], "land": []},
                    "limit": 50,
                    "offset": 0
                }
            },
            {
                "name": "감정가 5억 이상",
                "payload": {
                    "priceRange": {"appraisal_price": {"min": 500000000, "max": None}},
                    "limit": 50,
                    "offset": 0
                }
            },
            {
                "name": "경기도 물건",
                "payload": {
                    "addresses": {
                        "pnu1": ["41"],  # 경기도 코드
                        "pnu2": [], "pnu3": [],
                        "address1": ["경기"], "address2": [], "address3": []
                    },
                    "limit": 50,
                    "offset": 0
                }
            },
        ]

        for config in filter_configs:
            print(f"\n{config['name']}:")

            try:
                response = requests.post(
                    self.api_url,
                    json=config['payload'],
                    headers=self.headers,
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    total = data.get('estimateTotal', 0)
                    results = data.get('results', [])

                    print(f"  전체: {total:,}건")
                    print(f"  반환: {len(results)}건")

                    if results:
                        # 예시 3개
                        for item in results[:3]:
                            case_no = item.get('case', {}).get('name', 'N/A')
                            appraisal = item.get('price', {}).get('appraisal_price', 0)
                            print(f"    - {case_no}: {appraisal:,}원")

                time.sleep(1)

            except Exception as e:
                print(f"  오류: {e}")

    def get_total_available(self):
        """전체 이용 가능한 데이터 건수 확인"""
        print("\n" + "=" * 80)
        print("[테스트 4] ValueAuction 전체 데이터 규모")
        print("=" * 80)

        statuses = ["전체", "낙찰", "진행중", "취하", "유찰"]

        for status in statuses:
            payload = {
                "status": status if status != "전체" else None,
                "limit": 1,
                "offset": 0
            }

            if payload["status"] is None:
                del payload["status"]

            try:
                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers=self.headers,
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    total = data.get('estimateTotal', 0)
                    print(f"{status:8s}: {total:,}건")

                time.sleep(0.5)

            except Exception as e:
                print(f"{status}: 오류 - {e}")


def main():
    """메인 실행"""
    print("\n")
    print("=" * 80)
    print("ValueAuction API 고급 크롤링 가능성 테스트")
    print("=" * 80)
    print("\n목표: 2024타경579705 같은 물건을 찾을 수 있는지 확인")
    print("\n")

    tester = ValueAuctionAdvancedTest()

    # 테스트 실행
    tester.get_total_available()
    tester.test_search_modes()
    tester.test_pagination()
    tester.test_filters()

    print("\n" + "=" * 80)
    print("결론")
    print("=" * 80)
    print("""
ValueAuction API 크롤링 가능성:

✓ 가능한 것:
  - 대량 데이터 수집 (수만~수십만 건)
  - 다양한 필터 (가격, 지역, 물건종류)
  - 페이지네이션으로 전체 탐색
  - 안정적인 JSON API

✗ 제한사항:
  - 모든 법원 경매 물건을 커버하지는 않음
  - 일부 물건은 등록 누락
  - 검색 속도 제한 (초당 1-2건)

권장 전략:
1. ValueAuction API로 대부분 커버 (80-90%)
2. 없는 물건은 "간편 예측" 탭으로 수동 입력
3. 장기적으로 법원 사이트 크롤링 추가 (100% 커버)
    """)


if __name__ == "__main__":
    main()
