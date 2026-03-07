# 자동화 시스템 사용 가이드

경매 낙찰가 예측 시스템의 자동화 기능을 사용하는 방법입니다.

---

## 📋 목차

1. [시스템 구성](#시스템-구성)
2. [설치 및 설정](#설치-및-설정)
3. [수동 실행](#수동-실행)
4. [자동 스케줄링](#자동-스케줄링)
5. [모니터링](#모니터링)
6. [문제 해결](#문제-해결)

---

## 🏗️ 시스템 구성

### 주요 스크립트

| 파일명 | 설명 | 용도 |
|--------|------|------|
| `auto_weekly_collect.py` | 주간 데이터 수집 | 100건 자동 수집 |
| `auto_pipeline.py` | 전체 파이프라인 | 수집→학습→예측→분석 |
| `performance_monitor.py` | 성능 모니터링 | 지표 추적 및 분석 |
| `scheduler.py` | 작업 스케줄러 | 자동 실행 관리 |

### 배치 파일 (Windows)

| 파일명 | 설명 |
|--------|------|
| `start_scheduler.bat` | 스케줄러 시작 |
| `run_pipeline.bat` | 파이프라인 수동 실행 |
| `check_performance.bat` | 성능 확인 |

### 설정 파일

- `automation_config.json`: 자동화 설정

---

## ⚙️ 설치 및 설정

### 1. 필수 패키지 설치

```bash
pip install apscheduler
```

### 2. 설정 파일 수정

`automation_config.json` 파일을 열어서 설정을 변경하세요:

```json
{
  "weekly_collection_count": 100,  // 주간 수집 건수
  "max_retries": 3,                 // 최대 재시도 횟수
  "schedule": {
    "data_collection": {
      "enabled": true,
      "frequency": "weekly",
      "day_of_week": "monday",     // 요일: monday ~ sunday
      "time": "02:00"              // 실행 시간 (24시간 형식)
    },
    "model_retrain": {
      "enabled": true,
      "frequency": "weekly",
      "day_of_week": "monday",
      "time": "03:00"
    },
    "performance_check": {
      "enabled": true,
      "frequency": "daily",        // 매일 실행
      "time": "01:00"
    }
  }
}
```

---

## 🖐️ 수동 실행

### 1. 데이터 수집만 실행

```bash
python auto_weekly_collect.py
```

**결과**: 100건의 새로운 경매 데이터 수집

### 2. 전체 파이프라인 실행 (권장)

```bash
python auto_pipeline.py
```

**또는 Windows에서**:
```bash
run_pipeline.bat
```

**실행 단계**:
1. 데이터 100건 수집
2. 모델 재학습
3. 전체 데이터 재예측
4. 구간별 정확도 분석

**옵션**:
```bash
# 데이터 수집 건너뛰기 (재학습만)
python auto_pipeline.py --skip-collect

# 수집 건수 지정
python auto_pipeline.py --collect-count 200
```

### 3. 성능 모니터링 실행

```bash
python performance_monitor.py
```

**또는 Windows에서**:
```bash
check_performance.bat
```

**출력 정보**:
- 총 예측 건수
- 평균 오차율
- 구간별 성능
- 성능 저하 경고

---

## 🤖 자동 스케줄링

### 방법 1: Python 스케줄러 사용 (권장)

#### 시작

```bash
python scheduler.py
```

**또는 Windows에서**:
```bash
start_scheduler.bat
```

#### 백그라운드 실행 (Linux/Mac)

```bash
nohup python scheduler.py > logs/scheduler.log 2>&1 &
```

#### 중지

`Ctrl+C`를 누르거나 프로세스를 종료하세요.

### 방법 2: Windows 작업 스케줄러

1. **작업 스케줄러 열기**
   - `Win + R` → `taskschd.msc` 입력

2. **기본 작업 만들기**
   - 이름: "경매 예측 자동화"
   - 트리거: 매주 월요일 02:00
   - 작업: 프로그램 시작
   - 프로그램: `python.exe`
   - 인수: `auto_pipeline.py`
   - 시작 위치: 프로젝트 폴더 경로

### 방법 3: Linux Cron

`crontab -e`로 크론탭 편집:

```cron
# 매주 월요일 02:00에 데이터 수집
0 2 * * 1 cd /path/to/auction_gemini && python auto_pipeline.py

# 매일 01:00에 성능 체크
0 1 * * * cd /path/to/auction_gemini && python performance_monitor.py
```

---

## 📊 모니터링

### 로그 파일 위치

```
logs/
├── weekly_collect_YYYYMMDD_HHMMSS.log  # 데이터 수집 로그
├── pipeline_YYYYMMDD_HHMMSS.log        # 파이프라인 로그
├── scheduler_YYYYMMDD.log              # 스케줄러 로그
├── collection_history.json             # 수집 이력
├── pipeline_history.json               # 파이프라인 이력
└── metrics/
    ├── metrics_history.json            # 성능 지표 이력
    └── snapshot_YYYYMMDD_HHMMSS.json   # 성능 스냅샷
```

### 성능 지표 확인

```bash
python performance_monitor.py
```

**출력 예시**:
```
================================================================================
📊 현재 모델 성능 지표
================================================================================
조회 시간: 2026-02-12 20:00:00
총 예측 건수: 1,110건
평균 오차율: 2.79%
평균 오차 금액: 38,502,854원
최소 오차율: 0.00%
최대 오차율: 147.89%

구간별 성능:
  1억 이하: 170건, 오차율 2.66%
  1억~3억: 617건, 오차율 1.76%
  3억~5억: 116건, 오차율 2.67%
  5억~10억: 151건, 오차율 1.39%
  10억 초과: 56건, 오차율 18.58%
================================================================================
```

### 성능 추이 분석

`logs/metrics/metrics_history.json` 파일을 확인하여 시간에 따른 성능 변화를 추적할 수 있습니다.

---

## 🛠️ 문제 해결

### 1. 스케줄러가 시작되지 않음

**증상**: `ModuleNotFoundError: No module named 'apscheduler'`

**해결**:
```bash
pip install apscheduler
```

### 2. 데이터 수집 실패

**증상**: "처리된 데이터가 없습니다"

**원인**: API 연결 실패 또는 데이터 부족

**해결**:
- 인터넷 연결 확인
- API 키 확인 (`.env` 파일)
- 재시도 횟수 증가: `automation_config.json`의 `max_retries` 수정

### 3. 성능 저하 경고

**증상**: "⚠️ 성능 저하 감지!"

**해결**:
1. 데이터 추가 수집:
   ```bash
   python auto_weekly_collect.py
   ```

2. 전체 파이프라인 재실행:
   ```bash
   python auto_pipeline.py
   ```

3. 이상치 데이터 확인 및 제거

### 4. 로그 파일 용량 증가

**해결**: 오래된 로그 파일 수동 삭제

```bash
# Windows
del logs\*.log

# Linux/Mac
rm logs/*.log
```

---

## 📅 권장 스케줄

| 작업 | 빈도 | 시간 | 목적 |
|------|------|------|------|
| 데이터 수집 | 주 1회 | 월요일 02:00 | 신규 데이터 확보 |
| 모델 재학습 | 주 1회 | 월요일 03:00 | 성능 유지/개선 |
| 성능 모니터링 | 매일 | 01:00 | 이상 감지 |

---

## ⚡ 빠른 시작

### 첫 실행 (테스트)

```bash
# 1. 성능 확인
python performance_monitor.py

# 2. 전체 파이프라인 실행 (데이터 수집 건너뜀)
python auto_pipeline.py --skip-collect

# 3. 문제 없으면 스케줄러 시작
python scheduler.py
```

### 정기 유지보수

```bash
# 매주 월요일 또는 필요시 실행
python auto_pipeline.py
```

---

## 📞 지원

문제가 발생하거나 질문이 있으면:

1. 로그 파일 확인: `logs/` 디렉토리
2. 설정 파일 검토: `automation_config.json`
3. 수동 실행 테스트: `python auto_pipeline.py --skip-collect`

---

**작성일**: 2026-02-12
**버전**: 1.0
