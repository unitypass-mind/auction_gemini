"""
ValueAuction API로 사건번호 검색 테스트
실시간 경매 정보 가져오기 기능 확인
"""

import requests
import json

class ValueAuctionSearch:
    """밸류옥션 사건번호 검색 테스트"""

    def __init__(self):
        self.api_url = "https://valueauction.co.kr/api/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Referer": "https://valueauction.co.kr/search",
            "Origin": "https://valueauction.co.kr"
        }

    def search_by_case_no(self, case_no):
        """
        사건번호로 검색

        Args:
            case_no: 사건번호 (예: "2024타경12345")

        Returns:
            dict: 검색 결과
        """
        # 방법 1: 검색 쿼리 사용
        payload = {
            "query": case_no,  # 사건번호를 쿼리로 검색
            "limit": 10,
            "offset": 0,
            "order": "bidding_date",
            "direction": "desc"
        }

        try:
            print(f"\n[테스트 1] 쿼리 검색: {case_no}")
            print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=30
            )

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"응답 성공!")
                print(f"검색 결과 수: {data.get('estimateTotal', 0)}건")

                results = data.get('results', [])
                if results:
                    print(f"\n첫 번째 결과:")
                    first = results[0]
                    print(f"  사건ID: {first.get('case', {}).get('id')}")
                    print(f"  주소: {first.get('address')}")
                    print(f"  물건: {first.get('badge', {}).get('category')}")
                    print(f"  감정가: {first.get('price', {}).get('appraised_price', 0):,}원")
                    print(f"  낙찰가: {first.get('price', {}).get('selling_price', 0):,}원")
                    return data
                else:
                    print("검색 결과 없음")
                    return None
            else:
                print(f"오류: {response.status_code}")
                print(f"응답: {response.text[:500]}")
                return None

        except Exception as e:
            print(f"예외 발생: {e}")
            return None

    def search_recent_items(self, limit=5):
        """최근 물건 몇 개 가져오기 (API 연결 테스트)"""
        payload = {
            "status": "낙찰",  # 낙찰 완료 물건만
            "limit": limit,
            "offset": 0,
            "order": "bidding_date",
            "direction": "desc",
            "category": {
                "residential": ["전체"],
                "commercial": [],
                "land": []
            }
        }

        try:
            print(f"\n[테스트 2] 최근 물건 {limit}건 조회")

            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=30
            )

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"응답 성공!")
                print(f"총 물건 수: {data.get('estimateTotal', 0):,}건")

                results = data.get('results', [])
                print(f"\n최근 물건 {len(results)}건:")
                for i, item in enumerate(results, 1):
                    case_id = item.get('case', {}).get('id', 'N/A')
                    address = item.get('address', 'N/A')
                    category = item.get('badge', {}).get('category', 'N/A')
                    appraisal = item.get('price', {}).get('appraised_price', 0)

                    print(f"\n  {i}. {case_id}")
                    print(f"     주소: {address}")
                    print(f"     물건: {category}")
                    print(f"     감정가: {appraisal:,}원")

                return data
            else:
                print(f"오류: {response.status_code}")
                print(f"응답: {response.text[:500]}")
                return None

        except Exception as e:
            print(f"예외 발생: {e}")
            return None


if __name__ == "__main__":
    searcher = ValueAuctionSearch()

    print("=" * 70)
    print("ValueAuction API 사건번호 검색 테스트")
    print("=" * 70)

    # 테스트 1: API 연결 확인
    print("\n\n[1단계] API 연결 테스트 - 최근 물건 조회")
    print("-" * 70)
    recent_data = searcher.search_recent_items(limit=3)

    if recent_data and recent_data.get('results'):
        # 첫 번째 물건의 사건번호로 검색 테스트
        first_case_id = recent_data['results'][0].get('case', {}).get('id')

        print("\n\n[2단계] 사건번호 검색 테스트")
        print("-" * 70)
        print(f"테스트 사건번호: {first_case_id}")

        result = searcher.search_by_case_no(first_case_id)

        if result:
            print("\n✅ 성공! 사건번호로 검색 가능합니다.")
            print("\n다음 단계: main.py의 get_auction_item() 함수를")
            print("ValueAuction API 실시간 검색으로 교체할 수 있습니다.")
        else:
            print("\n⚠️  사건번호 검색이 작동하지 않습니다.")
            print("대안: 법원 경매 사이트 직접 크롤링 필요")
    else:
        print("\n❌ API 연결 실패")
        print("네트워크 또는 API 변경 가능성 확인 필요")

    print("\n" + "=" * 70)
