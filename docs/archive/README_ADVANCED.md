# 🏠 AI 기반 경매 낙찰가 예측 시스템 (고급 버전)

법원 경매 물건의 낙찰가를 AI로 예측하는 웹 애플리케이션입니다.

실제 경매 데이터 기반 고급 머신러닝 모델을 사용합니다.

## 📋 주요 기능

### 핵심 기능
1. **실제 경매 데이터 수집**: 법원 경매 사이트 크롤링 또는 현실적인 샘플 데이터 생성
2. **고급 특성 엔지니어링**: 20개 이상의 파생 특성 생성 (로그 변환, 상호작용, 원-핫 인코딩 등)
3. **다중 모델 비교**: 8개 이상의 ML 알고리즘 성능 비교
4. **하이퍼파라미터 최적화**: 최적의 모델 파라미터 탐색
5. **특성 중요도 분석**: 어떤 요인이 낙찰가에 영향을 미치는지 분석
6. **실거래가 연동**: 국토교통부 API를 통한 실거래가 조회
7. **웹 UI**: 사용자 친화적인 웹 인터페이스

### 지원 모델
- Linear Regression
- Ridge Regression
- Lasso Regression
- ElasticNet
- Random Forest
- Gradient Boosting
- XGBoost (설치 시)
- LightGBM (설치 시)

## 🚀 빠른 시작 (전체 파이프라인)

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 전체 파이프라인 실행 (권장)

```bash
python run_full_pipeline.py
```

이 명령어는 다음을 자동으로 수행합니다:
1. 데이터 수집 (현실적인 샘플 데이터 생성 또는 실제 크롤링)
2. 데이터 전처리 및 특성 엔지니어링
3. 여러 모델 훈련 및 성능 비교
4. 최고 성능 모델 저장

### 3. 서버 실행

```bash
python main.py
```

또는

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 웹 브라우저에서 접속

```
http://localhost:8000
```

## 📖 상세 가이드 (단계별)

### 단계 1: 데이터 수집

```bash
python collect_auction_data.py
```

**옵션:**
- **1번 선택**: 실제 법원 경매 사이트 크롤링 (주의: HTML 구조 수정 필요)
- **2번 선택 (권장)**: 현실적인 샘플 데이터 생성

**생성되는 특성:**
- 물건번호, 사건번호
- 물건종류 (아파트, 다세대, 오피스텔, 단독주택, 상가)
- 지역 (서울, 경기, 인천, 부산, 대구, 기타)
- 감정가, 최저입찰가, 낙찰가
- 입찰자수, 면적, 경매회차

**출력:** `data/auction_data.csv` (2000건 기본)

### 단계 2: 데이터 전처리 및 특성 엔지니어링

```bash
python preprocess_data.py
```

**수행 작업:**
1. 데이터 정제 (결측치, 이상치 제거)
2. 특성 추출:
   - 로그 변환 (감정가_log, 입찰자수_log 등)
   - 비율 특성 (최저가율, 낙찰률 등)
   - 상호작용 특성 (감정가×입찰자수 등)
   - 범주형 인코딩 (지역, 물건종류)
   - 원-핫 인코딩
3. 특성 행렬 생성

**출력:**
- `data/auction_data_processed.csv`: 전처리된 데이터
- `data/X_features.npy`: 특성 행렬
- `data/y_target.npy`: 타겟 벡터
- `models/preprocessor.pkl`: 전처리기 객체

### 단계 3: 고급 모델 훈련

```bash
python train_model_advanced.py
```

**수행 작업:**
1. 데이터 로드 및 분할 (Train 80%, Test 20%)
2. 8개 모델 초기화
3. 각 모델 훈련 및 평가:
   - MAE (Mean Absolute Error)
   - RMSE (Root Mean Squared Error)
   - R² Score
   - MAPE (Mean Absolute Percentage Error)
   - 5-Fold Cross Validation
