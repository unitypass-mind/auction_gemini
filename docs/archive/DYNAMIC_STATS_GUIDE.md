# 동적 구간별 통계 업데이트 가이드

감정가 구간별 예상 오차가 자동으로 업데이트되도록 구현되었습니다.

---

## 🎯 기능 개요

### 문제
- 기존: 웹 UI에 하드코딩된 고정 통계 (710건 기준)
- 데이터 증가 시 수동으로 HTML 수정 필요

### 해결
- 자동: 파이프라인 실행 시 자동으로 최신 통계 업데이트
- 웹 UI가 API에서 동적으로 로드

---

## 🔄 자동 업데이트 프로세스

```
1. 파이프라인 실행
   python auto_pipeline.py --skip-collect
         ↓
2. 이상치 제거 (Step 2)
   → 낙찰률 800% 초과 데이터 자동 제거
         ↓
3. 모델 재학습 (Step 3)
   → 정제된 데이터로 재학습
         ↓
4. 전체 재예측 (Step 4)
   → 모든 데이터 재예측
         ↓
5. 구간별 분석 (Step 5)
   → data/price_range_stats.json 자동 생성
         ↓
6. 서버 모델 리로드 (Step 6)
   → 최신 통계 반영
         ↓
7. 웹 UI 자동 갱신
   → API에서 최신 통계 로드
```

---

## 📊 저장되는 데이터

### JSON 파일: `data/price_range_stats.json`

```json
{
  "timestamp": "2026-02-12T20:49:38.656958",
  "last_updated": "2026-02-12 20:49:38",
  "total_count": 1210,
  "overall_stats": {
    "avg_error_rate": 2.76,
    "avg_error_amount": 35534574,
    "median_error_amount": 817367
  },
  "price_ranges": [
    {
      "range": "1억 이하",
      "count": 185,
      "avg_error_rate": 2.31,
      "avg_error_amount": 503790,
      "median_error_amount": 259936,
      "display_text": "평균 ±26만원 오차 (오차율 2.3%)"
    },
    ...
  ]
}
```

---

## 🌐 API 엔드포인트

### GET `/price-range-stats`

**설명**: 감정가 구간별 통계 조회

**요청**:
```bash
curl http://localhost:8000/price-range-stats
```

**응답**:
```json
{
  "success": true,
  "data": {
    "timestamp": "2026-02-12T20:49:38.656958",
    "last_updated": "2026-02-12 20:49:38",
    "total_count": 1210,
    "overall_stats": { ... },
    "price_ranges": [ ... ]
  }
}
```

**특징**:
- 파일이 없으면 자동으로 분석 실행
- 항상 최신 데이터 반환

---

## 💻 웹 UI 구현

### HTML (static/index.html)

**이전** (하드코딩):
```html
<div>📊 1억 이하: ±31만원</div>
<div>📊 1억~3억: ±56만원</div>
```

**현재** (동적):
```html
<div id="price-range-stats" style="...">
    <div style="color:#999;">로딩 중...</div>
</div>
```

### JavaScript

```javascript
async function loadPriceRangeStats() {
    const response = await fetch('/price-range-stats');
    const result = await response.json();

    const data = result.data;

    // 구간별 통계 표시
    container.innerHTML = data.price_ranges.map(range => {
        const median = Math.round(range.median_error_amount / 10000);
        const rate = range.avg_error_rate.toFixed(1);
        return `<div>📊 ${range.range}: ±${median}만원 (${rate}%)</div>`;
    }).join('');
}
```

**호출 시점**:
- 정확도 탭 로드 시 (`loadAccuracyData()` 함수 내)
- 페이지 로드 시 자동 실행

---

## 🎯 사용 방법

### 1. 일반 업데이트

```bash
# 1. 데이터 수집
python auto_weekly_collect.py

# 2. 전체 파이프라인 실행
python auto_pipeline.py --skip-collect
```

