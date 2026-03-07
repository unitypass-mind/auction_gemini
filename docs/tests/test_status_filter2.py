"""
ValueAuction API - 추가 status 필터 테스트
badge, filters 등 다른 파라미터 테스트
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json

def test_advanced_filters():
    """추가 필터 파라미터 테스트"""
    url = "https://valueauction.co.kr/api/search"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": "https://valueauction.co.kr/search",
        "Origin": "https://valueauction.co.kr"
    }

    # 추가 테스트할 필터들
    filter_tests = [
        {"filters": {"sold": True}},
        {"filters": {"status": "sold"}},
        {"saleStatus": "sold"},
        {"saleStatus": "낙찰"},
        {"bidStatus": "completed"},
        {"bidStatus": "낙찰"},
        {"tags": {"mode": "include", "values": ["낙찰"]}},
        {"tags": {"mode": "include", "values": ["sold"]}},
    ]

    print("=" * 80)
    print("추가 Status 필터 테스트")
    print("=" * 80)

    for i, filter_param in enumerate(filter_tests, 1):
        print(f"\n{'=' * 80}")
        print(f"테스트 {i}: {json.dumps(filter_param, ensure_ascii=False)}")
        print("=" * 80)

        payload = {
            "limit": 10,
            "offset": 0,
            "order": "bidding_date",
            "direction": "desc",
            "category": {
                "residential": ["전체"],
                "commercial": [],
                "land": []
            },
            "priceRange": {
                "min_ask_price": {"min": 0, "max": None},
                "appraisal_price": {"min": 0, "max": None}
            },
            "areaRange": {
                "land_area": {"min": 0, "max": None},
                "building_area": {"min": 0, "max": None}
            },
            "addresses": {
                "pnu1": [],
                "pnu2": [],
                "pnu3": [],
                "address1": [],
                "address2": [],
                "address3": []
            },
            "all": False,
            "courts": [],
            "tags": {"mode": "exclude"}
        }

        # 필터 파라미터 추가 (tags는 덮어쓰기)
        payload.update(filter_param)

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            total = data.get("estimateTotal", 0)

            print(f"✅ 응답 성공: {len(results)}건 반환, 전체 {total:,}건")

            # 처음 5건의 winning_info 확인
            sold_count = 0
            for idx, item in enumerate(results[:5], 1):
                histories = item.get("histories", [])
                winning_info = None
                for hist in reversed(histories):
                    if hist.get("winning_info"):
                        winning_info = hist["winning_info"]
                        break

                case_id = item.get("case", {}).get("name", "Unknown")
                if winning_info:
                    sold_count += 1
                    print(f"  {idx}. 낙찰: {case_id}")
                else:
                    print(f"  {idx}. 미낙찰: {case_id}")

            print(f"  → 처음 5건 중 낙찰 완료: {sold_count}건")

            if sold_count == 5 and len(results) > 0:
                print(f"  🎯 이 필터가 작동합니다! 전체 {total:,}건")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 422:
                print(f"❌ 422 오류: 이 파라미터는 지원되지 않음")
            else:
                print(f"❌ HTTP 오류: {e}")
        except Exception as e:
            print(f"❌ 오류: {e}")

if __name__ == "__main__":
    test_advanced_filters()
