"""
데이터 전처리 및 특성 엔지니어링
경매 데이터를 머신러닝에 적합한 형태로 변환
"""
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from sklearn.preprocessing import LabelEncoder, StandardScaler
from typing import Tuple
import joblib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AuctionDataPreprocessor:
    """경매 데이터 전처리기"""

    def __init__(self):
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.feature_names = []

    def load_data(self, file_path: str) -> pd.DataFrame:
        """데이터 로드"""
        logger.info(f"데이터 로드: {file_path}")
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        logger.info(f"총 {len(df)}건 로드")
        return df

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 정제"""
        logger.info("데이터 정제 시작...")

        # 결측치 확인
        missing = df.isnull().sum()
        if missing.any():
            logger.warning(f"결측치 발견:\n{missing[missing > 0]}")

        # 필수 컬럼 확인
        required_cols = ['감정가', '낙찰가', '입찰자수']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"필수 컬럼 없음: {col}")

        # 이상치 제거
        original_len = len(df)

        # 감정가가 0이거나 음수인 데이터 제거
        df = df[df['감정가'] > 0].copy()

        # 낙찰가가 0이거나 음수인 데이터 제거
        df = df[df['낙찰가'] > 0].copy()

        # 입찰자 수가 0 이하인 데이터 제거
        df = df[df['입찰자수'] > 0].copy()

        # 낙찰률이 비정상적인 데이터 제거 (30% ~ 150%)
        df['낙찰률'] = df['낙찰가'] / df['감정가']
        df = df[(df['낙찰률'] >= 0.3) & (df['낙찰률'] <= 1.5)].copy()

        removed = original_len - len(df)
        if removed > 0:
            logger.warning(f"이상치 제거: {removed}건 ({removed/original_len*100:.1f}%)")

        logger.info(f"정제 후 데이터: {len(df)}건")

        return df

    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """특성 추출 및 엔지니어링"""
        logger.info("특성 엔지니어링 시작...")

        df = df.copy()

        # 1. 기본 특성
        # 감정가 (로그 스케일)
        df['감정가_log'] = np.log1p(df['감정가'])

        # 최저입찰가 (있는 경우)
        if '최저입찰가' in df.columns:
            df['최저입찰가_log'] = np.log1p(df['최저입찰가'])
            df['최저가율'] = df['최저입찰가'] / df['감정가']
        else:
            df['최저입찰가'] = df['감정가'] * 0.8  # 기본 80%
            df['최저입찰가_log'] = np.log1p(df['최저입찰가'])
            df['최저가율'] = 0.8

        # 입찰자 수
        df['입찰자수_log'] = np.log1p(df['입찰자수'])

        # 입찰자 경쟁률 (입찰자수가 많을수록 경쟁 치열)
        df['경쟁지수'] = df['입찰자수'] / (df['입찰자수'].mean() + 1)

        # 2. 면적 관련 특성
        if '면적' in df.columns:
            df['면적_log'] = np.log1p(df['면적'])
            df['평당감정가'] = df['감정가'] / (df['면적'] * 0.3025)  # ㎡ -> 평
            df['평당감정가_log'] = np.log1p(df['평당감정가'])
        else:
            df['면적'] = 85  # 기본값
            df['면적_log'] = np.log1p(85)

        # 3. 경매 회차 관련
        if '경매회차' in df.columns:
            df['경매회차'] = df['경매회차'].fillna(1).astype(int)
            df['경매회차_제곱'] = df['경매회차'] ** 2
            # 회차가 높을수록 낙찰가 하락 경향
            df['회차페널티'] = 1 - (df['경매회차'] - 1) * 0.1
            df['회차페널티'] = df['회차페널티'].clip(0.5, 1.0)
        else:
            df['경매회차'] = 1
            df['경매회차_제곱'] = 1
            df['회차페널티'] = 1.0

        # 4. 지역 특성
        if '지역' in df.columns:
            # 지역을 숫자로 인코딩
            if '지역' not in self.label_encoders:
                self.label_encoders['지역'] = LabelEncoder()
                df['지역_encoded'] = self.label_encoders['지역'].fit_transform(df['지역'])
            else:
                df['지역_encoded'] = self.label_encoders['지역'].transform(df['지역'])

            # 원-핫 인코딩
            region_dummies = pd.get_dummies(df['지역'], prefix='지역')
            df = pd.concat([df, region_dummies], axis=1)
        else:
            df['지역_encoded'] = 0

        # 5. 물건 종류 특성
        if '물건종류' in df.columns:
            if '물건종류' not in self.label_encoders:
                self.label_encoders['물건종류'] = LabelEncoder()
                df['물건종류_encoded'] = self.label_encoders['물건종류'].fit_transform(df['물건종류'])
            else:
                df['물건종류_encoded'] = self.label_encoders['물건종류'].transform(df['물건종류'])

            # 원-핫 인코딩
            type_dummies = pd.get_dummies(df['물건종류'], prefix='물건종류')
            df = pd.concat([df, type_dummies], axis=1)
        else:
            df['물건종류_encoded'] = 0

        # 6. 상호작용 특성
        df['감정가x입찰자수'] = df['감정가_log'] * df['입찰자수_log']
        df['최저가율x입찰자수'] = df['최저가율'] * df['입찰자수']

        if '면적' in df.columns:
            df['면적x입찰자수'] = df['면적_log'] * df['입찰자수_log']

        # 7. 가격 구간 (categorization)
        df['가격구간'] = pd.cut(
            df['감정가'],
            bins=[0, 100_000_000, 300_000_000, 500_000_000, 1_000_000_000, np.inf],
            labels=['1억이하', '1-3억', '3-5억', '5-10억', '10억이상']
        )
        price_dummies = pd.get_dummies(df['가격구간'], prefix='가격구간')
        df = pd.concat([df, price_dummies], axis=1)

        logger.info(f"특성 추출 완료: 총 {df.shape[1]}개 컬럼")

        return df

    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, list]:
        """
        머신러닝을 위한 특성 준비

        Returns:
            X: 특성 행렬
            y: 타겟 벡터 (낙찰가)
            feature_names: 특성 이름 리스트
        """
        logger.info("특성 행렬 준비 중...")

        # 타겟 변수
        y = df['낙찰가'].values

        # 특성 선택
        feature_cols = [
            # 기본 특성
            '감정가', '감정가_log',
            '최저입찰가', '최저입찰가_log', '최저가율',
            '입찰자수', '입찰자수_log', '경쟁지수',
            '경매회차', '경매회차_제곱', '회차페널티',

            # 상호작용 특성
            '감정가x입찰자수', '최저가율x입찰자수',
        ]

        # 면적 특성 (있는 경우)
        if '면적' in df.columns:
            feature_cols.extend([
                '면적', '면적_log',
                '평당감정가', '평당감정가_log',
                '면적x입찰자수'
            ])

        # 인코딩된 범주형 특성
        if '지역_encoded' in df.columns:
            feature_cols.append('지역_encoded')

        if '물건종류_encoded' in df.columns:
            feature_cols.append('물건종류_encoded')

        # 원-핫 인코딩된 특성들
        for col in df.columns:
            if col.startswith('지역_') and col != '지역_encoded':
                feature_cols.append(col)
            elif col.startswith('물건종류_') and col != '물건종류_encoded':
                feature_cols.append(col)
            elif col.startswith('가격구간_'):
                feature_cols.append(col)

        # 실제 존재하는 컬럼만 선택
        feature_cols = [col for col in feature_cols if col in df.columns]

        X = df[feature_cols].values
        self.feature_names = feature_cols

        logger.info(f"특성 행렬 크기: {X.shape}")
        logger.info(f"타겟 벡터 크기: {y.shape}")
        logger.info(f"사용된 특성 ({len(feature_cols)}개):")
        for i, col in enumerate(feature_cols, 1):
            logger.info(f"  {i}. {col}")

        return X, y, feature_cols

    def save_preprocessor(self, path: str = "models/preprocessor.pkl"):
        """전처리기 저장"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            'label_encoders': self.label_encoders,
            'scaler': self.scaler,
            'feature_names': self.feature_names
        }, path)
        logger.info(f"전처리기 저장: {path}")

    def load_preprocessor(self, path: str = "models/preprocessor.pkl"):
        """전처리기 로드"""
        data = joblib.load(path)
        self.label_encoders = data['label_encoders']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        logger.info(f"전처리기 로드: {path}")


