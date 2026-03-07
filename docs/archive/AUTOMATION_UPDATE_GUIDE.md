# 자동화 시스템 업데이트 가이드

서버 자동 업데이트 기능이 추가된 자동화 시스템 사용 가이드입니다.

---

## 🆕 새로운 기능

### 1. 모델 핫 리로드 (Hot Reload)

서버를 재시작하지 않고도 모델을 자동으로 업데이트할 수 있습니다!

**주요 이점**:
- ✅ **무중단 업데이트**: 서버를 종료하지 않고 모델 갱신
- ✅ **빠른 업데이트**: 수십 초 내에 최신 모델 적용
- ✅ **자동화**: 파이프라인 실행 시 자동으로 서버 업데이트

### 2. 서버 API 엔드포인트

#### `/model-status` - 모델 상태 조회

```bash
curl http://localhost:8000/model-status
```

**응답 예시**:
```json
{
  "model_loaded": true,
  "model_version": "v2",
  "load_time": "2026-02-12 20:42:49",
  "v2_path_exists": true,
  "v1_path_exists": true
}
```

#### `/reload-model` - 모델 리로드

```bash
curl -X POST http://localhost:8000/reload-model
```

**응답 예시**:
```json
{
  "success": true,
  "message": "모델이 성공적으로 리로드되었습니다",
  "model_version": "v2",
  "load_time": "2026-02-12 20:43:06",
  "model_loaded": true
}
```

#### `/health` - 헬스 체크 (업데이트됨)

```bash
curl http://localhost:8000/health
```

**응답 예시**:
```json
{
  "status": "ok",
  "model_loaded": true,
  "model_load_time": "2026-02-12 20:43:06",
  "version": "1.0.0"
}
```

---

## 🚀 업데이트된 자동화 파이프라인

파이프라인이 **5단계**로 확장되었습니다:

### 실행 방법

```bash
# 데이터 수집 포함 (전체)
python auto_pipeline.py

# 재학습만 (데이터 수집 건너뜀)
python auto_pipeline.py --skip-collect
```

### 5단계 프로세스

1. **📥 데이터 수집** (선택적)
   - 신규 경매 데이터 수집
   - 건너뛰기 가능 (--skip-collect)

2. **🧠 모델 재학습**
   - 전체 데이터로 AI 모델 재학습
   - models/auction_model_v2.pkl 업데이트

3. **🔮 전체 재예측**
   - 모든 데이터에 대해 재예측 수행
   - 정확도 계산 및 업데이트

4. **📊 구간별 분석**
   - 감정가 구간별 성능 분석
   - 통계 리포트 생성

5. **🔄 서버 모델 리로드** ⭐ **NEW!**
   - 실행 중인 서버에 최신 모델 자동 적용
   - 서버 재시작 불필요

---

## 📋 상세 사용 예시

### 예시 1: 일반 업데이트 (권장)

```bash
# 1. 데이터 100건 수집
python auto_weekly_collect.py

# 2. 파이프라인 실행 (수집 건너뜀 - 이미 수집했으므로)
python auto_pipeline.py --skip-collect
```

**결과**:
- ✅ 모델 재학습 완료
- ✅ 예측 업데이트 완료
- ✅ 분석 완료
- ✅ **서버 자동 업데이트 완료** (재시작 불필요!)

### 예시 2: 전체 자동화

```bash
# 데이터 수집부터 서버 업데이트까지 한 번에
python auto_pipeline.py
```

**소요 시간**: 약 1~2분

### 예시 3: 재학습만 빠르게

```bash
# 새 데이터 없이 기존 데이터로 재학습만
python auto_pipeline.py --skip-collect
```

**소요 시간**: 약 30초

---

## 🔄 서버 관리

### 방법 1: 모델만 리로드 (권장)

서버가 실행 중일 때:

```bash
# Python에서
import requests
response = requests.post("http://localhost:8000/reload-model")
print(response.json())

# 또는 curl
curl -X POST http://localhost:8000/reload-model
```

### 방법 2: 서버 재시작

필요시 서버 완전 재시작:

