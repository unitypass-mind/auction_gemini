"""
AI 모델 재훈련 v3 - 최저입찰가 및 권리분석 개선
1. 최저입찰가를 경매회차에 따라 정확히 계산
2. 권리분석 태그 원-핫 인코딩 추가
3. 개선된 특성 엔지니어링
"""
import sqlite3
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import joblib
import logging
import json
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 경로 설정
DB_PATH = "auction_analysis.db"
MODEL_PATH = Path("models/auction_model_v3.pkl")
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)


def calc_lowest_price_by_round(appraisal_price: int, auction_round: int) -> int:
    """
    경매회차에 따른 최저입찰가 계산
    1회: 100%
    2회: 80%
    3회: 64% (80% * 80%)
    4회: 51.2% (64% * 80%)
    """
    ratio = 1.0
    for _ in range(auction_round - 1):
        ratio *= 0.8
    return int(appraisal_price * ratio)


def extract_rights_tags(tags_json: str) -> dict:
    """
    권리사항 태그 JSON에서 원-핫 인코딩 추출
    """
    # 주요 권리사항 태그 목록
    major_tags = {
        '대항력있는임차인': 0,
        '선순위전세권': 0,
        '가압류': 0,
        '가처분': 0,
        '가등기': 0,
        '근저당권': 0,
        '지상권': 0,
        '유치권': 0,
        '전세권': 0
    }

    if not tags_json:
        return major_tags

    try:
        if isinstance(tags_json, str):
            import json
            tags = json.loads(tags_json)
        else:
            tags = tags_json

        if isinstance(tags, list):
            for tag in tags:
                for major_tag in major_tags:
                    if major_tag in tag:
                        major_tags[major_tag] = 1
                        break
    except:
        pass

    return major_tags


