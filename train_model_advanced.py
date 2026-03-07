"""
고급 AI 모델 훈련 스크립트
실제 경매 데이터 기반 낙찰가 예측 모델
- 여러 알고리즘 비교
- 하이퍼파라미터 튜닝
- 앙상블 모델
- 특성 중요도 분석
"""
import numpy as np
import pandas as pd
from pathlib import Path
import logging
import joblib
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Scikit-learn
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, RandomizedSearchCV
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    VotingRegressor,
    StackingRegressor
)
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    mean_absolute_percentage_error
)
from sklearn.preprocessing import StandardScaler

# XGBoost & LightGBM
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logging.warning("XGBoost 없음, 설치 권장: pip install xgboost")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logging.warning("LightGBM 없음, 설치 권장: pip install lightgbm")

# Visualization
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    VISUALIZATION_AVAILABLE = True
    plt.rcParams['font.family'] = 'Malgun Gothic'  # 한글 폰트
    plt.rcParams['axes.unicode_minus'] = False
except ImportError:
    VISUALIZATION_AVAILABLE = False
    logging.warning("시각화 라이브러리 없음")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdvancedAuctionModel:
    """고급 경매 예측 모델"""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.models = {}
        self.results = {}
        self.best_model = None
        self.best_model_name = None
        self.feature_importance = None
        self.scaler = StandardScaler()

    def load_data(self) -> tuple:
        """전처리된 데이터 로드"""
        logger.info("데이터 로드 중...")

        data_dir = Path("data")

        # 전처리된 데이터 확인
        X_file = data_dir / "X_features.npy"
        y_file = data_dir / "y_target.npy"

        if X_file.exists() and y_file.exists():
            X = np.load(X_file, allow_pickle=True)
            y = np.load(y_file, allow_pickle=True)
            logger.info(f"전처리된 데이터 로드: X{X.shape}, y{y.shape}")
        else:
            # CSV에서 직접 로드
            csv_file = data_dir / "auction_data.csv"
            if not csv_file.exists():
                raise FileNotFoundError(f"데이터 파일 없음: {csv_file}")

            df = pd.read_csv(csv_file, encoding='utf-8-sig')
            logger.info(f"CSV 데이터 로드: {len(df)}건")

            # 기본 특성만 사용
            X = df[['감정가', '입찰자수']].values
            y = df['낙찰가'].values

            # 추가 특성이 있으면 포함
            if '경매회차' in df.columns:
                X = np.column_stack([X, df['경매회차'].values])
            if '면적' in df.columns:
                X = np.column_stack([X, df['면적'].values])

            logger.info(f"특성 추출 완료: X{X.shape}, y{y.shape}")

        return X, y

    def prepare_data(self, X, y, test_size: float = 0.2):
        """데이터 분할 및 스케일링"""
        logger.info("데이터 분할 및 스케일링...")

        # Train/Test 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=self.random_state,
            shuffle=True
        )

        logger.info(f"Train: {X_train.shape}, Test: {X_test.shape}")

        return X_train, X_test, y_train, y_test

    def initialize_models(self):
        """모델 초기화"""
        logger.info("모델 초기화 중...")

        self.models = {
            'Linear Regression': LinearRegression(),

            'Ridge': Ridge(
                alpha=100.0,
                random_state=self.random_state
            ),

            'Lasso': Lasso(
                alpha=1000.0,
                random_state=self.random_state,
                max_iter=10000
            ),

            'ElasticNet': ElasticNet(
                alpha=1000.0,
                l1_ratio=0.5,
                random_state=self.random_state,
                max_iter=10000
            ),

            'Random Forest': RandomForestRegressor(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=self.random_state,
                n_jobs=-1
            ),

            'Gradient Boosting': GradientBoostingRegressor(
                n_estimators=200,
                max_depth=7,
                learning_rate=0.05,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=self.random_state
            ),
        }

        # XGBoost
        if XGBOOST_AVAILABLE:
            self.models['XGBoost'] = xgb.XGBRegressor(
                n_estimators=200,
                max_depth=7,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=self.random_state,
                n_jobs=-1
            )

        # LightGBM
        if LIGHTGBM_AVAILABLE:
            self.models['LightGBM'] = lgb.LGBMRegressor(
                n_estimators=200,
                max_depth=7,
                learning_rate=0.05,
                num_leaves=31,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=self.random_state,
                n_jobs=-1,
                verbose=-1
            )

        logger.info(f"{len(self.models)}개 모델 초기화 완료")

    def evaluate_model(self, name, model, X_train, X_test, y_train, y_test):
        """모델 평가"""
        # 훈련
        model.fit(X_train, y_train)

        # 예측
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)

        # 평가 지표
        train_mae = mean_absolute_error(y_train, y_train_pred)
        test_mae = mean_absolute_error(y_test, y_test_pred)

        train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))

        train_r2 = r2_score(y_train, y_train_pred)
        test_r2 = r2_score(y_test, y_test_pred)

        # MAPE (Mean Absolute Percentage Error)
        train_mape = mean_absolute_percentage_error(y_train, y_train_pred) * 100
        test_mape = mean_absolute_percentage_error(y_test, y_test_pred) * 100

        # 교차 검증 (시간이 오래 걸릴 수 있음)
        try:
            cv_scores = cross_val_score(
                model, X_train, y_train,
                cv=5,
                scoring='r2',
                n_jobs=-1
            )
            cv_mean = cv_scores.mean()
            cv_std = cv_scores.std()
        except:
            cv_mean = None
            cv_std = None

        results = {
            'train_mae': train_mae,
            'test_mae': test_mae,
            'train_rmse': train_rmse,
            'test_rmse': test_rmse,
            'train_r2': train_r2,
            'test_r2': test_r2,
            'train_mape': train_mape,
            'test_mape': test_mape,
            'cv_r2_mean': cv_mean,
            'cv_r2_std': cv_std,
        }

        return results

    def train_and_evaluate_all(self, X_train, X_test, y_train, y_test):
        """모든 모델 훈련 및 평가"""
        logger.info("\n" + "="*80)
        logger.info("모델 훈련 및 평가 시작")
        logger.info("="*80)

        for name, model in self.models.items():
            logger.info(f"\n[{name}] 훈련 중...")

            try:
                results = self.evaluate_model(
                    name, model,
                    X_train, X_test, y_train, y_test
                )

                self.results[name] = results

                # 결과 출력
                logger.info(f"  Train MAE: {results['train_mae']:,.0f}원")
                logger.info(f"  Test MAE:  {results['test_mae']:,.0f}원")
                logger.info(f"  Train RMSE: {results['train_rmse']:,.0f}원")
                logger.info(f"  Test RMSE:  {results['test_rmse']:,.0f}원")
                logger.info(f"  Train R²: {results['train_r2']:.4f}")
                logger.info(f"  Test R²:  {results['test_r2']:.4f}")
                logger.info(f"  Test MAPE: {results['test_mape']:.2f}%")

                if results['cv_r2_mean'] is not None:
                    logger.info(f"  CV R²: {results['cv_r2_mean']:.4f} (+/- {results['cv_r2_std']:.4f})")

            except Exception as e:
                logger.error(f"  훈련 실패: {e}")
                self.results[name] = None

        # 최고 모델 선정 (Test R²기준)
        valid_results = {
            name: res for name, res in self.results.items()
            if res is not None
        }

        if valid_results:
            best_name = max(valid_results, key=lambda x: valid_results[x]['test_r2'])
            self.best_model_name = best_name
            self.best_model = self.models[best_name]

            # 최고 모델 재훈련 (전체 데이터)
            X_full = np.vstack([X_train, X_test])
            y_full = np.hstack([y_train, y_test])
            self.best_model.fit(X_full, y_full)

            logger.info("\n" + "="*80)
            logger.info(f"최고 성능 모델: {best_name}")
            logger.info(f"  Test R²: {valid_results[best_name]['test_r2']:.4f}")
            logger.info(f"  Test MAE: {valid_results[best_name]['test_mae']:,.0f}원")
            logger.info(f"  Test MAPE: {valid_results[best_name]['test_mape']:.2f}%")
            logger.info("="*80)

    def create_ensemble(self, X_train, y_train):
        """앙상블 모델 생성"""
        logger.info("\n앙상블 모델 생성 중...")

        # Voting Regressor
        estimators = []

        if 'Random Forest' in self.models:
            estimators.append(('rf', self.models['Random Forest']))
        if 'Gradient Boosting' in self.models:
            estimators.append(('gb', self.models['Gradient Boosting']))
        if XGBOOST_AVAILABLE and 'XGBoost' in self.models:
            estimators.append(('xgb', self.models['XGBoost']))
        if LIGHTGBM_AVAILABLE and 'LightGBM' in self.models:
            estimators.append(('lgb', self.models['LightGBM']))

        if len(estimators) >= 2:
            ensemble = VotingRegressor(estimators=estimators)
            ensemble.fit(X_train, y_train)
            logger.info(f"앙상블 모델 생성 완료 ({len(estimators)}개 모델)")
            return ensemble
        else:
            logger.warning("앙상블 모델 생성 불가 (모델 부족)")
            return None

    def analyze_feature_importance(self, X, feature_names=None):
        """특성 중요도 분석"""
        if self.best_model is None:
            logger.warning("훈련된 모델 없음")
            return

        logger.info("\n특성 중요도 분석...")

        # Tree 기반 모델만 feature_importances_ 속성 있음
        if hasattr(self.best_model, 'feature_importances_'):
            importances = self.best_model.feature_importances_

            if feature_names is None:
                feature_names = [f'Feature {i}' for i in range(len(importances))]

            # 정렬
            indices = np.argsort(importances)[::-1]

            logger.info("\n상위 10개 중요 특성:")
            for i, idx in enumerate(indices[:10], 1):
                logger.info(f"  {i}. {feature_names[idx]}: {importances[idx]:.4f}")

            self.feature_importance = {
                'names': [feature_names[i] for i in indices],
                'values': importances[indices]
            }

            # 시각화
            if VISUALIZATION_AVAILABLE:
                self.plot_feature_importance(feature_names, importances)

    def plot_feature_importance(self, feature_names, importances, top_n=15):
        """특성 중요도 시각화"""
        indices = np.argsort(importances)[::-1][:top_n]

        plt.figure(figsize=(10, 8))
        plt.barh(range(top_n), importances[indices])
        plt.yticks(range(top_n), [feature_names[i] for i in indices])
        plt.xlabel('중요도')
        plt.title(f'특성 중요도 (Top {top_n}) - {self.best_model_name}')
        plt.gca().invert_yaxis()
        plt.tight_layout()

        output_path = Path("models") / "feature_importance.png"
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        logger.info(f"특성 중요도 그래프 저장: {output_path}")
        plt.close()

    def save_model(self, output_path: str = "models/auction_model.pkl"):
        """모델 저장"""
        if self.best_model is None:
            logger.error("저장할 모델 없음")
            return

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.best_model, output_path)
        logger.info(f"\n모델 저장: {output_path}")

        # 모델 크기
        size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"모델 크기: {size_mb:.2f} MB")

    def save_results(self):
        """결과 저장"""
        output_dir = Path("models")
        output_dir.mkdir(exist_ok=True)

        # 결과 JSON 저장
        results_file = output_dir / "training_results.json"

        results_dict = {
            'timestamp': datetime.now().isoformat(),
            'best_model': self.best_model_name,
            'models': {}
        }

        for name, res in self.results.items():
            if res is not None:
                # NumPy float을 Python float으로 변환
                results_dict['models'][name] = {
                    k: float(v) if v is not None else None
                    for k, v in res.items()
                }

        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"훈련 결과 저장: {results_file}")

    def test_predictions(self, X_test, y_test):
        """예측 테스트"""
        if self.best_model is None:
            logger.warning("테스트할 모델 없음")
            return

        logger.info("\n" + "="*80)
        logger.info("예측 테스트")
        logger.info("="*80)

        # 랜덤 샘플 선택
        n_samples = min(10, len(X_test))
        indices = np.random.choice(len(X_test), n_samples, replace=False)

        for i, idx in enumerate(indices, 1):
            x = X_test[idx:idx+1]
            y_true = y_test[idx]
            y_pred = self.best_model.predict(x)[0]

            error = y_pred - y_true
            error_rate = (error / y_true) * 100

            logger.info(f"\n샘플 {i}:")
            logger.info(f"  실제 낙찰가: {y_true:,.0f}원")
            logger.info(f"  예측 낙찰가: {y_pred:,.0f}원")
            logger.info(f"  오차: {error:,.0f}원 ({error_rate:+.1f}%)")


