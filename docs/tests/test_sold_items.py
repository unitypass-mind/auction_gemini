"""
낙찰 완료된 물건만 확인하는 스크립트
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json

def test_sold_items():
    """낙찰 완료된 물건 찾기"""
    url = "https://valueauction.co.kr/api/search"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": "https://valueauction.co.kr/search",
        "Origin": "https://valueauction.co.kr"
    }

    print("=" * 80)
    print("낙찰 완료 물건 찾기 (여러 offset 검색)")
    print("=" * 80)

    # 여러 offset을 시도하여 낙찰 완료된 물건 찾기
    offsets_to_try = [0, 100, 200, 500, 1000, 2000]
    total_sold = 0
    sold_examples = []

    for offset in offsets_to_try:
        print(f"\n{'=' * 80}")
        print(f"Offset {offset} ~ {offset+100} 검색 중...")
        print('=' * 80)

        payload = {
            "limit": 100,
            "offset": offset,
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
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            print(f"총 {len(results)}건 검색")

            offset_sold = 0
            for i, item in enumerate(results, 1):
                case_id = item.get("case", {}).get("name", "Unknown")
                address = item.get("address", "Unknown")

                # histories에서 winning_info 확인
                histories = item.get("histories", [])
                winning_info = None
                for hist in reversed(histories):
                    if hist.get("winning_info"):
                        winning_info = hist["winning_info"]
                        break

                if winning_info:
                    offset_sold += 1
                    total_sold += 1

                    # 처음 3건만 상세 정보 저장
                    if len(sold_examples) < 3:
                        sold_examples.append({
                            "case_id": case_id,
                            "address": address,
                            "winning_info": winning_info,
                            "price": item.get("price", {}),
                            "offset": offset
                        })

            print(f"  낙찰 완료: {offset_sold}건")

            # 충분히 찾았으면 중단
            if len(sold_examples) >= 3:
                break

        except Exception as e:
            print(f"오류 (offset {offset}): {e}")
            continue

    # 결과 요약
    print(f"\n\n{'=' * 80}")
    print(f"전체 낙찰 완료 물건: {total_sold}건")
    print('=' * 80)

    # 상세 정보 출력
    for idx, example in enumerate(sold_examples, 1):
        print(f"\n{'=' * 80}")
        print(f"낙찰 예시 #{idx} (Offset: {example['offset']})")
        print('=' * 80)
        print(f"사건번호: {example['case_id']}")
        print(f"주소: {example['address']}")
        print(f"\nWinning Info 구조:")
        print(json.dumps(example['winning_info'], indent=2, ensure_ascii=False))
        print(f"\nPrice 구조:")
        print(json.dumps(example['price'], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_sold_items()
