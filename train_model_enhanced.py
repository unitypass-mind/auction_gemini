"""
AI 모델 고도화 (3단계)
1. 특성 엔지니어링 (Feature Engineering)
2. 하이퍼파라미터 튜닝 (Hyperparameter Tuning)
3. 앙상블 모델 (Ensemble Models)
"""
import sys
import io

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import sqlite3
import numpy as np
import warnings
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
import joblib
import logging

warnings.filterwarnings('ignore')

# XGBoost
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logging.warning("XGBoost 없음. 설치 권장: pip install xgboost")

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_PATH = Path("data/predictions.db")
MODEL_PATH = Path("models/auction_model_v2.pkl")


def create_features_enhanced(
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
    고도화된 특성 생성 (기존 48개 + 신규 특성)
    """
    # 기본값 설정
    if bidders_actual is None or bidders_actual == 0:
        bidders_actual = bidders
    if second_price is None or second_price < 0:
        second_price = 0

    features = []

    # ===== STEP 1: 기존 특성 (48개) =====

    # 1. 기존 기본 특성 (11개)
    min_price = start_price * 0.8
    평당감정가 = start_price / (area * 0.3025) if area > 0 else 0

    features.extend([
        start_price,
        np.log1p(start_price),
        min_price,
        np.log1p(min_price),
        0.8,
        bidders_actual,
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

    # 9. 2등 입찰가 관련 (3개)
    features.append(second_price)
    features.append(np.log1p(second_price))
    if second_price > 0:
        competition_gap = 1 - (second_price / start_price)
    else:
        competition_gap = 0
    features.append(competition_gap)

    # 10. 권리 관련 (4개)
    features.append(is_hard)
    features.append(tag_count)
    features.append(np.log1p(tag_count))
    risk_score = is_hard * 0.2 + tag_count * 0.05
    features.append(risk_score)

    # 11. 공유지분 (2개)
    features.append(share_floor)
    features.append(share_land)

    # 12. 청구금액 (3개)
    features.append(debt_ratio)
    features.append(debt_ratio ** 2)
    debt_risk = 1 if debt_ratio > 0.7 else 0
    features.append(debt_risk)

    # ===== STEP 2: 신규 고급 특성 엔지니어링 (추가 특성) =====

    # 13. 가격 관련 고급 특성 (5개)
    # 제곱근 변환
    features.append(np.sqrt(start_price))
    # 세제곱근 변환 (극단값 완화)
    features.append(np.cbrt(start_price))
    # 가격/면적 비율의 로그
    price_per_area = start_price / area if area > 0 else 0
    features.append(np.log1p(price_per_area))
    # 가격대 지수 (고가일수록 높은 값)
    price_tier = np.log10(start_price + 1) / 10
    features.append(price_tier)
    # 감정가 대비 최저입찰가 갭
    price_gap = start_price - min_price
    features.append(np.log1p(price_gap))

    # 14. 입찰 경쟁 고급 특성 (6개)
    # 입찰자 밀도 (회차 대비)
    bidder_density = bidders_actual / max(1, auction_round)
    features.append(bidder_density)
    # 입찰자수 제곱 (많을수록 기하급수적 효과)
    features.append(bidders_actual ** 2)
    # 2등가 비율
    if second_price > 0 and start_price > 0:
        second_price_ratio = second_price / start_price
    else:
        second_price_ratio = 0
    features.append(second_price_ratio)
    # 1-2등 경쟁 강도
    if second_price > 0:
        competition_intensity = (start_price - second_price) / start_price
    else:
        competition_intensity = 1.0
    features.append(competition_intensity)
    # 입찰자 로그 제곱
    features.append(np.log1p(bidders_actual) ** 2)
    # 경쟁률 지수
    competition_index = bidders_actual * bidder_density
    features.append(competition_index)

    # 15. 경매회차 고급 특성 (4개)
    # 회차 로그
    features.append(np.log1p(auction_round))
    # 회차 세제곱 (장기 유찰 페널티)
    features.append(auction_round ** 3)
    # 회차별 가격 감소율 추정
    round_depreciation = 1 - (auction_round * 0.15)
    features.append(max(0.3, round_depreciation))
    # 유찰 심각도 (3회차 이상 = 1)
    serious_failure = 1 if auction_round >= 3 else 0
    features.append(serious_failure)

    # 16. 면적 고급 특성 (5개)
    # 면적 제곱 (대형 물건 프리미엄)
    features.append(area ** 2)
    # 평당가 제곱
    features.append(평당감정가 ** 2)
    # 소형/대형 물건 구분
    is_small = 1 if area < 60 else 0
    is_large = 1 if area > 120 else 0
    features.append(is_small)
    features.append(is_large)
    # 면적 효율성 지수
    area_efficiency = area / (np.log1p(start_price) + 1)
    features.append(area_efficiency)

    # 17. 복합 상호작용 특성 (8개)
    # 가격 x 회차
    features.append(np.log1p(start_price) * auction_round)
    # 가격 x 면적
    features.append(np.log1p(start_price) * np.log1p(area))
    # 입찰자 x 회차
    features.append(bidders_actual * auction_round)
    # 입찰자 x 면적
    features.append(bidders_actual * area)
    # 평당가 x 입찰자
    features.append(평당감정가 * bidders_actual)
    # 회차 x 면적
    features.append(auction_round * area)
    # 3-way 상호작용: 가격 x 입찰자 x 회차
    features.append(np.log1p(start_price) * bidders_actual * auction_round)
    # 경쟁도 x 가격
    features.append(bidders_actual * np.log1p(start_price))

    # 18. 권리 및 리스크 고급 특성 (6개)
    # 권리 복잡도 x 가격
    features.append(is_hard * np.log1p(start_price))
    # 태그 밀도
    tag_density = tag_count / max(1, auction_round)
    features.append(tag_density)
    # 종합 리스크 점수
    total_risk = (is_hard * 0.3 +
                  tag_count * 0.1 +
                  share_floor * 0.2 +
                  share_land * 0.2 +
                  debt_ratio * 0.2)
    features.append(total_risk)
    # 권리 x 부채 복합 리스크
    features.append(is_hard * debt_ratio)
    # 공유지분 종합
    total_share = share_floor + share_land
    features.append(total_share)
    # 리스크 x 회차
    features.append(total_risk * auction_round)

    # 19. 지역-물건 상호작용 (2개)
    # 서울 x 아파트
    is_seoul_apt = 1 if (region == '서울' and property_type == '아파트') else 0
    features.append(is_seoul_apt)
    # 경기 x 아파트
    is_gyeonggi_apt = 1 if (region == '경기' and property_type == '아파트') else 0
    features.append(is_gyeonggi_apt)

    # 20. 부채 고급 특성 (4개)
    # 부채비율 로그
    features.append(np.log1p(debt_ratio))
    # 부채비율 세제곱
    features.append(debt_ratio ** 3)
    # 고부채 여부 (50% 이상)
    high_debt = 1 if debt_ratio > 0.5 else 0
    features.append(high_debt)
    # 부채 x 입찰자 (부채 높아도 인기 많으면 괜찮음)
    features.append(debt_ratio * bidders_actual)

    # 총 특성 개수: 48 (기존) + 45 (신규) = 93개
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

        # 고도화된 특성 생성
        features = create_features_enhanced(
            start_price, property_type, region, area, auction_round, bidders,
            bidders_actual, second_price, is_hard, tag_count,
            share_floor, share_land, debt_ratio
        )

        X.append(features[0])
        y.append(actual_price)

    return np.array(X), np.array(y)


def train_with_hyperparameter_tuning(X_train, y_train, X_test, y_test):
    """
    STEP 2: 하이퍼파라미터 튜닝
    """
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: 하이퍼파라미터 튜닝")
    logger.info("=" * 80)

    # RandomForest 튜닝
    logger.info("\nRandomForest 하이퍼파라미터 튜닝 중...")

    param_grid_rf = {
        'n_estimators': [200, 300],
        'max_depth': [15, 20, 25],
        'min_samples_split': [3, 5],
        'min_samples_leaf': [1, 2],
        'max_features': ['sqrt', 'log2']
    }

    rf_base = RandomForestRegressor(random_state=42, n_jobs=-1)

    grid_search_rf = GridSearchCV(
        rf_base,
        param_grid_rf,
        cv=5,
        scoring='neg_mean_absolute_error',
        n_jobs=-1,
        verbose=1
    )

    grid_search_rf.fit(X_train, y_train)

    best_rf = grid_search_rf.best_estimator_
    logger.info(f"최적 파라미터: {grid_search_rf.best_params_}")

    # 성능 평가
    rf_pred = best_rf.predict(X_test)
    rf_mae = mean_absolute_error(y_test, rf_pred)
    rf_r2 = r2_score(y_test, rf_pred)
    rf_errors = np.abs(rf_pred - y_test) / y_test * 100

    logger.info(f"튜닝된 RandomForest - MAE: {rf_mae:,.0f}원, R²: {rf_r2:.4f}, 오차율: {rf_errors.mean():.2f}%")

    return best_rf, rf_errors.mean()


def train_ensemble_models(X_train, y_train, X_test, y_test, tuned_rf):
    """
    STEP 3: 앙상블 모델
    """
    logger.info("\n" + "=" * 80)
    logger.info("STEP 3: 앙상블 모델")
    logger.info("=" * 80)

    estimators = [('rf', tuned_rf)]
    model_results = {'RandomForest (Tuned)': tuned_rf}

    # GradientBoosting
    logger.info("\nGradientBoosting 학습 중...")
    gb_model = GradientBoostingRegressor(
        n_estimators=300,
        max_depth=7,
        learning_rate=0.05,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42
    )
    gb_model.fit(X_train, y_train)
    gb_pred = gb_model.predict(X_test)
    gb_mae = mean_absolute_error(y_test, gb_pred)
    gb_r2 = r2_score(y_test, gb_pred)
    gb_errors = np.abs(gb_pred - y_test) / y_test * 100
    logger.info(f"GradientBoosting - MAE: {gb_mae:,.0f}원, R²: {gb_r2:.4f}, 오차율: {gb_errors.mean():.2f}%")

    estimators.append(('gb', gb_model))
    model_results['GradientBoosting'] = gb_model

    # XGBoost
    if XGBOOST_AVAILABLE:
        logger.info("\nXGBoost 학습 중...")
        xgb_model = xgb.XGBRegressor(
            n_estimators=300,
            max_depth=7,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        xgb_model.fit(X_train, y_train)
        xgb_pred = xgb_model.predict(X_test)
        xgb_mae = mean_absolute_error(y_test, xgb_pred)
        xgb_r2 = r2_score(y_test, xgb_pred)
        xgb_errors = np.abs(xgb_pred - y_test) / y_test * 100
        logger.info(f"XGBoost - MAE: {xgb_mae:,.0f}원, R²: {xgb_r2:.4f}, 오차율: {xgb_errors.mean():.2f}%")

        estimators.append(('xgb', xgb_model))
        model_results['XGBoost'] = xgb_model

    # Voting Ensemble
    logger.info(f"\nVoting Ensemble 생성 ({len(estimators)}개 모델)...")
    voting_model = VotingRegressor(estimators=estimators)
    voting_model.fit(X_train, y_train)

    voting_pred = voting_model.predict(X_test)
    voting_mae = mean_absolute_error(y_test, voting_pred)
    voting_r2 = r2_score(y_test, voting_pred)
    voting_errors = np.abs(voting_pred - y_test) / y_test * 100

    logger.info("\n" + "=" * 80)
    logger.info("앙상블 최종 성능")
    logger.info("=" * 80)
    logger.info(f"Voting Ensemble - MAE: {voting_mae:,.0f}원, R²: {voting_r2:.4f}, 오차율: {voting_errors.mean():.2f}%")
    logger.info("=" * 80)

    return voting_model, voting_errors.mean(), model_results


def train_model_enhanced():
    """고도화 모델 학습 (3단계 통합)"""
    logger.info("=" * 80)
    logger.info("AI 모델 고도화 시작")
    logger.info("1단계: 특성 엔지니어링 (93개 특성)")
    logger.info("2단계: 하이퍼파라미터 튜닝")
    logger.info("3단계: 앙상블 모델")
    logger.info("=" * 80)

    # STEP 1: 특성 엔지니어링 (데이터 로드)
    logger.info("\nSTEP 1: 고급 특성 엔지니어링")
    X, y = load_data()
    logger.info(f"특성 개수: {X.shape[1]}개 (기존 48개 → 고도화 93개)")
    logger.info(f"학습 데이터: {X.shape[0]}건")

    # Train/Test 분리
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    logger.info(f"훈련: {len(X_train)}건, 테스트: {len(X_test)}건")

    # STEP 2: 하이퍼파라미터 튜닝
    tuned_rf, rf_error_rate = train_with_hyperparameter_tuning(
        X_train, y_train, X_test, y_test
    )

    # STEP 3: 앙상블 모델
    ensemble_model, ensemble_error_rate, individual_models = train_ensemble_models(
        X_train, y_train, X_test, y_test, tuned_rf
    )

    # 최종 모델 저장 (Voting Ensemble)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(ensemble_model, MODEL_PATH)
    logger.info(f"\n최종 모델 저장: {MODEL_PATH}")

    # 개별 모델도 저장 (백업)
    for name, model in individual_models.items():
        model_name = name.replace(' ', '_').replace('(', '').replace(')', '')
        backup_path = Path(f"models/backup_{model_name}.pkl")
        joblib.dump(model, backup_path)
        logger.info(f"백업 저장: {backup_path}")

    logger.info("\n" + "=" * 80)
    logger.info("✅ 모델 고도화 완료!")
    logger.info(f"최종 오차율: {ensemble_error_rate:.2f}%")
    logger.info("=" * 80)

    return ensemble_model, ensemble_error_rate


if __name__ == "__main__":
    model, avg_error = train_model_enhanced()
    print(f"\n🎉 고도화 완료! 최종 평균 오차율: {avg_error:.2f}%")