```bash
# Python 스크립트
python restart_server.py

# 또는 Windows 배치 파일
restart_server.bat
```

**요구사항**: `pip install psutil`

---

## 🔍 모니터링

### 현재 모델 상태 확인

```bash
curl http://localhost:8000/model-status
```

### 로그 확인

파이프라인 실행 로그:
```
logs/pipeline_YYYYMMDD_HHMMSS.log
```

서버 로그:
- 콘솔 출력 확인
- 또는 백그라운드 실행 시 로그 파일 확인

---

## ⚡ 전체 워크플로우

### 주간 자동화 루틴

**매주 월요일 02:00** (자동 스케줄링 시):

```
1. 📥 데이터 수집 (100건)
   └─> 2. 🧠 모델 재학습
       └─> 3. 🔮 전체 재예측
           └─> 4. 📊 구간별 분석
               └─> 5. 🔄 서버 모델 리로드 ✅
```

**결과**: 사용자는 최신 모델로 예측 서비스 이용 가능!

---

## 🛠️ 문제 해결

### 1. 서버 모델 리로드 실패

**증상**:
```
⚠️ 서버에 연결할 수 없습니다 (서버가 실행 중이 아님)
```

**해결**:
```bash
# 서버 시작
python main.py

# 또는 백그라운드 실행
python main.py &  # Linux/Mac
start python main.py  # Windows
```

### 2. 모델 파일 없음

**증상**:
```json
{
  "detail": "모델 파일을 찾을 수 없거나 로드에 실패했습니다"
}
```

**해결**:
```bash
# 모델 재학습
python train_model_v2.py

# 재학습 후 리로드
curl -X POST http://localhost:8000/reload-model
```

### 3. psutil 설치 오류

**증상**:
```
ModuleNotFoundError: No module named 'psutil'
```

**해결**:
```bash
pip install psutil
```

---

## 📊 성능 비교

### 이전 방식 (서버 재시작)

```
1. 재학습 (30초)
2. 서버 종료 (5초)
3. 서버 재시작 (10초)
4. 테스트 (5초)
-------------------
총 소요 시간: 50초
다운타임: 15초 ❌
```

### 새 방식 (모델 핫 리로드)

```
1. 재학습 (30초)
2. 모델 리로드 (1초)
3. 테스트 (5초)
-------------------
총 소요 시간: 36초
다운타임: 0초 ✅
```

**개선**: 28% 빠름, 무중단 서비스!

---

## 🎯 Best Practices

### 1. 정기 업데이트

```bash
# 매주 실행 (스케줄러 사용)
python auto_pipeline.py
```

### 2. 긴급 업데이트

```bash
# 빠른 재학습 (데이터 수집 없이)
python auto_pipeline.py --skip-collect
```

### 3. 수동 모델 리로드

```bash
# 모델만 교체하고 리로드
curl -X POST http://localhost:8000/reload-model
```

### 4. 상태 모니터링

```bash
# 주기적으로 확인
curl http://localhost:8000/model-status
```

---

## 📁 관련 파일

| 파일 | 설명 |
|------|------|
| `main.py` | 서버 (모델 핫 리로드 기능 추가) |
| `auto_pipeline.py` | 5단계 자동화 파이프라인 |
| `restart_server.py` | 서버 재시작 스크립트 |
| `restart_server.bat` | Windows용 배치 파일 |
| `AUTOMATION_GUIDE.md` | 기본 자동화 가이드 |
| `AUTOMATION_UPDATE_GUIDE.md` | 이 파일 |

---

## 🎉 요약

**새로운 기능**:
- ✅ 서버 무중단 모델 업데이트
- ✅ 자동화 파이프라인에 통합
- ✅ REST API 엔드포인트 제공
- ✅ 상태 모니터링 기능

**사용법**:
```bash
# 전체 자동화 (가장 간단)
python auto_pipeline.py --skip-collect
```

**결과**:
- 30초 만에 모델 업데이트
- 서버 재시작 불필요
- 사용자 서비스 중단 없음

---

**작성일**: 2026-02-12
**버전**: 2.0
