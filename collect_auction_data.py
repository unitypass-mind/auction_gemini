"""
법원 경매 사이트 데이터 수집 스크립트
실제 경매 데이터를 크롤링하여 CSV 파일로 저장
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
from pathlib import Path
import re
from datetime import datetime
from typing import List, Dict, Optional
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CourtAuctionCrawler:
    """법원 경매 사이트 크롤러"""

    def __init__(self):
        self.base_url = "https://www.courtauction.go.kr"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def clean_number(self, text: str) -> int:
        """텍스트에서 숫자만 추출"""
        try:
            cleaned = re.sub(r'[^\d]', '', text)
            return int(cleaned) if cleaned else 0
        except:
            return 0

    def clean_text(self, text: str) -> str:
        """텍스트 정제"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text).strip()

    def extract_area(self, text: str) -> float:
        """면적 추출 (㎡)"""
        try:
            # "85.5㎡" 형식에서 숫자 추출
            match = re.search(r'([\d,]+\.?\d*)', text)
            if match:
                return float(match.group(1).replace(',', ''))
            return 0.0
        except:
            return 0.0

    def get_auction_list(self, page: int = 1, items_per_page: int = 20) -> List[str]:
        """
        경매 물건 목록 가져오기

        Returns:
            물건번호 리스트
        """
        try:
            # 실제 법원 경매 사이트 검색 URL
            # 부동산 > 아파트로 필터링
            search_url = f"{self.base_url}/RetrieveRealEstMulDetailList.laf"

            params = {
                "targetRow": items_per_page,
                "page": page,
                "realVowel": "35007",  # 부동산-아파트
                "srnID": "PNO102001",
            }

            logger.info(f"페이지 {page} 검색 중...")
            response = self.session.get(search_url, params=params, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 물건번호 추출 (실제 사이트 구조에 맞게 수정 필요)
            item_numbers = []

            # 테이블에서 물건번호 찾기
            # 실제 HTML 구조에 따라 selector 수정 필요
            links = soup.select("a[href*='RetrieveRealEstDetailInqSaList']")

            for link in links:
                href = link.get('href', '')
                # URL에서 물건번호 추출
                match = re.search(r'msSeq=(\d+)', href)
                if match:
                    item_numbers.append(match.group(1))

            logger.info(f"페이지 {page}에서 {len(item_numbers)}개 물건번호 추출")
            return item_numbers

        except Exception as e:
            logger.error(f"물건 목록 가져오기 실패: {e}")
            return []

    def get_auction_detail(self, item_no: str) -> Optional[Dict]:
        """
        특정 물건의 상세 정보 가져오기
        """
        try:
            detail_url = f"{self.base_url}/RetrieveRealEstDetailInqSaList.laf"
            params = {"msSeq": item_no}

            logger.info(f"물건 {item_no} 상세 정보 수집 중...")
            response = self.session.get(detail_url, params=params, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 데이터 추출 (실제 HTML 구조에 맞게 수정 필요)
            data = {
                "물건번호": item_no,
                "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # 기본 정보 테이블 파싱
            tables = soup.select("table")

            if tables:
                # 사건번호, 물건종류 등
                rows = tables[0].find_all("tr")
                for row in rows:
                    cells = row.find_all(["th", "td"])
                    if len(cells) >= 2:
                        key = self.clean_text(cells[0].get_text())
                        value = self.clean_text(cells[1].get_text())

                        if "사건번호" in key:
                            data["사건번호"] = value
                        elif "물건종류" in key:
                            data["물건종류"] = value
                        elif "소재지" in key or "위치" in key:
                            data["소재지"] = value
                        elif "감정가" in key:
                            data["감정가"] = self.clean_number(value)
                        elif "최저가" in key or "최저입찰가" in key:
                            data["최저입찰가"] = self.clean_number(value)
                        elif "낙찰가" in key or "매각가격" in key:
                            data["낙찰가"] = self.clean_number(value)
                        elif "입찰자수" in key or "입찰인원" in key:
                            data["입찰자수"] = self.clean_number(value)
                        elif "면적" in key:
                            data["면적"] = self.extract_area(value)
                        elif "경매회차" in key or "매각회차" in key:
                            data["경매회차"] = self.clean_number(value)

            # 필수 필드 확인
            if "감정가" not in data or data["감정가"] == 0:
                logger.warning(f"물건 {item_no}: 감정가 정보 없음")
                return None

            return data

        except Exception as e:
            logger.error(f"물건 {item_no} 상세 정보 수집 실패: {e}")
            return None

    def crawl_multiple_items(
        self,
        num_pages: int = 5,
        items_per_page: int = 20,
        delay: float = 2.0
    ) -> pd.DataFrame:
        """
        여러 페이지의 경매 물건 정보 수집
        """
        all_data = []

        logger.info(f"총 {num_pages}페이지 크롤링 시작...")

        for page in range(1, num_pages + 1):
            # 물건 목록 가져오기
            item_numbers = self.get_auction_list(page, items_per_page)

            if not item_numbers:
                logger.warning(f"페이지 {page}: 물건 없음, 중단")
                break

            # 각 물건의 상세 정보 수집
            for item_no in item_numbers:
                detail = self.get_auction_detail(item_no)
                if detail:
                    all_data.append(detail)

                # 서버 부하 방지를 위한 딜레이
                time.sleep(delay)

            logger.info(f"페이지 {page}/{num_pages} 완료 - 현재까지 {len(all_data)}건 수집")

        # DataFrame 생성
        df = pd.DataFrame(all_data)
        logger.info(f"총 {len(df)}건의 데이터 수집 완료")

        return df


def generate_realistic_sample_data(n_samples: int = 1000) -> pd.DataFrame:
    """
    실제 경매 패턴을 반영한 현실적인 샘플 데이터 생성
    실제 데이터가 없을 경우 사용
    """
    import numpy as np

    np.random.seed(42)

    logger.info(f"현실적인 샘플 데이터 {n_samples}건 생성 중...")

    # 물건 종류별 특성
    property_types = {
        "아파트": {"base_price_range": (100_000_000, 1_000_000_000), "avg_rate": 0.75},
        "다세대": {"base_price_range": (50_000_000, 500_000_000), "avg_rate": 0.70},
        "오피스텔": {"base_price_range": (80_000_000, 600_000_000), "avg_rate": 0.72},
        "단독주택": {"base_price_range": (150_000_000, 800_000_000), "avg_rate": 0.68},
        "상가": {"base_price_range": (100_000_000, 2_000_000_000), "avg_rate": 0.65},
    }

    # 지역별 특성
    regions = {
        "서울": {"premium": 1.5, "bidder_multiplier": 1.3},
        "경기": {"premium": 1.2, "bidder_multiplier": 1.1},
        "인천": {"premium": 1.1, "bidder_multiplier": 1.0},
        "부산": {"premium": 1.0, "bidder_multiplier": 0.9},
        "대구": {"premium": 0.9, "bidder_multiplier": 0.8},
        "기타": {"premium": 0.8, "bidder_multiplier": 0.7},
    }

    data = []

    for i in range(n_samples):
        # 물건 종류 선택
        property_type = np.random.choice(list(property_types.keys()))
        prop_config = property_types[property_type]

        # 지역 선택
        region = np.random.choice(list(regions.keys()), p=[0.3, 0.3, 0.1, 0.1, 0.1, 0.1])
        region_config = regions[region]

        # 감정가 생성
        min_price, max_price = prop_config["base_price_range"]
        appraisal_price = np.random.uniform(min_price, max_price) * region_config["premium"]

        # 면적 (물건 종류에 따라 다름)
        if property_type == "아파트":
            area = np.random.uniform(40, 150)
        elif property_type == "오피스텔":
            area = np.random.uniform(20, 80)
        elif property_type == "상가":
            area = np.random.uniform(30, 200)
        else:
            area = np.random.uniform(30, 120)

        # 경매 회차 (1~5회)
        auction_round = np.random.choice([1, 2, 3, 4, 5], p=[0.4, 0.3, 0.2, 0.07, 0.03])

        # 회차별 최저가율 (1회차 100%, 2회차 80%, 3회차 64%...)
        min_bid_rate = 0.8 ** (auction_round - 1)
        min_bid_price = appraisal_price * min_bid_rate

        # 입찰자 수 (지역, 회차, 가격에 영향)
        base_bidders = np.random.poisson(8) + 1
        bidders = int(base_bidders * region_config["bidder_multiplier"] / auction_round)
        bidders = max(1, min(bidders, 50))

        # 낙찰가 계산 (현실적인 패턴)
        # 기본 낙찰률
        base_rate = prop_config["avg_rate"]

        # 입찰자가 많을수록 낙찰가 상승
        bidder_effect = (bidders - 1) * 0.01  # 입찰자 1명당 1% 상승

        # 회차가 높을수록 낙찰가 하락
        round_effect = -(auction_round - 1) * 0.05

        # 지역 프리미엄 효과
        region_effect = (region_config["premium"] - 1) * 0.1

        # 최종 낙찰률
        final_rate = base_rate + bidder_effect + round_effect + region_effect

        # 노이즈 추가
        noise = np.random.normal(0, 0.03)
        final_rate = np.clip(final_rate + noise, 0.5, 1.2)

        # 낙찰가 = 최저가 * 낙찰률
        final_price = min_bid_price * (final_rate / min_bid_rate)
        final_price = max(min_bid_price, final_price)  # 최저가 이상

        # 데이터 추가
        data.append({
            "물건번호": f"SAMPLE-{i+1:06d}",
            "사건번호": f"2024타경{np.random.randint(10000, 99999)}",
            "물건종류": property_type,
            "소재지": f"{region} {np.random.choice(['강남구', '서초구', '송파구', '중구', '남구'])}",
            "감정가": int(appraisal_price),
            "최저입찰가": int(min_bid_price),
            "낙찰가": int(final_price),
            "입찰자수": bidders,
            "면적": round(area, 2),
            "경매회차": auction_round,
            "지역": region,
            "낙찰률": round(final_price / appraisal_price, 4),
            "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    df = pd.DataFrame(data)

    logger.info(f"샘플 데이터 생성 완료: {len(df)}건")
    logger.info(f"감정가 범위: {df['감정가'].min():,}원 ~ {df['감정가'].max():,}원")
    logger.info(f"평균 낙찰률: {df['낙찰률'].mean():.2%}")
    logger.info(f"물건 종류 분포:\n{df['물건종류'].value_counts()}")
    logger.info(f"지역 분포:\n{df['지역'].value_counts()}")

    return df


def main():
    """메인 함수"""
    logger.info("="*60)
    logger.info("법원 경매 데이터 수집 시작")
    logger.info("="*60)

    # 데이터 저장 경로
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # 사용자 선택
    print("\n데이터 수집 방법을 선택하세요:")
    print("1. 실제 크롤링 (법원 경매 사이트)")
    print("2. 현실적인 샘플 데이터 생성 (권장)")
    choice = input("선택 (1 or 2): ").strip()

    if choice == "1":
        # 실제 크롤링
        print("\n⚠️  주의사항:")
        print("- 법원 경매 사이트의 robots.txt를 준수해야 합니다")
        print("- 과도한 크롤링은 IP 차단의 원인이 될 수 있습니다")
        print("- 수집한 데이터는 개인적인 용도로만 사용하세요")

        confirm = input("\n계속하시겠습니까? (y/n): ").strip().lower()

        if confirm == 'y':
            crawler = CourtAuctionCrawler()

            num_pages = int(input("크롤링할 페이지 수 (권장: 5): ") or "5")
            delay = float(input("요청 간 딜레이(초) (권장: 2): ") or "2")

            df = crawler.crawl_multiple_items(
                num_pages=num_pages,
                items_per_page=20,
                delay=delay
            )

            if df.empty:
                logger.warning("크롤링 실패, 샘플 데이터로 전환합니다")
                df = generate_realistic_sample_data(1000)
        else:
            logger.info("크롤링 취소, 샘플 데이터 생성으로 전환")
            df = generate_realistic_sample_data(1000)
    else:
        # 샘플 데이터 생성
        n_samples = int(input("생성할 샘플 데이터 수 (권장: 2000): ") or "2000")
        df = generate_realistic_sample_data(n_samples)

    # 데이터 저장
    if not df.empty:
        output_file = data_dir / "auction_data.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        logger.info(f"\n데이터 저장 완료: {output_file}")
        logger.info(f"총 {len(df)}건의 데이터 저장됨")

        # 기본 통계
        logger.info("\n" + "="*60)
        logger.info("데이터 통계")
        logger.info("="*60)
        logger.info(f"감정가 평균: {df['감정가'].mean():,.0f}원")
        logger.info(f"낙찰가 평균: {df['낙찰가'].mean():,.0f}원")
        logger.info(f"평균 낙찰률: {(df['낙찰가'] / df['감정가']).mean():.2%}")
        logger.info(f"평균 입찰자 수: {df['입찰자수'].mean():.1f}명")

        if '물건종류' in df.columns:
            logger.info(f"\n물건 종류별 평균 낙찰률:")
            for ptype in df['물건종류'].unique():
                rate = (df[df['물건종류']==ptype]['낙찰가'] / df[df['물건종류']==ptype]['감정가']).mean()
                logger.info(f"  {ptype}: {rate:.2%}")

    else:
        logger.error("데이터가 없습니다")


if __name__ == "__main__":
    main()