def create_features_v3(
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
    debt_ratio: float,
    tags_json: str = None
) -> np.ndarray:
    """
    v3 특성 생성: 최저입찰가 정확 계산 + 권리분석 태그 원-핫
    """
    if bidders_actual is None or bidders_actual < 0:
        bidders_actual = bidders
    if second_price is None or second_price < 0:
        second_price = 0

    features = []

    # ===== 1. 기본 특성 =====
    # 최저입찰가를 경매회차에 따라 정확히 계산
    lowest_bid_price = calc_lowest_price_by_round(start_price, auction_round)
    lowest_price_ratio = lowest_bid_price / start_price if start_price > 0 else 0.8

    평당감정가 = start_price / (area * 0.3025) if area > 0 else 0

    features.extend([
        start_price,                      # 감정가
        np.log1p(start_price),           # 감정가_log
        lowest_bid_price,                 # 최저입찰가 (정확한 계산) ✅
        np.log1p(lowest_bid_price),      # 최저입찰가_log
        lowest_price_ratio,               # 최저가율 (실제 비율) ✅
        bidders_actual,                   # 실제 입찰자수
        np.log1p(bidders_actual),
        bidders_actual / 11.0,
        auction_round,                    # 경매회차
        auction_round ** 2,
        max(0.3, 1 - (auction_round - 1) * 0.15),  # 회차페널티 (더 강하게)
    ])

    # 2. 상호작용 특성
    features.extend([
        np.log1p(start_price) * np.log1p(bidders_actual),
        lowest_price_ratio * bidders_actual,  # 최저가율 x 입찰자
    ])

    # 3. 면적 특성
    features.extend([
        area,
        np.log1p(area),
        평당감정가,
        np.log1p(평당감정가),
        start_price / area if area > 0 else 0,
    ])

    # 4. 지역 인코딩
    region_map = {'경기': 0, '기타': 1, '대구': 2, '부산': 3, '서울': 4, '인천': 5}
    region_idx = region_map.get(region, 1)
    features.append(region_idx)

    # 5. 지역 원-핫
    region_order = ['경기', '기타', '대구', '부산', '서울', '인천']
    for r in region_order:
        features.append(1 if region == r else 0)

    # 6. 물건종류 인코딩
    type_map = {'다세대': 0, '단독주택': 1, '상가': 2, '아파트': 3, '오피스텔': 4}
    type_idx = type_map.get(property_type, 3)
    features.append(type_idx)

    # 7. 물건종류 원-핫
    type_order = ['다세대', '단독주택', '상가', '아파트', '오피스텔']
    for t in type_order:
        features.append(1 if property_type == t else 0)

    # 8. 가격구간 원-핫
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

    # 9. 2등 입찰가 관련
    features.append(second_price)
    features.append(np.log1p(second_price))
    if second_price > 0:
        competition_gap = 1 - (second_price / start_price)
    else:
        competition_gap = 0
    features.append(competition_gap)

    # 10. 권리 관련 (기존)
    features.append(is_hard)
    features.append(tag_count)
    features.append(np.log1p(tag_count))
    risk_score = is_hard * 0.2 + tag_count * 0.05
    features.append(risk_score)

    # ===== 11. 권리분석 태그 원-핫 (신규!) ✅ =====
    rights_tags = extract_rights_tags(tags_json)
    features.extend([
        rights_tags['대항력있는임차인'],
        rights_tags['선순위전세권'],
        rights_tags['가압류'],
        rights_tags['가처분'],
        rights_tags['가등기'],
        rights_tags['근저당권'],
        rights_tags['지상권'],
        rights_tags['유치권'],
        rights_tags['전세권'],
    ])

    # 12. 공유지분
    features.append(share_floor)
    features.append(share_land)

    # 13. 청구금액
    features.append(debt_ratio)
    features.append(debt_ratio ** 2)
    debt_risk = 1 if debt_ratio > 0.7 else 0
    features.append(debt_risk)

    # ===== 14. 고급 특성 (enhanced에서 가져옴) =====
    # 가격 관련
    features.append(np.sqrt(start_price))
    features.append(np.cbrt(start_price))
    price_per_area = start_price / area if area > 0 else 0
    features.append(np.log1p(price_per_area))
    price_tier = np.log10(start_price + 1) / 10
    features.append(price_tier)

    # 입찰 경쟁 고급 특성
    bidder_density = bidders_actual / max(1, auction_round)
    features.append(bidder_density)
    features.append(bidders_actual ** 2)
    second_price_ratio = second_price / start_price if second_price > 0 and start_price > 0 else 0
    features.append(second_price_ratio)
    competition_intensity = (start_price - second_price) / start_price if second_price > 0 else 1.0
    features.append(competition_intensity)
    features.append(np.log1p(bidders_actual) ** 2)
    competition_index = bidders_actual * bidder_density
    features.append(competition_index)

    # 경매회차 고급 특성
    features.append(np.log1p(auction_round))
    features.append(auction_round ** 3)
    round_depreciation = max(0.3, 1 - (auction_round * 0.15))
    features.append(round_depreciation)
    serious_failure = 1 if auction_round >= 3 else 0
    features.append(serious_failure)

    # 면적 고급 특성
    features.append(area ** 2)
    features.append(평당감정가 ** 2)
    is_small = 1 if area < 60 else 0
    is_large = 1 if area > 120 else 0
    features.append(is_small)
    features.append(is_large)
    area_efficiency = area / (np.log1p(start_price) + 1)
    features.append(area_efficiency)

    # 복합 상호작용
    features.append(np.log1p(start_price) * auction_round)
    features.append(np.log1p(start_price) * np.log1p(area))
    features.append(bidders_actual * auction_round)
    features.append(bidders_actual * area)
    features.append(평당감정가 * bidders_actual)
    features.append(auction_round * area)
    features.append(np.log1p(start_price) * bidders_actual * auction_round)
    features.append(bidders_actual * np.log1p(start_price))

    # 권리 및 리스크 고급 특성
    features.append(is_hard * np.log1p(start_price))
    tag_density = tag_count / max(1, auction_round)
    features.append(tag_density)
    total_risk = (is_hard * 0.3 + tag_count * 0.1 + share_floor * 0.2 +
                  share_land * 0.2 + debt_ratio * 0.2)
    features.append(total_risk)
    features.append(is_hard * debt_ratio)
    total_share = share_floor + share_land
    features.append(total_share)
    features.append(total_risk * auction_round)

    # 지역-물건 상호작용
    is_seoul_apt = 1 if (region == '서울' and property_type == '아파트') else 0
    features.append(is_seoul_apt)
    is_gyeonggi_apt = 1 if (region == '경기' and property_type == '아파트') else 0
    features.append(is_gyeonggi_apt)

    # 부채 고급 특성
    features.append(np.log1p(debt_ratio))
    features.append(debt_ratio ** 3)
    high_debt = 1 if debt_ratio > 0.5 else 0
    features.append(high_debt)
    features.append(debt_ratio * bidders_actual)

    # ===== 15. 최저입찰가 관련 신규 특성 ✅ =====
    # 최저입찰가 비율의 변화 추적
    features.append(lowest_price_ratio ** 2)  # 비율 제곱
    features.append(np.log1p(lowest_price_ratio))  # 비율 로그
    # 최저입찰가와 실제 입찰 경쟁의 상호작용
    features.append(lowest_bid_price * bidders_actual)
    features.append(lowest_price_ratio * auction_round)

    # 총 특성 개수: 약 107개
    return np.array(features).reshape(1, -1)


