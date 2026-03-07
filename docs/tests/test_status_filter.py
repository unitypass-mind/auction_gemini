"""
ValueAuction API status 필터 테스트
낙찰된 물건만 가져오는 필터 값을 찾습니다.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json

def test_status_filter():
    """다양한 status 필터 값 테스트"""
    url = "https://valueauction.co.kr/api/search"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": "https://valueauction.co.kr/search",
        "Origin": "https://valueauction.co.kr"
    }

    # 테스트할 status 값들
    status_tests = [
        {"status": ["낙찰"]},
        {"status": ["매각"]},
        {"status": ["sold"]},
        {"soldOnly": True},
        {"isSold": True},
        # badge 기반 필터링도 테스트
        {"badge": {"sold": True}},
    ]

    print("=" * 80)
    print("Status 필터 테스트")
    print("=" * 80)

    for i, status_param in enumerate(status_tests, 1):
        print(f"\n{'=' * 80}")
        print(f"테스트 {i}: {json.dumps(status_param, ensure_ascii=False)}")
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

        # status 파라미터 추가
        payload.update(status_param)

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            total = data.get("estimateTotal", 0)

            print(f"✅ 응답 성공: {len(results)}건 반환, 전체 {total:,}건")

            # 처음 3건의 winning_info 확인
            sold_count = 0
            for item in results[:3]:
                histories = item.get("histories", [])
                winning_info = None
                for hist in reversed(histories):
                    if hist.get("winning_info"):
                        winning_info = hist["winning_info"]
                        break

                if winning_info:
                    sold_count += 1
                    case_id = item.get("case", {}).get("name", "Unknown")
                    print(f"  낙찰 완료: {case_id}")

            print(f"  → 처음 3건 중 낙찰 완료: {sold_count}건")

            if sold_count == 3 and len(results) > 0:
                print(f"  🎯 이 필터가 작동하는 것 같습니다!")

        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 실패: {e}")
        except Exception as e:
            print(f"❌ 오류: {e}")

    # 필터 없이 기본 요청도 테스트
    print(f"\n{'=' * 80}")
    print(f"비교: 필터 없는 기본 요청")
    print("=" * 80)

    base_payload = {
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

    try:
        response = requests.post(url, json=base_payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        total = data.get("estimateTotal", 0)

        print(f"✅ 응답 성공: {len(results)}건 반환, 전체 {total:,}건")

        sold_count = 0
        for item in results[:10]:
            histories = item.get("histories", [])
            winning_info = None
            for hist in reversed(histories):
                if hist.get("winning_info"):
                    winning_info = hist["winning_info"]
                    break

            if winning_info:
                sold_count += 1

        print(f"  → 처음 10건 중 낙찰 완료: {sold_count}건")

    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    test_status_filter()
