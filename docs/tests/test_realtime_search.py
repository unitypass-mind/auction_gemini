# -*- coding: utf-8 -*-
"""
실시간 경매 정보 검색 테스트
웹 UI 테스트 전 API 엔드포인트 직접 테스트
"""

import requests
import json

def test_auction_search(case_no):
    """
    /auction API 엔드포인트 테스트

    Args:
        case_no: 사건번호 (예: "2025타경32075")
    """
    print("=" * 80)
    print(f"실시간 경매 정보 검색 테스트: {case_no}")
    print("=" * 80)

    # API 호출
    url = f"http://localhost:8000/auction?case_no={case_no}&bidders=10"

    print(f"\n[요청]")
    print(f"URL: {url}")

    try:
        response = requests.get(url, timeout=60)

        print(f"\n[응답]")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if data.get('success'):
                auction_info = data['data']['auction_info']

                print(f"\n✓ 성공! 경매 정보를 가져왔습니다.\n")
                print(f"=" * 80)
                print(f"[경매 물건 정보]")
                print(f"=" * 80)
                print(f"  사건번호: {auction_info.get('사건번호')}")
                print(f"  물건종류: {auction_info.get('물건종류')}")
                print(f"  소재지: {auction_info.get('소재지')}")
                print(f"  감정가: {auction_info.get('감정가')}")
                print(f"  면적: {auction_info.get('면적')}")
                print(f"  경매회차: {auction_info.get('경매회차')}")
                print(f"  지역: {auction_info.get('지역')}")
                print(f"  데이터소스: {auction_info.get('데이터소스')}")

                print(f"\n" + "=" * 80)
                print(f"[AI 예측 결과]")
                print(f"=" * 80)
                print(f"  예측 낙찰가: {data['data'].get('predicted_price_formatted')}")
                print(f"  시장가: {data['data'].get('market_price_formatted')}")

                profit = data['data'].get('profit_analysis', {})
                print(f"\n  예상 수익: {profit.get('예상수익_formatted', 'N/A')}")
                print(f"  예상 수익률: {profit.get('예상수익률', 0):.2f}%")

                print(f"\n" + "=" * 80)
                print(f"[참고]")
                print(f"  {auction_info.get('note', '')}")
                print(f"=" * 80)

                return True
            else:
                print(f"\n✗ 실패: {data.get('error', '알 수 없는 오류')}")
                return False
        else:
            print(f"\n✗ HTTP 오류: {response.status_code}")
            print(f"응답: {response.text[:500]}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"\n✗ 서버 연결 실패")
        print(f"서버가 http://localhost:8000 에서 실행 중인지 확인하세요.")
        return False
    except Exception as e:
        print(f"\n✗ 예외 발생: {e}")
        return False


if __name__ == "__main__":
    print("\n")
    print("=" * 80)
    print("실시간 경매 정보 검색 기능 테스트")
    print("=" * 80)
    print("\n이 테스트는 다음을 확인합니다:")
    print("1. 로컬 CSV DB 검색")
    print("2. ValueAuction API 실시간 검색 (CSV에 없을 경우)")
    print("3. AI 낙찰가 예측")
    print("\n")

    # 테스트 1: ValueAuction에서 확인한 실제 사건번호
    print("\n[테스트 1] ValueAuction 실제 사건번호")
    test_auction_search("2025타경32075")

    print("\n\n")

    # 테스트 2: 로컬 DB에 있는 사건번호 (샘플)
    print("[테스트 2] 로컬 DB 사건번호 (샘플)")
    test_auction_search("2024타경00001")

    print("\n\n")
    print("=" * 80)
    print("테스트 완료!")
    print("=" * 80)
    print("\n다음 단계:")
    print("1. 웹 브라우저에서 http://localhost:8000 접속")
    print("2. '전체 분석' 탭 클릭")
    print("3. 사건번호 입력: 2025타경32075")
    print("4. '예측하기' 버튼 클릭")
    print("\n실시간 경매 정보가 자동으로 조회되는지 확인하세요!")
    print("=" * 80)