**결과**:
- ✅ 모델 재학습
- ✅ 전체 재예측
- ✅ 구간별 통계 JSON 생성
- ✅ 서버 모델 리로드
- ✅ 웹 UI 자동 반영

### 2. 통계만 업데이트

```bash
# 구간별 분석만 실행
python analyze_by_price_range.py
```

**결과**:
- ✅ data/price_range_stats.json 생성/업데이트
- 웹 UI 새로고침 시 반영

### 3. 수동 API 호출

```bash
# API 테스트
curl http://localhost:8000/price-range-stats
```

---

## 📈 업데이트 확인

### 방법 1: 웹 UI

1. http://localhost:8000 접속
2. **정확도** 탭 클릭
3. "💡 감정가 구간별 예상 오차" 섹션 확인
4. 우측에 업데이트 시간 표시됨

예: `💡 감정가 구간별 예상 오차 (2026-02-12 20:49:38 업데이트)`

### 방법 2: JSON 파일

```bash
cat data/price_range_stats.json
```

### 방법 3: API 직접 조회

```bash
curl -s http://localhost:8000/price-range-stats | python -m json.tool
```

---

## 🔍 현재 통계 (1,210건 기준)

| 구간 | 건수 | 중위 오차 | 오차율 |
|------|------|----------|--------|
| 1억 이하 | 185건 | ±26만원 | 2.3% |
| **1억~3억** | **681건** | **±70만원** | **1.9%** ⭐ |
| 3억~5억 | 126건 | ±126만원 | 2.8% |
| **5억~10억** | 158건 | **±423만원** | **1.4%** ⭐⭐ |
| 10억 초과 | 60건 | ±6,334만원 | 17.8% |

---

## 🚀 자동화 워크플로우

### 전체 프로세스 (완전 자동)

```
매주 자동 실행 (scheduler.py)
         ↓
   📥 데이터 수집 (100건)
         ↓
   🧹 이상치 제거 ✅ (낙찰률 800% 초과 자동 제거)
         ↓
   🧠 모델 재학습
         ↓
   🔮 전체 재예측
         ↓
   📊 구간별 분석 ✅ (JSON 자동 생성)
         ↓
   🔄 서버 모델 리로드
         ↓

   ✅ 웹 UI 최신 통계 표시
```

**사용자 경험**:
- 다운타임: 0초
- 최신 통계 자동 반영
- 별도 작업 불필요

---

## 🛠️ 문제 해결

### 1. 통계가 업데이트되지 않음

**원인**: JSON 파일이 생성되지 않음

**해결**:
```bash
python analyze_by_price_range.py
```

### 2. 웹 UI에 "로딩 중..." 계속 표시

**원인**: API 호출 실패

**확인**:
```bash
curl http://localhost:8000/price-range-stats
```

**해결**: 서버 재시작
```bash
python restart_server.py
```

### 3. 구 통계 표시됨

**원인**: 브라우저 캐시

**해결**:
- 브라우저 새로고침 (Ctrl+F5)
- 또는 시크릿 모드로 접속

---

## 📁 관련 파일

| 파일 | 역할 |
|------|------|
| `analyze_by_price_range.py` | 통계 분석 + JSON 생성 |
| `data/price_range_stats.json` | 통계 데이터 저장 |
| `main.py` | API 엔드포인트 제공 |
| `static/index.html` | 웹 UI (동적 로드) |
| `auto_pipeline.py` | 전체 자동화 |

---

## 🎉 요약

**이전**:
- 하드코딩된 고정 통계
- 수동 HTML 수정 필요
- 최신 데이터 반영 어려움

**현재**:
- ✅ 자동 업데이트
- ✅ API 기반 동적 로드
- ✅ 파이프라인 통합
- ✅ 실시간 반영

**효과**:
- 유지보수 시간 **100% 절감**
- 항상 최신 통계 표시
- 완전 자동화

---

**작성일**: 2026-02-12
**버전**: 1.0
