"""
AI 모델 훈련 스크립트
경매 낙찰가 예측 모델 생성
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_sample_data(n_samples=1000):
    """
    샘플 데이터 생성

    특성:
    - 감정가 (start_price)
    - 입찰자 수 (bidders)

    타겟:
    - 낙찰가 (final_price)
    """
    np.random.seed(42)

    # 감정가: 1억 ~ 10억 사이
    start_price = np.random.uniform(100_000_000, 1_000_000_000, n_samples)

    # 입찰자 수: 1 ~ 50명
    bidders = np.random.randint(1, 51, n_samples)

    # 낙찰가 계산 (현실적인 패턴 반영)
    # 기본: 감정가의 60~90%
    # 입찰자가 많을수록 낙찰가 상승
    base_rate = np.random.uniform(0.60, 0.90, n_samples)
    bidder_effect = (bidders - 1) * 0.005  # 입찰자 1명당 0.5% 상승
    final_rate = np.clip(base_rate + bidder_effect, 0.5, 1.1)

    # 노이즈 추가
    noise = np.random.normal(0, 0.02, n_samples)
    final_rate = np.clip(final_rate + noise, 0.5, 1.1)

    final_price = start_price * final_rate

    # DataFrame 생성
    df = pd.DataFrame({
        'start_price': start_price,
        'bidders': bidders,
        'final_price': final_price
    })

    logger.info(f"샘플 데이터 생성 완료: {n_samples}건")
    logger.info(f"감정가 범위: {start_price.min():,.0f} ~ {start_price.max():,.0f}원")
    logger.info(f"낙찰가 범위: {final_price.min():,.0f} ~ {final_price.max():,.0f}원")
    logger.info(f"평균 낙찰률: {(final_price / start_price).mean():.2%}")

    return df


def train_models(df):
    """
    여러 모델 훈련 및 평가
    """
    X = df[['start_price', 'bidders']].values
    y = df['final_price'].values

    # 학습/테스트 데이터 분리
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    models = {
        'Linear Regression': LinearRegression(),
        'Random Forest': RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        ),
        'Gradient Boosting': GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
    }

    best_model = None
    best_score = -np.inf
    best_name = None

    logger.info("\n" + "="*50)
    logger.info("모델 훈련 및 평가")
    logger.info("="*50)

    for name, model in models.items():
        logger.info(f"\n[{name}] 훈련 중...")

        # 모델 훈련
        model.fit(X_train, y_train)

        # 예측
        y_pred = model.predict(X_test)

        # 평가
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # 교차 검증
        cv_scores = cross_val_score(
            model, X_train, y_train, cv=5,
            scoring='r2'
        )
        cv_mean = cv_scores.mean()

        logger.info(f"  MAE: {mae:,.0f}원")
        logger.info(f"  R² Score: {r2:.4f}")
        logger.info(f"  CV R² Score: {cv_mean:.4f} (+/- {cv_scores.std():.4f})")

        # 최고 모델 선택
        if r2 > best_score:
            best_score = r2
            best_model = model
            best_name = name

    logger.info("\n" + "="*50)
    logger.info(f"최고 성능 모델: {best_name} (R² = {best_score:.4f})")
    logger.info("="*50)

    return best_model, best_name


def save_model(model, model_path="models/auction_model.pkl"):
    """
    모델 저장
    """
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, model_path)
    logger.info(f"\n모델 저장 완료: {model_path}")

    # 모델 크기 확인
    size_mb = model_path.stat().st_size / (1024 * 1024)
    logger.info(f"모델 크기: {size_mb:.2f} MB")


def test_model(model):
    """
    모델 테스트
    """
    logger.info("\n" + "="*50)
    logger.info("모델 테스트")
    logger.info("="*50)

    test_cases = [
        (300_000_000, 10, "3억원 물건, 입찰자 10명"),
        (500_000_000, 5, "5억원 물건, 입찰자 5명"),
        (1_000_000_000, 30, "10억원 물건, 입찰자 30명"),
        (200_000_000, 2, "2억원 물건, 입찰자 2명"),
    ]

    for start_price, bidders, desc in test_cases:
        predicted = model.predict([[start_price, bidders]])[0]
        rate = (predicted / start_price) * 100

        logger.info(f"\n{desc}")
        logger.info(f"  감정가: {start_price:,}원")
        logger.info(f"  예상 낙찰가: {predicted:,.0f}원")
        logger.info(f"  예상 낙찰률: {rate:.1f}%")


def main():
    """
    메인 함수
    """
    logger.info("AI 모델 훈련 시작")

    # 1. 샘플 데이터 생성
    df = generate_sample_data(n_samples=2000)

    # 데이터 저장
    data_path = Path("data/sample_data.csv")
    data_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(data_path, index=False, encoding='utf-8-sig')
    logger.info(f"샘플 데이터 저장: {data_path}")

    # 2. 모델 훈련
    model, model_name = train_models(df)

    # 3. 모델 저장
    save_model(model)

    # 4. 모델 테스트
    test_model(model)

    logger.info("\n훈련 완료!")


if __name__ == "__main__":
    main()
