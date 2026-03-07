"""
AI 모델 v3 훈련 스크립트 (간소화 버전)
- 현재 테이블 구조 사용
- 경매회차에 따른 정확한 최저입찰가 계산 적용
- 권리분석 태그는 추후 추가 예정
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
MODEL_OUTPUT = "models/auction_model_v3.pkl"


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


def create_features_v3(
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
) -> np.ndarray:
    """
    v3 특성 생성 - 정확한 최저입찰가 계산 반영
    """
    features = []

    # ✅ 핵심 개선: 경매회차에 따른 정확한 최저입찰가 계산
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

    # 이상치 제거 (감정가 대비 낙찰가가 너무 비정상적인 경우)
    df = df[(df['actual_price'] > df['감정가'] * 0.1) & (df['actual_price'] < df['감정가'] * 2)]

    logger.info(f"이상치 제거 후: {len(df)}건")

    return df


def train_model():
    """모델 훈련"""
    # 데이터 로드
    df = load_training_data()

    # 특성 생성
    logger.info("특성 생성 중...")
    X = []
    y = []

    for idx, row in df.iterrows():
        features = create_features_v3(
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
    logger.info("경매 낙찰가 예측 AI 모델 v3 훈련 시작")
    logger.info("개선사항: 경매회차별 정확한 최저입찰가 계산")
    logger.info("="*60)

    model, feature_count = train_model()

    logger.info("\n" + "="*60)
    logger.info("훈련 완료!")
    logger.info("="*60)
