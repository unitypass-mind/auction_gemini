# -*- coding: utf-8 -*-
import requests
import json

def test_valueauction_api(case_no="2024타경579705"):
    """ValueAuction API 응답 구조 확인"""

    api_url = "https://valueauction.co.kr/api/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Content-Type": "application/json",
        "Referer": "https://valueauction.co.kr/",
        "Origin": "https://valueauction.co.kr"
    }

    payload = {
        "auctionType": "auction",
        "case": case_no
    }

    response = requests.post(api_url, json=payload, headers=headers, timeout=30)

    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])

        if results:
            item = results[0]
            print("=== API 응답 구조 ===")
            print(f"최상위 키들: {list(item.keys())}")
            print()

            # tags 관련 필드 찾기
            print("=== tags 관련 필드 ===")
            if 'tags' in item:
                print(f"tags: {item['tags']}")
            if 'badge' in item and 'tags' in item.get('badge', {}):
                print(f"badge.tags: {item['badge']['tags']}")

            # badge 정보
            if 'badge' in item:
                print(f"\n=== badge 정보 ===")
                badge = item['badge']
                print(f"badge 키들: {list(badge.keys())}")
                for key, value in badge.items():
                    if 'tag' in key.lower() or isinstance(value, list):
                        print(f"  {key}: {value}")

            # 전체 item 출력 (JSON 형식으로)
            print("\n=== 전체 응답 (처음 3000자) ===")
            json_str = json.dumps(item, ensure_ascii=False, indent=2)
            print(json_str[:3000])

            # JSON 파일로 저장
            with open('valueauction_response.json', 'w', encoding='utf-8') as f:
                json.dump(item, f, ensure_ascii=False, indent=2)
            print("\n전체 응답을 'valueauction_response.json' 파일에 저장했습니다.")
        else:
            print("검색 결과 없음")
    else:
        print(f"API 오류: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_valueauction_api()
