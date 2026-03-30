"""
AI 모델 v4 훈련 스크립트
- v3 기반 + 과거 패턴 특성 추가
- 물건종류 × 경매회차 패턴
- 지역별 평균 낙찰률
- 복합 패턴 (지역 × 물건 × 회차)
"""
import sqlite3
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "data/predictions.db"
MODEL_OUTPUT = "models/auction_model_v4.pkl"

# 패턴 테이블 경로
PATTERN_PROPERTY_ROUND = "models/pattern_property_round.pkl"
PATTERN_REGION = "models/pattern_region.pkl"
PATTERN_COMPLEX = "models/pattern_complex.pkl"


def calc_lowest_price_by_round(appraisal_price: int, auction_round: int) -> int:
    """
    경매회차에 따른 최저입찰가 계산
    1회: 100%
    2회: 80%  (0.8)
    3회: 64%  (0.8 * 0.8)
    4회: 51.2% (0.8 * 0.8 * 0.8)
    """
    ratio = 1.0
    for _ in range(auction_round - 1):
        ratio *= 0.8
    return int(appraisal_price * ratio)


def create_features_v4(
    start_price: int,
    property_type: str,
    region: str,
    area: float,
    auction_round: int,
    bidders: int,
    bidders_actual: int = None,
    share_floor: float = 0,
    share_land: float = 0,
    debt_ratio: float = 0,
    second_price: int = 0,
    pattern_property_round: dict = None,
    pattern_region: dict = None,
    pattern_complex: dict = None,
    lowest_bid_price: int = None,  # ValueAuction API에서 받은 실제 최저입찰가
) -> np.ndarray:
    """
    v4 특성 생성 - v3 + 과거 패턴 특성 추가
    특성 개수: 53 (v3) + 5 (패턴) = 58개

    Args:
        lowest_bid_price: ValueAuction API에서 받은 법원의 실제 최저입찰가
                         (None이면 경매회차에 따라 자동 계산)
    """
    features = []

    # ✅ 핵심 개선: ValueAuction API에서 받은 실제 최저입찰가 사용
    if lowest_bid_price is None or lowest_bid_price == 0:
        # fallback: API에서 못 받았을 경우에만 계산
        lowest_bid_price = calc_lowest_price_by_round(start_price, auction_round)

    lowest_price_ratio = lowest_bid_price / start_price if start_price > 0 else 0.8

    if bidders_actual is None:
        bidders_actual = bidders

    # 1. 기본 가격 특성 (로그 변환 포함)
    features.extend([
        start_price,
        np.log1p(start_price),
        lowest_bid_price,          # ✅ 정확한 최저입찰가
        np.log1p(lowest_bid_price),
        lowest_price_ratio,        # ✅ 실제 비율 (0.8, 0.64, 0.512 등)
    ])

    # 2. 물건 종류 (원-핫 인코딩)
    property_types = ['아파트', '다세대', '단독주택', '오피스텔', '토지', '상가', '기타']
    for ptype in property_types:
        features.append(1 if ptype in property_type else 0)

    # 3. 지역 (원-핫 인코딩 - 주요 지역만)
    regions = ['서울', '경기', '인천', '부산', '대구', '대전', '광주', '울산', '세종', '기타']
    region_matched = False
    for reg in regions[:-1]:
        if reg in region:
            features.append(1)
            region_matched = True
        else:
            features.append(0)
    features.append(0 if region_matched else 1)  # 기타

    # 4. 면적 관련 특성
    features.extend([
        area,
        np.log1p(area),
        start_price / area if area > 0 else 0,  # 평당가
        np.log1p(start_price / area) if area > 0 else 0,
    ])

    # 5. 경매 진행 상황
    features.extend([
        auction_round,
        np.log1p(auction_round),
        bidders,
        bidders_actual,
        np.log1p(bidders_actual),
    ])

    # 6. 공유지분 & 부채
    features.extend([
        share_floor,
        share_land,
        debt_ratio,
        np.log1p(debt_ratio),
    ])

    # 7. 2순위 가격 (음수 처리)
    second_price_safe = max(0, second_price)  # 음수 방지
    features.extend([
        second_price_safe,
        np.log1p(second_price_safe),
        second_price_safe / start_price if start_price > 0 and second_price_safe > 0 else 0,
    ])

    # 8. ✅ 최저입찰가 상호작용 특성 (NEW)
    features.extend([
        lowest_price_ratio * auction_round,           # 가율 x 회차
        lowest_price_ratio * bidders_actual,          # 가율 x 입찰자
        lowest_bid_price * bidders_actual,            # 최저가 x 입찰자
        np.log1p(lowest_price_ratio * auction_round),
    ])

    # 9. 고급 상호작용 특성
    features.extend([
        start_price * auction_round,
        start_price * bidders_actual,
        area * auction_round,
        (start_price / area if area > 0 else 0) * auction_round,  # 평당가 x 회차
        bidders_actual / auction_round if auction_round > 0 else bidders_actual,  # 회차당 입찰자
        share_floor + share_land,  # 총 공유지분
        debt_ratio * auction_round,
    ])

    # 10. 다항 특성
    features.extend([
        start_price ** 2,
        area ** 2,
        auction_round ** 2,
        bidders_actual ** 2,
    ])

    # ====================
    # 11. 과거 패턴 특성 (v4 NEW)
    # ====================

    # 물건종류 정규화
    property_category = '기타'
    if '아파트' in property_type:
        property_category = '아파트'
    elif '오피스텔' in property_type:
        property_category = '오피스텔'
    elif '다세대' in property_type or '연립' in property_type:
        property_category = '다세대'
    elif '단독' in property_type:
        property_category = '단독주택'
    elif '상가' in property_type or '점포' in property_type:
        property_category = '상가'
    elif '토지' in property_type:
        property_category = '토지'

    # 지역 그룹핑
    region_group = '기타'
    for r in ['서울', '경기', '인천', '부산', '대구', '대전', '광주', '울산', '세종', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']:
        if r in region:
            region_group = r
            break

    # 패턴 1: 물건종류 × 경매회차
    pattern_pr_key = f"{property_category}_{auction_round}"
    pattern_pr_ratio = 0.5  # 기본값
    if pattern_property_round and pattern_pr_key in pattern_property_round:
        pattern_pr_ratio = pattern_property_round[pattern_pr_key]['avg_ratio']

    # 패턴 2: 지역별 평균
    region_avg_ratio = 0.5  # 기본값
    if pattern_region and region_group in pattern_region:
        region_avg_ratio = pattern_region[region_group]['avg_ratio']

    # 패턴 3: 복합 패턴 (지역 × 물건 × 회차)
    pattern_complex_key = f"{region_group}_{property_category}_{auction_round}"
    pattern_complex_ratio = 0.5  # 기본값
    if pattern_complex and pattern_complex_key in pattern_complex:
        pattern_complex_ratio = pattern_complex[pattern_complex_key]['avg_ratio']

    # 패턴 특성 추가 (5개)
    features.extend([
        pattern_pr_ratio,                                    # 1. 물건×회차 평균
        region_avg_ratio,                                    # 2. 지역 평균
        pattern_complex_ratio,                               # 3. 복합 패턴
        pattern_pr_ratio * region_avg_ratio,                 # 4. 패턴 상호작용
        abs(pattern_pr_ratio - region_avg_ratio),            # 5. 패턴 차이
    ])

    # NaN, Inf 값 처리
    features_array = np.array(features, dtype=np.float64)
    features_array = np.nan_to_num(features_array, nan=0.0, posinf=0.0, neginf=0.0)

    return features_array


def load_training_data():
    """데이터베이스에서 훈련 데이터 로드"""
    logger.info(f"데이터베이스 로드: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)

    # 낙찰 데이터만 조회 (actual_price > 0)
    query = """
        SELECT
            감정가, 물건종류, 지역, 면적, 경매회차, 입찰자수,
            입찰자수_실제, 공유지분_건물, 공유지분_토지, 청구금액비율,
            second_price, actual_price
        FROM predictions
        WHERE actual_price IS NOT NULL AND actual_price > 0
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    logger.info(f"로드된 데이터: {len(df)}건")

    # 결측치 처리
    df['입찰자수_실제'] = df['입찰자수_실제'].fillna(df['입찰자수'])
    df['공유지분_건물'] = df['공유지분_건물'].fillna(0)
    df['공유지분_토지'] = df['공유지분_토지'].fillna(0)
    df['청구금액비율'] = df['청구금액비율'].fillna(0)
    df['second_price'] = df['second_price'].fillna(0)

    # 이상치 제거 강화 (감정가 대비 낙찰가 40~105% 범위만 허용)
    # 극단적인 저가 낙찰(<40%)이나 감정가 초과(>105%)는 모델 성능 저하 원인
    df = df[(df['actual_price'] > df['감정가'] * 0.4) & (df['actual_price'] < df['감정가'] * 1.05)]

    logger.info(f"이상치 제거 후: {len(df)}건")

    return df


def train_model():
    """모델 훈련 (v4)"""
    # 패턴 테이블 로드
    logger.info("패턴 테이블 로드 중...")
    pattern_property_round = joblib.load(PATTERN_PROPERTY_ROUND)
    pattern_region = joblib.load(PATTERN_REGION)
    pattern_complex = joblib.load(PATTERN_COMPLEX)
    logger.info(f"  - 물건×회차 패턴: {len(pattern_property_round)}개")
    logger.info(f"  - 지역 패턴: {len(pattern_region)}개")
    logger.info(f"  - 복합 패턴: {len(pattern_complex)}개")

    # 데이터 로드
    df = load_training_data()

    # 특성 생성
    logger.info("특성 생성 중 (v4)...")
    X = []
    y = []

    for idx, row in df.iterrows():
        features = create_features_v4(
            start_price=row['감정가'],
            property_type=str(row['물건종류']),
            region=str(row['지역']),
            area=row['면적'],
            auction_round=row['경매회차'],
            bidders=row['입찰자수'],
            bidders_actual=row['입찰자수_실제'],
            share_floor=row['공유지분_건물'],
            share_land=row['공유지분_토지'],
            debt_ratio=row['청구금액비율'],
            second_price=row['second_price'],
            pattern_property_round=pattern_property_round,
            pattern_region=pattern_region,
            pattern_complex=pattern_complex,
        )
        X.append(features)
        y.append(row['actual_price'])

    X = np.array(X)
    y = np.array(y)

    logger.info(f"특성 개수: {X.shape[1]}개")
    logger.info(f"훈련 샘플: {len(X)}개")

    # 데이터 분할
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 모델 앙상블
    logger.info("모델 훈련 중...")

    rf = RandomForestRegressor(
        n_estimators=200,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )

    gb = GradientBoostingRegressor(
        n_estimators=200,
        max_depth=10,
        learning_rate=0.1,
        random_state=42
    )

    voting = VotingRegressor([
        ('rf', rf),
        ('gb', gb),
    ])

    voting.fit(X_train, y_train)

    # 평가
    logger.info("\n" + "="*60)
    logger.info("모델 평가")
    logger.info("="*60)

    train_pred = voting.predict(X_train)
    test_pred = voting.predict(X_test)

    train_mae = mean_absolute_error(y_train, train_pred)
    test_mae = mean_absolute_error(y_test, test_pred)
    train_r2 = r2_score(y_train, train_pred)
    test_r2 = r2_score(y_test, test_pred)

    logger.info(f"훈련 MAE: {train_mae:,.0f}원")
    logger.info(f"테스트 MAE: {test_mae:,.0f}원")
    logger.info(f"훈련 R²: {train_r2:.4f}")
    logger.info(f"테스트 R²: {test_r2:.4f}")

    # 오차율 계산
    train_error_rate = np.mean(np.abs((y_train - train_pred) / y_train) * 100)
    test_error_rate = np.mean(np.abs((y_test - test_pred) / y_test) * 100)

    logger.info(f"훈련 평균 오차율: {train_error_rate:.2f}%")
    logger.info(f"테스트 평균 오차율: {test_error_rate:.2f}%")

    # 샘플 예측 비교
    logger.info("\n샘플 예측 비교 (테스트 데이터 처음 5개):")
    for i in range(min(5, len(y_test))):
        error_pct = abs(y_test[i] - test_pred[i]) / y_test[i] * 100
        logger.info(f"  실제: {y_test[i]:>12,.0f}원 | 예측: {test_pred[i]:>12,.0f}원 | 오차: {error_pct:>5.2f}%")

    # 모델 저장
    Path(MODEL_OUTPUT).parent.mkdir(exist_ok=True)
    joblib.dump(voting, MODEL_OUTPUT)
    logger.info(f"\n모델 저장 완료: {MODEL_OUTPUT}")
    logger.info(f"특성 개수: {X.shape[1]}개")

    return voting, X.shape[1]


if __name__ == "__main__":
    logger.info("="*60)
    logger.info("경매 낙찰가 예측 AI 모델 v4 훈련 시작")
    logger.info("개선사항:")
    logger.info("  - v3 기반 (정확한 최저입찰가 계산)")
    logger.info("  - 물건종류 × 경매회차 과거 패턴")
    logger.info("  - 지역별 과거 평균 낙찰률")
    logger.info("  - 복합 패턴 (지역 × 물건 × 회차)")
    logger.info("="*60)

    model, feature_count = train_model()

    logger.info("\n" + "="*60)
    logger.info("v4 모델 훈련 완료!")
    logger.info("="*60)