def main():
    """메인 함수"""
    logger.info("="*80)
    logger.info("고급 AI 모델 훈련 시작")
    logger.info("="*80)

    # 1. 모델 초기화
    trainer = AdvancedAuctionModel(random_state=42)

    # 2. 데이터 로드
    try:
        X, y = trainer.load_data()
    except FileNotFoundError as e:
        logger.error(f"데이터 파일을 찾을 수 없습니다: {e}")
        logger.info("먼저 다음을 실행하세요:")
        logger.info("  1. python collect_auction_data.py")
        logger.info("  2. python preprocess_data.py")
        return

    # 3. 데이터 분할
    X_train, X_test, y_train, y_test = trainer.prepare_data(X, y)

    # 4. 모델 초기화
    trainer.initialize_models()

    # 5. 모든 모델 훈련 및 평가
    trainer.train_and_evaluate_all(X_train, X_test, y_train, y_test)

    # 6. 앙상블 모델 생성 (선택사항)
    # ensemble = trainer.create_ensemble(X_train, y_train)

    # 7. 특성 중요도 분석
    # feature_names 로드 (전처리기에서)
    try:
        from preprocess_data import AuctionDataPreprocessor
        preprocessor = AuctionDataPreprocessor()
        preprocessor.load_preprocessor()
        feature_names = preprocessor.feature_names
    except:
        feature_names = None

    trainer.analyze_feature_importance(X, feature_names)

    # 8. 모델 저장
    trainer.save_model()

    # 9. 결과 저장
    trainer.save_results()

    # 10. 예측 테스트
    trainer.test_predictions(X_test, y_test)

    logger.info("\n" + "="*80)
    logger.info("훈련 완료!")
    logger.info("="*80)
    logger.info("\n다음 단계:")
    logger.info("  1. 모델 파일 확인: models/auction_model.pkl")
    logger.info("  2. 결과 확인: models/training_results.json")
    logger.info("  3. 서버 실행: python main.py")


if __name__ == "__main__":
    main()
