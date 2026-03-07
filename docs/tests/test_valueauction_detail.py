# -*- coding: utf-8 -*-
"""
ValueAuction API 상세 응답 분석
법원 사건번호 필드 확인
"""

import requests
import json

def get_auction_detail():
    """ValueAuction API 응답 구조 분석"""

    api_url = "https://valueauction.co.kr/api/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": "https://valueauction.co.kr/search",
        "Origin": "https://valueauction.co.kr"
    }

    payload = {
        "status": "낙찰",
        "limit": 1,  # 1개만 가져오기
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
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])

            if results:
                item = results[0]

                print("=" * 80)
                print("ValueAuction API 응답 구조 분석 (첫 번째 물건)")
                print("=" * 80)
                print("\n전체 응답 JSON:")
                print(json.dumps(item, indent=2, ensure_ascii=False))

                print("\n\n" + "=" * 80)
                print("핵심 필드 추출")
                print("=" * 80)

                # 사건 정보
                case_data = item.get('case', {})
                print(f"\n[case] 사건 정보:")
                print(json.dumps(case_data, indent=2, ensure_ascii=False))

                # auction 정보 (법원 사건번호가 여기에 있을 가능성)
                auction_data = item.get('auction', {})
                print(f"\n[auction] 경매 정보:")
                print(json.dumps(auction_data, indent=2, ensure_ascii=False))

                # badge 정보
                badge_data = item.get('badge', {})
                print(f"\n[badge] 배지 정보:")
                print(f"  category: {badge_data.get('category')}")
                print(f"  area: {badge_data.get('area')}")
                print(f"  failure_count: {badge_data.get('failure_count')}")

                # 가격 정보
                price_data = item.get('price', {})
                print(f"\n[price] 가격 정보:")
                print(f"  appraisal_price: {price_data.get('appraisal_price'):,}원")
                print(f"  selling_price: {price_data.get('selling_price'):,}원")

                # 검색: '사건', '번호', 'case_number', 'number' 등이 포함된 필드
                print("\n\n" + "=" * 80)
                print("법원 사건번호 관련 필드 검색")
                print("=" * 80)

                def search_dict(d, prefix=""):
                    """재귀적으로 딕셔너리에서 '사건', '번호', 'number', 'case' 키 찾기"""
                    for key, value in d.items():
                        full_key = f"{prefix}.{key}" if prefix else key

                        # 키에 관련 단어가 포함되어 있는지 확인
                        if any(word in key.lower() for word in ['case', 'number', '사건', '번호']):
                            print(f"  {full_key}: {value}")

                        # 중첩된 딕셔너리 탐색
                        if isinstance(value, dict):
                            search_dict(value, full_key)

                search_dict(item)

                print("\n\n" + "=" * 80)
                print("결론")
                print("=" * 80)

                if auction_data:
                    print("\n[auction] 필드에 법원 사건번호가 있을 가능성이 높습니다.")
                    print("위 JSON 출력에서 법원 사건번호 형식(예: 2024타경12345)을 찾아보세요.")
                else:
                    print("\nValueAuction API에는 법원 사건번호가 없을 수 있습니다.")
                    print("대안: 법원 경매 사이트 직접 크롤링 필요")

            else:
                print("검색 결과 없음")

        else:
            print(f"API 오류: {response.status_code}")
            print(response.text[:500])

    except Exception as e:
        print(f"예외 발생: {e}")


if __name__ == "__main__":
    get_auction_detail()
