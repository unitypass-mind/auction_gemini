"""
사건 2025타경11549 상세 분석
"""
import sqlite3
import json
import sys

DB_PATH = "data/predictions.db"

def analyze_case(case_no):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 한글 컬럼명 확인
    cursor.execute("PRAGMA table_info(predictions)")
    cols = cursor.fetchall()
    col_names = [col[1] for col in cols]

    # 데이터 조회
    cursor.execute(f"SELECT * FROM predictions WHERE case_no = ?", (case_no,))
    row = cursor.fetchone()

    if not row:
        print(f"❌ {case_no} 데이터를 찾을 수 없습니다.")
        return

    # 딕셔너리로 변환
    data = dict(zip(col_names, row))

    print("=" * 70)
    print(f"사건번호: {case_no} 상세 분석")
    print("=" * 70)

    print("\n[1. 기본 정보]")
    print(f"  사건번호: {data.get('case_no', 'N/A')}")
    print(f"  물건종류: {data.get('물건종류', 'N/A')}")
    print(f"  지역: {data.get('지역', 'N/A')}")
    print(f"  면적: {data.get('면적', 'N/A')}㎡")
    print(f"  감정가: {data.get('감정가', 0):,}원")

    print("\n[2. 경매 진행 정보]")
    print(f"  경매회차: {data.get('경매회차', 'N/A')}회")
    print(f"  입찰자수 (공고): {data.get('입찰자수', 'N/A')}명")
    print(f"  입찰자수 (실제): {data.get('입찰자수_실제', 'N/A')}명")

    print("\n[3. 권리/부채 정보]")
    print(f"  공유지분_건물: {data.get('공유지분_건물', 'N/A')}")
    print(f"  공유지분_토지: {data.get('공유지분_토지', 'N/A')}")
    print(f"  청구금액: {data.get('청구금액', 'N/A'):,}원" if data.get('청구금액') else "  청구금액: N/A")
    print(f"  청구금액비율: {data.get('청구금액비율', 'N/A')}")
    print(f"  2순위 가격: {data.get('second_price', 'N/A'):,}원" if data.get('second_price') else "  2순위 가격: N/A")

    print("\n[4. 예측 vs 실제]")
    predicted = data.get('predicted_price', 0) or 0
    actual = data.get('actual_price', 0) or 0
    error_rate = data.get('error_rate', 0) or 0

    print(f"  예측가격: {predicted:,}원")
    print(f"  실제낙찰가: {actual:,}원" if actual > 0 else "  실제낙찰가: 아직 낙찰되지 않음")
    if actual > 0:
        print(f"  오차: {actual - predicted:,}원")
        print(f"  오차율: {error_rate:.2f}%")

    # 감정가 대비 비율
    if data.get('감정가'):
        appraisal = data.get('감정가')
        pred_ratio = (predicted / appraisal * 100) if appraisal else 0
        actual_ratio = (actual / appraisal * 100) if appraisal else 0
        print(f"\n  예측가/감정가: {pred_ratio:.2f}%")
        print(f"  낙찰가/감정가: {actual_ratio:.2f}%")

    print("\n[5. 기타 정보]")
    print(f"  데이터소스: {data.get('source', 'N/A')}")
    print(f"  예측시각: {data.get('created_at', 'N/A')}")
    print(f"  낙찰일자: {data.get('actual_date', 'N/A')}")
    print(f"  검증여부: {'O' if data.get('verified') else 'X'}")

    # 경매회차별 최저입찰가 계산
    print("\n[6. 최저입찰가 분석]")
    auction_round = data.get('경매회차', 1)
    appraisal = data.get('감정가', 0)

    ratio = 1.0
    for _ in range(auction_round - 1):
        ratio *= 0.8

    lowest_bid = int(appraisal * ratio)
    print(f"  경매회차: {auction_round}회")
    print(f"  최저가율: {ratio:.2f} ({ratio*100:.1f}%)")
    print(f"  최저입찰가: {lowest_bid:,}원")
    print(f"  실제낙찰가: {actual:,}원")

    if actual > 0:
        actual_vs_lowest = (actual / lowest_bid) if lowest_bid > 0 else 0
        print(f"  낙찰가/최저가: {actual_vs_lowest:.2f}배 ({actual_vs_lowest*100:.1f}%)")

    conn.close()

    # 분석 및 제안
    print("\n" + "=" * 70)
    print("📊 ULTRA THINK 분석")
    print("=" * 70)

    print("\n🔍 예측 오차 발생 원인 분석:")

    # 1. 최저입찰가 대비 낙찰가 분석
    if actual > 0 and lowest_bid > 0:
        actual_vs_lowest = actual / lowest_bid
        if actual_vs_lowest > 1.15:
            print(f"  ⚠️  낙찰가가 최저입찰가의 {actual_vs_lowest:.2f}배 (15% 이상 초과)")
            print(f"     → 경쟁이 치열했거나 특수한 요인이 있을 가능성")

    # 2. 감정가 대비 낙찰률 분석
    if appraisal > 0:
        actual_ratio = (actual / appraisal * 100)
        pred_ratio = (predicted / appraisal * 100)

        print(f"\n  • 낙찰률: {actual_ratio:.1f}% (예측: {pred_ratio:.1f}%)")

        if actual_ratio > 80 and auction_round > 1:
            print(f"     ⚠️  {auction_round}회 경매임에도 낙찰률이 {actual_ratio:.1f}%로 높음")
            print(f"     → 물건가치가 높거나, 위치/조건이 좋을 가능성")

    # 3. 입찰자 분석
    bidders = data.get('입찰자수', 0)
    bidders_actual = data.get('입찰자수_실제', 0)

    if bidders_actual and bidders_actual > 3:
        print(f"\n  • 입찰자 {bidders_actual}명 (경쟁 치열)")
        print(f"     → 다수 입찰자로 인한 가격 상승 가능성")

    # 4. 권리/부채 분석
    share_floor = data.get('공유지분_건물', 0)
    share_land = data.get('공유지분_토지', 0)
    debt_ratio = data.get('청구금액비율', 0)

    if share_floor or share_land:
        print(f"\n  • 공유지분: 건물={share_floor}, 토지={share_land}")
        print(f"     → 공유지분이 있지만 낙찰가가 높음 (긍정적 요인 존재)")

    if debt_ratio and debt_ratio > 0.5:
        print(f"\n  • 청구금액비율: {debt_ratio:.2%}")
        print(f"     → 부채비율이 높지만 낙찰가 예측보다 높음")

    print("\n" + "=" * 70)
    print("💡 누락 가능성이 있는 중요 변수")
    print("=" * 70)

    suggestions = [
        {
            "변수": "지역 세부 정보",
            "설명": "역세권, 학군, 상권 등의 위치 프리미엄",
            "예상영향": "10-30% 가격 상승",
            "수집방법": "네이버/카카오 지도 API로 주변 시설 정보 수집"
        },
        {
            "변수": "물건 상태",
            "설명": "리모델링 여부, 층수, 향, 실사용 면적",
            "예상영향": "5-20% 가격 변동",
            "수집방법": "ValueAuction 상세페이지 크롤링"
        },
        {
            "변수": "시장 동향",
            "설명": "해당 지역의 최근 거래가, 시세 동향",
            "예상영향": "10-25% 가격 변동",
            "수집방법": "국토부 실거래가 API 연동"
        },
        {
            "변수": "계절성/타이밍",
            "설명": "경매일자, 요일, 월별 시장 특성",
            "예상영향": "3-10% 가격 변동",
            "수집방법": "경매일자, 계절 특성 추가"
        },
        {
            "변수": "유사 물건 최근 낙찰가",
            "설명": "같은 단지, 인근 지역의 최근 낙찰 사례",
            "예상영향": "15-30% 가격 예측 개선",
            "수집방법": "DB에서 유사 물건 검색 후 특성 추가"
        },
        {
            "변수": "권리분석 상세",
            "설명": "말소기준권리, 인수권리, 유치권 등",
            "예상영향": "10-40% 가격 변동",
            "수집방법": "ValueAuction 권리분석 텍스트 파싱"
        },
        {
            "변수": "평당가 지역 평균",
            "설명": "해당 지역/물건종류의 평균 평당가",
            "예상영향": "10-20% 예측 정확도 개선",
            "수집방법": "DB 집계로 지역별 평균 계산"
        }
    ]

    for i, sug in enumerate(suggestions, 1):
        print(f"\n{i}. {sug['변수']}")
        print(f"   설명: {sug['설명']}")
        print(f"   예상영향: {sug['예상영향']}")
        print(f"   수집방법: {sug['수집방법']}")

    print("\n" + "=" * 70)
    print("📈 즉시 적용 가능한 개선 방안")
    print("=" * 70)

    quick_wins = [
        "1. 유사물건 특성: DB에서 같은 지역, 같은 물건종류의 최근 6개월 낙찰가 평균을 특성으로 추가",
        "2. 경매회차 가중치: 회차가 높을수록 경쟁이 적지만, 일부 물건은 역전 현상 → 물건종류별 회차 가중치 차별화",
        "3. 입찰자수 신뢰도: 입찰자수_실제를 더 강하게 반영 (현재 53개 특성 중 비중 확인 필요)",
        "4. 지역 세분화: '경기'가 아닌 '경기-성남-분당' 수준으로 세분화하여 원-핫 인코딩",
        "5. 시계열 특성: 예측 시점의 최근 1개월 평균 낙찰률을 추가 (시장 열기 반영)",
        "6. 이상치 학습: 현재 오차 15% 이상인 케이스들을 따로 분석하여 패턴 파악"
    ]

    for tip in quick_wins:
        print(f"  {tip}")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    case_no = "2025타경11549"
    if len(sys.argv) > 1:
        case_no = sys.argv[1]

    analyze_case(case_no)
