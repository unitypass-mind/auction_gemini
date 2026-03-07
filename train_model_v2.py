"""
AI 모델 재학습 (신규 변수 포함)
"""
import sqlite3
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import logging
import sys
import io

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = Path("data/predictions.db")
MODEL_PATH = Path("models/auction_model_v2.pkl")


def create_features_v2(
    start_price: int,
    property_type: str,
    region: str,
    area: float,
    auction_round: int,
    bidders: int,
    bidders_actual: int,
    second_price: int,
    is_hard: int,
    tag_count: int,
    share_floor: int,
    share_land: int,
    debt_ratio: float
) -> np.ndarray:
    """
    신규 변수를 포함한 특성 생성 (48개 특성)
    """
    # 기본값 설정
    if bidders_actual is None or bidders_actual == 0:
        bidders_actual = bidders
    if second_price is None or second_price < 0:
        second_price = 0

    features = []

    # 1. 기존 기본 특성 (11개)
    min_price = start_price * 0.8
    평당감정가 = start_price / (area * 0.3025) if area > 0 else 0

    features.extend([
        start_price,
        np.log1p(start_price),
        min_price,
        np.log1p(min_price),
        0.8,
        bidders_actual,  # 실제 입찰자수 사용
        np.log1p(bidders_actual),
        bidders_actual / 11.0,
        auction_round,
        auction_round ** 2,
        max(0.5, 1 - (auction_round - 1) * 0.1),
    ])

    # 2. 상호작용 특성 (2개)
    features.extend([
        np.log1p(start_price) * np.log1p(bidders_actual),
        0.8 * bidders_actual,
    ])

    # 3. 면적 특성 (5개)
    features.extend([
        area,
        np.log1p(area),
        평당감정가,
        np.log1p(평당감정가),
        np.log1p(area) * np.log1p(bidders_actual),
    ])

    # 4. 지역 인코딩 (1개)
    region_map = {'경기': 0, '기타': 1, '대구': 2, '부산': 3, '서울': 4, '인천': 5}
    region_idx = region_map.get(region, 1)
    features.append(region_idx)

    # 5. 지역 원-핫 (6개)
    region_order = ['경기', '기타', '대구', '부산', '서울', '인천']
    for r in region_order:
        features.append(1 if region == r else 0)

    # 6. 물건종류 인코딩 (1개)
    type_map = {'다세대': 0, '단독주택': 1, '상가': 2, '아파트': 3, '오피스텔': 4}
    type_idx = type_map.get(property_type, 3)
    features.append(type_idx)

    # 7. 물건종류 원-핫 (5개)
    type_order = ['다세대', '단독주택', '상가', '아파트', '오피스텔']
    for t in type_order:
        features.append(1 if property_type == t else 0)

    # 8. 가격구간 원-핫 (5개)
    if start_price <= 100_000_000:
        price_range = [1, 0, 0, 0, 0]
    elif start_price <= 300_000_000:
        price_range = [0, 1, 0, 0, 0]
    elif start_price <= 500_000_000:
        price_range = [0, 0, 1, 0, 0]
    elif start_price <= 1_000_000_000:
        price_range = [0, 0, 0, 1, 0]
    else:
        price_range = [0, 0, 0, 0, 1]
    features.extend(price_range)

    # ===== 신규 변수 (12개) =====

    # 9. 2등 입찰가 관련 (3개)
    features.append(second_price)
    features.append(np.log1p(second_price))
    # 경쟁 강도 (1등-2등 차이)
    if second_price > 0:
        competition_gap = 1 - (second_price / start_price)
    else:
        competition_gap = 0
    features.append(competition_gap)

    # 10. 권리 관련 (4개)
    features.append(is_hard)
    features.append(tag_count)
    features.append(np.log1p(tag_count))
    # 권리 리스크 점수
    risk_score = is_hard * 0.2 + tag_count * 0.05
    features.append(risk_score)

    # 11. 공유지분 (2개)
    features.append(share_floor)
    features.append(share_land)

    # 12. 청구금액 (3개)
    features.append(debt_ratio)
    features.append(debt_ratio ** 2)
    # 부채 위험 지표
    debt_risk = 1 if debt_ratio > 0.7 else 0
    features.append(debt_risk)

    return np.array(features).reshape(1, -1)


def load_data():
    """DB에서 검증된 데이터 로드"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            감정가, 물건종류, 지역, 면적, 경매회차, 입찰자수,
            입찰자수_실제, second_price, 권리분석복잡도, 권리사항태그수,
            공유지분_건물, 공유지분_토지, 청구금액비율,
            actual_price
        FROM predictions
        WHERE verified = 1 AND actual_price > 0
    """)

    data = cursor.fetchall()
    conn.close()

    logger.info(f"검증된 데이터 {len(data)}건 로드")

    X = []
    y = []

    for row in data:
        (start_price, property_type, region, area, auction_round, bidders,
         bidders_actual, second_price, is_hard, tag_count,
         share_floor, share_land, debt_ratio, actual_price) = row

        # 특성 생성
        features = create_features_v2(
            start_price, property_type, region, area, auction_round, bidders,
            bidders_actual, second_price, is_hard, tag_count,
            share_floor, share_land, debt_ratio
        )

        X.append(features[0])
        y.append(actual_price)

    return np.array(X), np.array(y)


def train_model():
    """모델 학습"""
    logger.info("=" * 60)
    logger.info("AI 모델 재학습 시작 (신규 변수 포함)")
    logger.info("=" * 60)

    # 데이터 로드
    X, y = load_data()
    logger.info(f"특성 개수: {X.shape[1]}개")
    logger.info(f"학습 데이터: {X.shape[0]}건")

    # Train/Test 분리
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    logger.info(f"훈련: {len(X_train)}건, 테스트: {len(X_test)}건")

    # 모델 학습
    logger.info("\n모델 학습 중...")
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)
    logger.info("모델 학습 완료!")

    # 평가
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)

    train_mae = mean_absolute_error(y_train, train_pred)
    test_mae = mean_absolute_error(y_test, test_pred)

    train_r2 = r2_score(y_train, train_pred)
    test_r2 = r2_score(y_test, test_pred)

    # 오차율 계산
    train_errors = np.abs(train_pred - y_train) / y_train * 100
    test_errors = np.abs(test_pred - y_test) / y_test * 100

    logger.info("\n" + "=" * 60)
    logger.info("모델 성능")
    logger.info("=" * 60)
    logger.info(f"Train MAE: {train_mae:,.0f}원")
    logger.info(f"Test MAE:  {test_mae:,.0f}원")
    logger.info(f"Train R²:  {train_r2:.4f}")
    logger.info(f"Test R²:   {test_r2:.4f}")
    logger.info(f"Train 평균 오차율: {train_errors.mean():.2f}%")
    logger.info(f"Test 평균 오차율:  {test_errors.mean():.2f}%")
    logger.info("=" * 60)

    # 특성 중요도
    feature_importance = model.feature_importances_
    top_10_idx = np.argsort(feature_importance)[-10:][::-1]

    logger.info("\nTop 10 중요 특성:")
    for idx in top_10_idx:
        logger.info(f"  특성 {idx}: {feature_importance[idx]:.4f}")

    # 모델 저장
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    logger.info(f"\n모델 저장: {MODEL_PATH}")

    return model, test_errors.mean()


if __name__ == "__main__":
    model, avg_error = train_model()
    print(f"\n✅ 재학습 완료! 테스트 평균 오차율: {avg_error:.2f}%")
