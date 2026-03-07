# 📊 예측 정확도 추적 시스템 가이드

## 🎯 목적

AI 모델의 예측 결과와 실제 낙찰가를 비교하여 정확도를 추적하고 개선합니다.

---

## 🏗️ 시스템 구조

### 1. 데이터베이스 (`database.py`)
- **SQLite 데이터베이스**: `data/predictions.db`
- **예측 저장**: 모든 예측이 자동으로 저장됨
- **실제 결과 업데이트**: 낙찰 후 실제 가격 입력
- **정확도 통계**: 자동 계산

### 2. 자동 로깅 (`main.py`)
- `/predict` API 호출 시 자동 저장
- `/auction` API 호출 시 자동 저장
- 예측 정보 (감정가, 물건종류, 지역 등) 포함

### 3. 웹 대시보드
- **접속**: http://localhost:8000 → "📊 정확도" 탭
- **표시 내용**:
  - 총 예측 건수
  - 검증 완료 건수
  - 평균 오차율
  - 검증된 예측 목록
  - 미검증 예측 목록

### 4. 검증 스크립트 (`verify_results.py`)
- 실제 낙찰 결과 입력
- 정확도 리포트 생성
- CSV 일괄 업로드 지원

---

## 📝 사용 방법

### A. 예측 저장 (자동)

웹에서 예측을 실행하면 자동으로 데이터베이스에 저장됩니다.

```bash
# 예: 간단 예측 실행
curl "http://localhost:8000/predict?start_price=300000000&bidders=10"
```

### B. 실제 낙찰가 입력 (수동)

#### 방법 1: 명령줄 입력

```bash
# 사건번호, 실제 낙찰가, 낙찰일자
python verify_results.py verify "2024타경00001" 245000000 "2024-03-15"
```

#### 방법 2: 대화형 모드

```bash
python verify_results.py

# 화면 안내에 따라 입력
```

#### 방법 3: CSV 파일 업로드

**CSV 형식 (result.csv):**
```csv
사건번호,실제낙찰가,낙찰일자
2024타경00001,245000000,2024-03-15
2024타경00002,180000000,2024-03-16
2024타경00003,320000000,2024-03-17
```

**업로드:**
```bash
python verify_results.py csv result.csv
```

### C. 정확도 확인

#### 웹 대시보드
```
http://localhost:8000 → 📊 정확도 탭
```

#### 명령줄 리포트
```bash
python verify_results.py report
```

**출력 예시:**
```
📊 AI 모델 정확도 리포트 (최근 30일)
============================================================
총 예측 건수:         2건
검증 완료:            1건
검증률:           50.0%
------------------------------------------------------------
평균 오차율:       2.04%
평균 오차 금액:       5,000,000원
최고 정확도:       2.04%
최저 정확도:       2.04%
============================================================
```

#### 미검증 목록 조회
```bash
python verify_results.py list
```

---

## 🔍 API 엔드포인트

### 1. 정확도 조회
```bash
GET /accuracy

# 응답:
{
  "success": true,
  "stats": {
    "total_predictions": 2,
    "verified_predictions": 1,
    "avg_error_rate": 2.04,
    "avg_error_amount": 5000000,
    "verification_rate": 50.0
  },
  "recent_verified": [...],
  "unverified_count": 1
}
```

### 2. 실제 낙찰가 업데이트
```bash
POST /verify-result?case_no=2024타경00001&actual_price=245000000&actual_date=2024-03-15

# 응답:
{
  "success": true,
  "message": "실제 낙찰가가 업데이트되었습니다",
  "case_no": "2024타경00001",
  "actual_price": 245000000
}
```

---

## 📈 데이터 분석 워크플로우

### 단계 1: 예측 실행
```
웹 UI 또는 API로 예측 실행 → 자동 저장
```

### 단계 2: 낙찰 결과 수집
```
법원 경매 사이트에서 낙찰 결과 확인
→ CSV 파일 작성 또는 수동 입력
```

### 단계 3: 검증 입력
```bash
python verify_results.py csv result.csv
```

### 단계 4: 정확도 분석
```bash
python verify_results.py report
```

### 단계 5: 모델 개선
```
- 오차율이 높은 케이스 분석
- 특성 추가 또는 모델 재훈련
- 반복 테스트
```

---

## 💡 Best Practices

### 1. 정기적인 검증
- **주 1회**: 낙찰된 물건의 실제 가격 입력
- **월 1회**: 정확도 리포트 생성 및 분석

### 2. CSV 템플릿 활용
```bash
# 미검증 목록을 CSV로 저장
python verify_results.py list > pending.txt

# 템플릿 생성
echo "사건번호,실제낙찰가,낙찰일자" > template.csv
```

### 3. 오차율 모니터링
- **2% 이하**: 매우 우수
- **2-5%**: 양호
- **5-10%**: 개선 필요
- **10% 이상**: 모델 재검토 필요

### 4. 데이터 축적 목표
- **초기 단계**: 최소 50건 검증
- **신뢰도 확보**: 최소 200건 검증
- **수익화 준비**: 500건 이상 검증

---

## 📊 데이터베이스 스키마

```sql
CREATE TABLE predictions (
    id INTEGER PRIMARY KEY,
    case_no TEXT NOT NULL,        -- 사건번호
    물건번호 TEXT,
    감정가 INTEGER,
    물건종류 TEXT,
    지역 TEXT,
    면적 REAL,
    경매회차 INTEGER,
    입찰자수 INTEGER,
    predicted_price INTEGER,       -- 예측 낙찰가
    actual_price INTEGER,          -- 실제 낙찰가 (나중에 입력)
    error_amount INTEGER,          -- 오차 금액
    error_rate REAL,               -- 오차율 (%)
    verified BOOLEAN,              -- 검증 여부
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

---

## 🎯 다음 단계

### 1. 데이터 수집 자동화
- 법원 경매 사이트 크롤러 개발
- 낙찰 결과 자동 업데이트

### 2. 고급 분석 기능
- 지역별 정확도 분석
- 물건 종류별 정확도 분석
- 시간대별 트렌드 분석

### 3. 알림 시스템
- 예측한 물건 낙찰 시 알림
- 정확도 이상 감지 시 경고

### 4. 리포트 자동화
- 주간/월간 정확도 리포트 이메일
- PDF 리포트 생성

---

## 🔧 트러블슈팅

### 문제 1: 데이터베이스 파일이 없음
```bash
# 데이터베이스 재초기화
python database.py
```

### 문제 2: 중복 예측 오류
```
→ 정상입니다. 같은 사건번호로 여러 번 예측 시 최신 것만 업데이트됩니다.
```

### 문제 3: CSV 업로드 실패
```bash
# 인코딩 확인 (UTF-8)
# 컬럼명 확인: 사건번호, 실제낙찰가, 낙찰일자
```

---

## 📞 명령어 요약

```bash
# 정확도 리포트
python verify_results.py report

# 미검증 목록
python verify_results.py list

# 수동 검증
python verify_results.py verify <사건번호> <낙찰가> [날짜]

# CSV 업로드
python verify_results.py csv <파일경로>

# 대화형 모드
python verify_results.py
```

---

**목표: 500건 검증 데이터 확보 → 신뢰도 99% 달성 → 수익화 시작! 🚀**
