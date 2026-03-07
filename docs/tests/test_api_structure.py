"""
ValueAuction API 응답 구조 확인 스크립트
실제 API 응답을 출력하여 selling_price 필드 위치를 파악합니다.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
from datetime import datetime

def test_api_structure():
    """API 응답 구조 확인"""
    # ValueAuction API 엔드포인트
    url = "https://valueauction.co.kr/api/search"

    payload = {
        "limit": 5,  # 처음 5건만
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

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": "https://valueauction.co.kr/search",
        "Origin": "https://valueauction.co.kr"
    }

    print("=" * 80)
    print("ValueAuction API 테스트")
    print("=" * 80)
    print(f"URL: {url}")
    print(f"Method: POST\n")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        print(f"응답 상태: {response.status_code}")
        print(f"Success: {data.get('success')}")
        print(f"Total: {data.get('estimateTotal', 0):,}건\n")

        results = data.get("results", [])

        if not results:
            print("⚠️ 결과 없음")
            return

        print("=" * 80)
        print("첫 번째 아이템 전체 구조:")
        print("=" * 80)
        print(json.dumps(results[0], indent=2, ensure_ascii=False))
        print("\n")

        # 각 아이템의 price 구조만 출력
        print("=" * 80)
        print("처음 5개 아이템의 price 구조:")
        print("=" * 80)

        for i, item in enumerate(results, 1):
            case_id = item.get("case", {}).get("id", "Unknown")
            address = item.get("address", "Unknown")

            print(f"\n{i}. Case ID: {case_id}")
            print(f"   주소: {address}")
            print(f"   Price 구조:")
            print(f"   {json.dumps(item.get('price', {}), indent=6, ensure_ascii=False)}")

            # 직접 확인
            price_data = item.get("price", {})
            print(f"\n   직접 추출 테스트:")
            print(f"   - appraised_price: {price_data.get('appraised_price', 'NOT FOUND')}")
            print(f"   - selling_price: {price_data.get('selling_price', 'NOT FOUND')}")
            print(f"   - lowestSellingPrice: {price_data.get('lowestSellingPrice', 'NOT FOUND')}")
            print(f"   - sold_price: {price_data.get('sold_price', 'NOT FOUND')}")
            print(f"   - final_price: {price_data.get('final_price', 'NOT FOUND')}")
            print(f"   - 낙찰가: {price_data.get('낙찰가', 'NOT FOUND')}")

            # badge 정보도 확인
            badge = item.get("badge", {})
            print(f"\n   Badge 구조:")
            print(f"   {json.dumps(badge, indent=6, ensure_ascii=False)}")

            print("\n" + "-" * 80)

    except requests.exceptions.RequestException as e:
        print(f"❌ API 요청 실패: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 실패: {e}")
        print(f"응답 내용: {response.text[:500]}")
    except Exception as e:
        print(f"❌ 오류: {e}", exc_info=True)

if __name__ == "__main__":
    test_api_structure()
