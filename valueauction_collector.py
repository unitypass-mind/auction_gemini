"""
밸류옥션 낙찰 데이터 자동 수집 스크립트

실제 낙찰된 물건 데이터를 수집하여 AI 예측 → 즉시 검증
"""

import requests
import time
import json
from datetime import datetime
from database import db
from main import predict_price_advanced
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValueAuctionCollector:
    """밸류옥션 데이터 수집기"""

    def __init__(self):
        self.api_url = "https://valueauction.co.kr/api/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Referer": "https://valueauction.co.kr/search",
            "Origin": "https://valueauction.co.kr"
        }

    def fetch_sold_items(self, limit=20, offset=0, min_appraisal_price=0):
        """
        낙찰 완료 물건 가져오기 (법원 경매)

        Args:
            limit: 가져올 개수 (기본 20)
            offset: 시작 위치 (페이지네이션)
            min_appraisal_price: 최소 감정가 (기본 0, 고가 물건 필터용)

        Returns:
            dict: API 응답 데이터
        """
        payload = {
            # auctionType 파라미터 없음 = 기본값으로 법원 경매 조회
            # ⚠️ API는 낙찰 상태 필터를 지원하지 않음 (모든 테스트 실패)
            #    → 모든 상태 포함 (낙찰, 매각, 유찰 등 전체 13,267건)
            #    → 코드 레벨에서 winning_info 존재 여부로 필터링 (lines 217-238)
            "limit": limit,
            "offset": offset,
            "order": "bidding_date",
            "direction": "desc",  # 최신순
            "category": {
                "residential": ["전체"],
                "commercial": [],
                "land": []
            },
            "priceRange": {
                "min_ask_price": {"min": 0, "max": None},
                "appraisal_price": {"min": min_appraisal_price, "max": None}  # 최소 감정가 필터
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
            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"API 요청 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Status Code: {e.response.status_code}")
                logger.error(f"Response: {e.response.text[:500]}")
            return None

    def extract_region(self, address):
        """주소에서 지역 추출"""
        regions = ["서울", "경기", "인천", "부산", "대구", "대전", "광주", "울산", "세종",
                   "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]

        for region in regions:
            if region in address:
                return region

        # 기타 지역
        return "기타"

    def map_category(self, category):
        """물건종류 매핑"""
        category_map = {
            "아파트": "아파트",
            "다세대주택": "다세대",
            "단독주택": "단독주택",
            "근린생활시설": "상가",
            "오피스텔": "오피스텔",
            "도시형생활주택": "오피스텔",
            "주상복합": "오피스텔",
            "대지": "토지",
            "전": "토지",
            "답": "토지",
            "임야": "토지",
            "컨테이너주택": "기타"
        }

        return category_map.get(category, "기타")

    def collect_and_verify(self, max_items=50, start_offset=0, min_appraisal_price=0, continuous=False, days_limit=None):
        """
        낙찰 물건 수집 → 예측 → 검증

        Args:
            max_items: 최대 확인할 개수 (continuous=True일 경우 API에서 가져올 최대 개수)
            start_offset: 시작 오프셋
            min_appraisal_price: 최소 감정가 (기본 0, 고가 물건 필터용)
            continuous: 지속적 수집 모드 (중복 체크 후 새로운 데이터만 추가)
            days_limit: 최근 N일 이내 데이터만 수집 (None이면 전체)

        Returns:
            dict: 수집 통계
        """
        stats = {
            "total_fetched": 0,
            "total_processed": 0,
            "skipped": 0,
            "not_sold": 0,  # 낙찰되지 않은 물건
            "too_old": 0,  # 너무 오래된 물건
            "duplicates": 0,
            "errors": 0
        }

        # 날짜 제한 계산
        cutoff_timestamp = None
        if days_limit:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days_limit)
            cutoff_timestamp = int(cutoff_date.timestamp())
            logger.info(f"📅 날짜 필터: 최근 {days_limit}일 이내 데이터만 수집 ({cutoff_date.strftime('%Y-%m-%d')} 이후)")

        # 기존 DB에 있는 case_no 목록 로드 (중복 체크용)
        import sqlite3
        conn = sqlite3.connect("data/predictions.db")
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT case_no FROM predictions")
        existing_case_ids = set(row[0] for row in cursor.fetchall() if row[0])
        conn.close()
        logger.info(f"💡 DB에 이미 {len(existing_case_ids)}건 존재, 중복은 자동으로 건너뜀")

        offset = start_offset
        items_checked = 0  # 확인한 아이템 수
        consecutive_duplicates = 0  # 연속 중복 카운터

        while items_checked < max_items:
            logger.info(f"데이터 가져오는 중... (offset: {offset}, 확인: {items_checked}/{max_items})")

            data = self.fetch_sold_items(limit=20, offset=offset, min_appraisal_price=min_appraisal_price)

            if not data or not data.get("success"):
                logger.error("API 응답 실패")
                break

            results = data.get("results", [])

            if not results:
                logger.info("더 이상 데이터가 없습니다")
                break

            stats["total_fetched"] += len(results)

            for item in results:
                items_checked += 1
                if not continuous and stats["total_processed"] >= max_items:
                    break

                try:
                    # 데이터 추출
                    case_id = item["case"]["id"]
                    case_name = item["case"].get("name", str(case_id))

                    # 중복 체크 (모든 모드에서 수행)
                    if case_name in existing_case_ids:
                        stats["duplicates"] += 1
                        consecutive_duplicates += 1
                        logger.debug(f"중복 건너뜀: {case_name}")

                        # 연속으로 20건 이상 중복이면 더 이상 새로운 데이터가 없다고 판단
                        if consecutive_duplicates >= 20:
                            logger.info(f"✅ 연속 {consecutive_duplicates}건 중복 - 최신 데이터까지 확인 완료")
                            return stats
                        continue

                    # 새로운 데이터 발견 시 중복 카운터 리셋
                    consecutive_duplicates = 0

                    # 날짜 필터 체크
                    if cutoff_timestamp:
                        bidding_date = item.get("bidding_date", 0)
                        if bidding_date > 0 and bidding_date < cutoff_timestamp:
                            stats["too_old"] += 1
                            logger.debug(f"너무 오래된 물건 건너뜀: {case_name}")
                            # 연속으로 20건 이상 오래된 데이터면 중단
                            consecutive_duplicates += 1  # too_old도 중복처럼 처리
                            if consecutive_duplicates >= 20:
                                logger.info(f"✅ 연속 20건 이상 오래된 데이터 - 날짜 범위 초과")
                                return stats
                            continue

                    address = item["address"]

                    price_data = item["price"]
                    appraised_price = int(price_data.get("appraised_price", 0))

                    badge = item["badge"]
                    category = badge.get("category", "기타")
                    area = badge.get("area_buildings", 0) or badge.get("area", 0)
                    failure_count = badge.get("failure_count", 0)

                    # ===== 신규 변수 추출 =====
                    # 1. 실제 입찰자 수 및 낙찰가
                    histories = item.get("histories", [])
                    winning_info = None
                    for hist in reversed(histories):
                        if hist.get("winning_info"):
                            winning_info = hist["winning_info"]
                            break

                    # 낙찰 완료 여부 확인 - winning_info가 없으면 건너뛰기
                    if not winning_info:
                        # price_data에서 selling_price 확인 (older records용)
                        selling_price = int(price_data.get("selling_price", 0))
                        if selling_price <= 0:
                            # 낙찰되지 않은 물건 - 건너뛰기
                            stats["not_sold"] += 1
                            logger.debug(f"낙찰 미완료 건너뜀: {case_name}")
                            continue
                        # 오래된 레코드 (selling_price가 이미 설정됨)
                        bidders_count_actual = 1
                        second_price = 0
                    else:
                        # winning_info에서 실제 낙찰가 추출 (newer records)
                        selling_price = int(winning_info.get("winning_price", 0))
                        bidders_count_actual = winning_info.get("bidders_count", 1)
                        second_price = winning_info.get("second_price", 0)

                    logger.info(f"  낙찰 완료: {case_name} - 낙찰가 {selling_price:,}원 (입찰자 {bidders_count_actual}명)")

                    # 2. 권리분석 복잡도
                    is_hard = badge.get("is_hard", False)

                    # 3. 권리사항 태그 수
                    tags = badge.get("tags", [])
                    tag_count = len(tags)

                    # 4. 공유지분 여부
                    has_share_floor = item.get("has_share_floor", False)
                    has_share_land = item.get("has_share_land", False)

                    # 5. 청구금액
                    auction_data = item.get("auction", {})
                    claim_amount = int(auction_data.get("claim_amount", 0))
                    debt_ratio = (claim_amount / appraised_price) if appraised_price > 0 else 0

                    # 검증: 감정가 확인
                    if not appraised_price or appraised_price == 0:
                        logger.warning(f"Skip {case_name}: 감정가 정보 없음")
                        stats["skipped"] += 1
                        continue

                    # 지역 추출
                    region = self.extract_region(address)

                    # 물건종류 매핑
                    property_type = self.map_category(category)

                    # 면적 기본값 설정
                    if area == 0:
                        area = 85.0  # 기본 면적

                    logger.info(f"\n처리 중: {case_id}")
                    logger.info(f"  감정가: {appraised_price:,}원")
                    logger.info(f"  낙찰가: {selling_price:,}원")
                    logger.info(f"  물건: {category} ({property_type})")
                    logger.info(f"  지역: {region}")
                    logger.info(f"  면적: {area}㎡")
                    logger.info(f"  입찰자: {bidders_count_actual}명 (2등가: {second_price:,}원)")
                    logger.info(f"  권리: {'복잡' if is_hard else '일반'}, 태그: {tag_count}개")
                    logger.info(f"  공유: 건물={has_share_floor}, 토지={has_share_land}")

                    # AI 예측 생성
                    predicted_price = predict_price_advanced(
                        start_price=appraised_price,
                        property_type=property_type,
                        region=region,
                        area=float(area),
                        auction_round=failure_count + 1,
                        bidders=10  # 기본값
                    )

                    logger.info(f"  예측: {predicted_price:,}원")

                    # DB에 예측 저장
                    db_case_no = f"VA-{case_id}"  # ValueAuction 접두사

                    # 예상 수익 계산
                    expected_profit = appraised_price - predicted_price
                    profit_rate = (expected_profit / appraised_price * 100) if appraised_price > 0 else 0

                    prediction_data = {
                        "case_no": db_case_no,
                        "사건번호": case_name,  # 실제 사건번호 (예: 2024타경88398)
                        "감정가": appraised_price,
                        "물건종류": property_type,
                        "지역": region,
                        "면적": float(area),
                        "경매회차": failure_count + 1,
                        "입찰자수": bidders_count_actual,  # 실제 입찰자 수로 변경
                        "predicted_price": predicted_price,
                        "expected_profit": expected_profit,
                        "profit_rate": profit_rate,
                        "prediction_mode": "advanced",
                        "model_used": True,
                        "source": "valueauction",
                        # 신규 변수
                        "입찰자수_실제": bidders_count_actual,
                        "second_price": second_price,
                        "권리분석복잡도": 1 if is_hard else 0,
                        "권리사항태그수": tag_count,
                        "공유지분_건물": 1 if has_share_floor else 0,
                        "공유지분_토지": 1 if has_share_land else 0,
                        "청구금액": claim_amount,
                        "청구금액비율": debt_ratio,
                    }

                    db.save_prediction(prediction_data)

                    # 실제 낙찰가로 즉시 검증
                    today = datetime.now().strftime("%Y-%m-%d")

                    success = db.update_actual_result(
                        case_no=db_case_no,
                        actual_price=selling_price,
                        actual_date=today
                    )

                    if success:
                        error_rate = abs(predicted_price - selling_price) / selling_price * 100
                        logger.info(f"  ✅ 검증 완료! 오차율: {error_rate:.2f}%")
                        stats["total_processed"] += 1
                    else:
                        logger.error(f"  ❌ 검증 실패")
                        stats["errors"] += 1

                except Exception as e:
                    logger.error(f"오류 발생: {e}", exc_info=True)
                    stats["errors"] += 1
                    continue

                # 요청 제한 (1초 대기)
                time.sleep(1)

            # 다음 페이지
            offset += 20

            # 페이지 간 대기
            time.sleep(2)

        return stats

    def collect_preview(self, limit=5):
        """
        미리보기: 처음 몇 개만 확인

        Args:
            limit: 확인할 개수
        """
        logger.info(f"=== 미리보기: 처음 {limit}건 확인 ===\n")

        data = self.fetch_sold_items(limit=limit, offset=0)

        if not data or not data.get("success"):
            logger.error("API 응답 실패")
            return

        results = data.get("results", [])
        total = data.get("estimateTotal", 0)

        logger.info(f"총 {total:,}건의 낙찰 데이터 발견!\n")

        for i, item in enumerate(results, 1):
            case_id = item["case"]["id"]
            address = item["address"]

            price_data = item["price"]
            appraised_price = int(price_data.get("appraised_price", 0))
            selling_price = int(price_data.get("selling_price", 0))

            badge = item["badge"]
            category = badge.get("category", "기타")

            logger.info(f"{i}. {case_id}")
            logger.info(f"   주소: {address}")
            logger.info(f"   물건: {category}")
            logger.info(f"   감정가: {appraised_price:,}원")
            logger.info(f"   낙찰가: {selling_price:,}원")
            logger.info("")


def main():
    """메인 실행"""
    collector = ValueAuctionCollector()

    print("=" * 60)
    print("밸류옥션 낙찰 데이터 수집기")
    print("=" * 60)
    print()

    # 미리보기
    print("1. 미리보기 (5건)")
    print("2. 소량 수집 (10건)")
    print("3. 중량 수집 (50건)")
    print("4. 대량 수집 (100건)")
    print()

    choice = input("선택하세요 (1-4): ").strip()

    if choice == "1":
        collector.collect_preview(limit=5)

    elif choice == "2":
        print("\n10건 수집 시작...\n")
        stats = collector.collect_and_verify(max_items=10)
        print("\n" + "=" * 60)
        print("수집 완료!")
        print(f"가져온 데이터: {stats['total_fetched']}건")
        print(f"처리 완료: {stats['total_processed']}건")
        print(f"건너뜀: {stats['skipped']}건")
        print(f"오류: {stats['errors']}건")
        print("=" * 60)

    elif choice == "3":
        print("\n50건 수집 시작...\n")
        stats = collector.collect_and_verify(max_items=50)
        print("\n" + "=" * 60)
        print("수집 완료!")
        print(f"가져온 데이터: {stats['total_fetched']}건")
        print(f"처리 완료: {stats['total_processed']}건")
        print(f"건너뜀: {stats['skipped']}건")
        print(f"오류: {stats['errors']}건")
        print("=" * 60)

    elif choice == "4":
        confirm = input("100건 수집하시겠습니까? (yes/no): ").strip().lower()
        if confirm == "yes":
            print("\n100건 수집 시작...\n")
            stats = collector.collect_and_verify(max_items=100)
            print("\n" + "=" * 60)
            print("수집 완료!")
            print(f"가져온 데이터: {stats['total_fetched']}건")
            print(f"처리 완료: {stats['total_processed']}건")
            print(f"건너뜀: {stats['skipped']}건")
            print(f"오류: {stats['errors']}건")
            print("=" * 60)

    else:
        print("잘못된 선택입니다.")


if __name__ == "__main__":
    main()