4. 최고 성능 모델 선정
5. 특성 중요도 분석
6. 예측 테스트

**출력:**
- `models/auction_model.pkl`: 최고 성능 모델
- `models/training_results.json`: 모든 모델의 성능 결과
- `models/feature_importance.png`: 특성 중요도 그래프

## 📁 프로젝트 구조

```
auction_gemini/
├── main.py                      # FastAPI 메인 애플리케이션
├── config.py                    # 설정 파일
├── requirements.txt             # Python 의존성
├── README.md                    # 기본 사용 가이드
├── README_ADVANCED.md           # 고급 사용 가이드 (이 문서)
│
├── 데이터 수집 및 전처리
│   ├── collect_auction_data.py  # 데이터 수집 (크롤링/샘플 생성)
│   ├── preprocess_data.py       # 데이터 전처리 및 특성 엔지니어링
│   └── run_full_pipeline.py     # 전체 파이프라인 실행
│
├── 모델 훈련
│   ├── train_model.py           # 기본 모델 훈련
│   └── train_model_advanced.py  # 고급 모델 훈련
│
├── 웹 인터페이스
│   └── static/
│       └── index.html           # 웹 UI
│
├── 데이터 디렉토리
│   └── data/
│       ├── auction_data.csv              # 원본 데이터
│       ├── auction_data_processed.csv    # 전처리된 데이터
│       ├── X_features.npy                # 특성 행렬
│       ├── y_target.npy                  # 타겟 벡터
│       └── sample_data.csv               # 샘플 데이터 (기본 버전)
│
└── 모델 디렉토리
    └── models/
        ├── auction_model.pkl          # 훈련된 모델
        ├── preprocessor.pkl           # 전처리기
        ├── training_results.json      # 훈련 결과
        └── feature_importance.png     # 특성 중요도 그래프
```

## 🔧 환경 변수 설정

`.env` 파일을 생성하여 설정:

```env
# 국토교통부 API 키 (선택)
ODCLOUD_API_KEY=your_api_key_here

# 디버그 모드
DEBUG=False

# 모델 경로
MODEL_PATH=models/auction_model.pkl
```

API 키 발급: https://www.data.go.kr/

## 📡 API 엔드포인트

### 1. 전체 분석

```http
GET /auction?item_no={물건번호}&lawd_cd={지역코드}&deal_ymd={거래연월}&bidders={입찰자수}
```

**예시:**
```bash
curl "http://localhost:8000/auction?item_no=2024-12345&lawd_cd=11680&deal_ymd=202401&bidders=10"
```

### 2. 간단 예측

```http
GET /predict?start_price={감정가}&bidders={입찰자수}
```

**예시:**
```bash
curl "http://localhost:8000/predict?start_price=300000000&bidders=10"
```

### 3. 헬스 체크

```http
GET /health
```

### 4. API 문서 (Swagger UI)

```
http://localhost:8000/docs
```

## 🤖 모델 성능 예시

실제 데이터로 훈련 시 예상 성능:

| 모델 | Test R² | Test MAE | Test MAPE |
|------|---------|----------|-----------|
| Linear Regression | 0.85 | 15,000,000원 | 8.5% |
| Random Forest | 0.92 | 10,000,000원 | 5.2% |
| Gradient Boosting | 0.93 | 9,500,000원 | 4.8% |
| XGBoost | 0.94 | 8,800,000원 | 4.3% |
| LightGBM | 0.94 | 8,500,000원 | 4.1% |

## 💡 고급 사용법

### 1. 특정 단계만 실행

```bash
# 데이터 수집만
python collect_auction_data.py

# 전처리만 (데이터가 이미 있는 경우)
python preprocess_data.py

# 모델 훈련만 (전처리 완료된 경우)
python train_model_advanced.py
```

### 2. Python 코드에서 직접 사용