def main():
    """메인 함수"""
    logger.info("="*60)
    logger.info("데이터 전처리 및 특성 엔지니어링")
    logger.info("="*60)

    # 데이터 파일 확인
    data_file = Path("data/auction_data.csv")

    if not data_file.exists():
        logger.error(f"데이터 파일이 없습니다: {data_file}")
        logger.info("먼저 collect_auction_data.py를 실행하세요")
        return

    # 전처리기 초기화
    preprocessor = AuctionDataPreprocessor()

    # 1. 데이터 로드
    df = preprocessor.load_data(data_file)

    # 2. 데이터 정제
    df = preprocessor.clean_data(df)

    # 3. 특성 엔지니어링
    df = preprocessor.extract_features(df)

    # 4. 특성 행렬 준비
    X, y, feature_names = preprocessor.prepare_features(df)

    # 5. 전처리된 데이터 저장
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)

    # DataFrame 저장
    processed_file = output_dir / "auction_data_processed.csv"
    df.to_csv(processed_file, index=False, encoding='utf-8-sig')
    logger.info(f"전처리된 데이터 저장: {processed_file}")

    # NumPy 배열 저장
    np.save(output_dir / "X_features.npy", X)
    np.save(output_dir / "y_target.npy", y)
    logger.info(f"특성 행렬 저장: {output_dir / 'X_features.npy'}")
    logger.info(f"타겟 벡터 저장: {output_dir / 'y_target.npy'}")

    # 6. 전처리기 저장
    preprocessor.save_preprocessor()

    # 7. 통계 정보
    logger.info("\n" + "="*60)
    logger.info("전처리 완료 통계")
    logger.info("="*60)
    logger.info(f"전처리된 데이터 수: {len(df)}건")
    logger.info(f"특성 개수: {X.shape[1]}개")
    logger.info(f"타겟 범위: {y.min():,.0f}원 ~ {y.max():,.0f}원")
    logger.info(f"타겟 평균: {y.mean():,.0f}원")
    logger.info(f"타겟 표준편차: {y.std():,.0f}원")

    # 낙찰률 분포
    auction_rate = df['낙찰가'] / df['감정가']
    logger.info(f"\n낙찰률 통계:")
    logger.info(f"  평균: {auction_rate.mean():.2%}")
    logger.info(f"  중앙값: {auction_rate.median():.2%}")
    logger.info(f"  최소: {auction_rate.min():.2%}")
    logger.info(f"  최대: {auction_rate.max():.2%}")

    # 물건 종류별 통계
    if '물건종류' in df.columns:
        logger.info(f"\n물건 종류별 평균 낙찰률:")
        for ptype in df['물건종류'].unique():
            mask = df['물건종류'] == ptype
            rate = (df[mask]['낙찰가'] / df[mask]['감정가']).mean()
            count = mask.sum()
            logger.info(f"  {ptype}: {rate:.2%} ({count}건)")

    # 지역별 통계
    if '지역' in df.columns:
        logger.info(f"\n지역별 평균 낙찰률:")
        for region in df['지역'].unique():
            mask = df['지역'] == region
            rate = (df[mask]['낙찰가'] / df[mask]['감정가']).mean()
            count = mask.sum()
            logger.info(f"  {region}: {rate:.2%} ({count}건)")

    logger.info("\n전처리 완료!")
    logger.info("다음 단계: python train_model_advanced.py")


if __name__ == "__main__":
    main()