def load_data():
    """DB에서 낙찰 완료 데이터 로드"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # raw_data 컬럼이 있는지 확인
    cursor.execute("PRAGMA table_info(predictions)")
    columns = [col[1] for col in cursor.fetchall()]
    has_raw_data = 'raw_data' in columns

    if has_raw_data:
        query = """
            SELECT
                감정가, 물건종류, 지역, 면적, 경매회차, 입찰자수,
                입찰자수_실제, second_price, 권리분석복잡도, 권리사항태그수,
                공유지분_건물, 공유지분_토지, 청구금액비율,
                raw_data, actual_price
            FROM predictions
            WHERE actual_price IS NOT NULL AND actual_price > 0
        """
    else:
        query = """
            SELECT
                감정가, 물건종류, 지역, 면적, 경매회차, 입찰자수,
                입찰자수_실제, second_price, 권리분석복잡도, 권리사항태그수,
                공유지분_건물, 공유지분_토지, 청구금액비율,
                actual_price
            FROM predictions
            WHERE actual_price IS NOT NULL AND actual_price > 0
        """

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    logger.info(f"로드된 낙찰 데이터: {len(rows)}건")

    if len(rows) == 0:
        raise ValueError("낙찰 데이터가 없습니다. 먼저 데이터를 수집하세요.")

    X = []
    y = []

    for row in rows:
        if has_raw_data:
            (start_price, property_type, region, area, auction_round, bidders,
             bidders_actual, second_price, is_hard, tag_count,
             share_floor, share_land, debt_ratio, raw_data, actual_price) = row
        else:
            (start_price, property_type, region, area, auction_round, bidders,
             bidders_actual, second_price, is_hard, tag_count,
             share_floor, share_land, debt_ratio, actual_price) = row
            raw_data = None

        # v3 특성 생성
        features = create_features_v3(
            start_price, property_type, region, area, auction_round, bidders,
            bidders_actual, second_price, is_hard, tag_count,
            share_floor, share_land, debt_ratio, raw_data
        )

        X.append(features[0])
        y.append(actual_price)

    return np.array(X), np.array(y)


def train_model():
    """모델 훈련 및 저장"""
    logger.info("="*60)
    logger.info("AI 모델 재훈련 v3 시작")
    logger.info("개선 사항:")
    logger.info("  1. 최저입찰가 정확 계산 (경매회차 반영)")
    logger.info("  2. 권리분석 태그 원-핫 인코딩 추가")
    logger.info("  3. 개선된 특성 엔지니어링")
    logger.info("="*60)

    # 데이터 로드
    X, y = load_data()
    logger.info(f"특성 개수: {X.shape[1]}개")
    logger.info(f"학습 데이터: {len(X)}건")

    # 데이터 분할
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    logger.info(f"훈련 세트: {len(X_train)}건, 테스트 세트: {len(X_test)}건")

    # 모델 훈련
    logger.info("\n모델 훈련 중...")

    # RandomForest
    rf_model = RandomForestRegressor(
        n_estimators=200,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )

    # GradientBoosting
    gb_model = GradientBoostingRegressor(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.1,
        random_state=42
    )

    # 앙상블 모델
    model = VotingRegressor([
        ('rf', rf_model),
        ('gb', gb_model)
    ])

    model.fit(X_train, y_train)

    # 평가
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    train_mae = mean_absolute_error(y_train, y_pred_train)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))

    logger.info("\n" + "="*60)
    logger.info("모델 성능")
    logger.info("="*60)
    logger.info(f"훈련 MAE: {train_mae:,.0f}원")
    logger.info(f"테스트 MAE: {test_mae:,.0f}원")
    logger.info(f"훈련 R²: {train_r2:.4f}")
    logger.info(f"테스트 R²: {test_r2:.4f}")
    logger.info(f"테스트 RMSE: {test_rmse:,.0f}원")

    # 에러율 계산
    errors = np.abs(y_test - y_pred_test) / y_test * 100
    avg_error_rate = errors.mean()
    median_error_rate = np.median(errors)
    logger.info(f"평균 에러율: {avg_error_rate:.2f}%")
    logger.info(f"중앙값 에러율: {median_error_rate:.2f}%")

    # 모델 저장
    joblib.dump(model, MODEL_PATH)
    logger.info(f"\n✅ 모델 저장 완료: {MODEL_PATH}")

    # 결과 저장
    results = {
        "model_version": "v3",
        "trained_at": datetime.now().isoformat(),
        "n_features": X.shape[1],
        "n_samples": len(X),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "train_mae": float(train_mae),
        "test_mae": float(test_mae),
        "train_r2": float(train_r2),
        "test_r2": float(test_r2),
        "test_rmse": float(test_rmse),
        "avg_error_rate": float(avg_error_rate),
        "median_error_rate": float(median_error_rate),
        "improvements": [
            "정확한 최저입찰가 계산 (경매회차 반영)",
            "권리분석 태그 원-핫 인코딩",
            "최저입찰가 관련 상호작용 특성 추가"
        ]
    }

    results_path = MODEL_PATH.parent / "training_results_v3.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"✅ 훈련 결과 저장 완료: {results_path}")

    return model, results


if __name__ == "__main__":
    try:
        model, results = train_model()
        logger.info("\n" + "="*60)
        logger.info("✅ 모델 재훈련 완료!")
        logger.info("="*60)
    except Exception as e:
        logger.error(f"❌ 훈련 실패: {e}", exc_info=True)