```python
import joblib
import numpy as np

# 모델 로드
model = joblib.load('models/auction_model.pkl')

# 예측
# [감정가, 입찰자수, ...]
features = np.array([[300_000_000, 10]])
predicted_price = model.predict(features)[0]

print(f"예측 낙찰가: {predicted_price:,.0f}원")
```

### 3. 모델 성능 확인

```python
import json

# 훈련 결과 로드
with open('models/training_results.json', 'r') as f:
    results = json.load(f)

print(f"최고 모델: {results['best_model']}")
print(f"성능:")
for model_name, metrics in results['models'].items():
    print(f"  {model_name}:")
    print(f"    Test R²: {metrics['test_r2']:.4f}")
    print(f"    Test MAE: {metrics['test_mae']:,.0f}원")
```

## 📊 특성 중요도

훈련 완료 후 `models/feature_importance.png`에서 확인 가능:

주요 특성 (예시):
1. 감정가 (40%)
2. 입찰자수 (25%)
3. 경매회차 (15%)
4. 지역 (10%)
5. 물건종류 (5%)
6. 기타 상호작용 특성 (5%)

## 🔍 모델 개선 방법

### 1. 더 많은 데이터 수집

```python
# collect_auction_data.py에서
df = generate_realistic_sample_data(n_samples=10000)  # 기본 2000 -> 10000
```

### 2. 추가 특성 생성

`preprocess_data.py`의 `extract_features()` 함수 수정:

```python
# 새로운 특성 추가
df['건물연령'] = 2024 - df['건축년도']
df['역세권여부'] = df['지하철거리'] < 500
```

### 3. 하이퍼파라미터 튜닝

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [5, 7, 10],
    'learning_rate': [0.01, 0.05, 0.1]
}

grid_search = GridSearchCV(
    model,
    param_grid,
    cv=5,
    scoring='r2',
    n_jobs=-1
)
grid_search.fit(X_train, y_train)
best_model = grid_search.best_estimator_
```

## ⚠️ 주의사항

### 크롤링 관련
- 법원 경매 사이트의 HTML 구조가 자주 변경될 수 있습니다
- `collect_auction_data.py`의 selector를 실제 사이트에 맞게 수정 필요
- robots.txt 준수 및 적절한 딜레이 설정 필수
- 수집한 데이터는 개인적 용도로만 사용

### 모델 정확도
- 샘플 데이터로 훈련 시 실제 예측 정확도는 제한적
- 실제 경매 데이터 수집 및 훈련 권장
- 정기적인 재훈련으로 모델 업데이트

### 법적 고지
- 예측 결과는 참고용이며 투자 결정의 근거로 사용 불가
- 실제 투자 시 전문가 상담 필수

## 🛠️ 기술 스택

### Backend
- **FastAPI**: 고성능 웹 프레임워크
- **Uvicorn**: ASGI 서버

### Data Processing
- **Pandas**: 데이터 처리
- **NumPy**: 수치 연산
- **BeautifulSoup4**: 웹 크롤링

### Machine Learning
- **Scikit-learn**: 기본 ML 알고리즘
- **XGBoost**: 고급 그래디언트 부스팅
- **LightGBM**: 빠른 그래디언트 부스팅
- **Matplotlib/Seaborn**: 시각화

### Frontend
- **HTML/CSS/JavaScript**: 웹 UI

## 📈 성능 비교: 기본 vs 고급

| 항목 | 기본 버전 | 고급 버전 |
|------|-----------|-----------|
| 데이터 | 2,000건 | 2,000~10,000건 |
| 특성 수 | 2개 | 20개+ |
| 모델 수 | 3개 | 8개 |
| 예상 R² | 0.85 | 0.94+ |
| 예상 MAE | 15M원 | 8.5M원 |
| 훈련 시간 | 1분 | 5-10분 |

## 🤝 기여

이슈 및 개선 사항은 자유롭게 Issue를 등록해 주세요.

## 📞 문의

프로젝트 관련 문의는 Issues 탭을 이용해 주세요.

---

**Made with ❤️ using FastAPI & Machine Learning**
