# 밸류옥션(valueauction.co.kr) API 분석 리포트

작성일: 2026-02-09

---

## 🔍 웹사이트 분석 결과

### 기술 스택
- **프레임워크**: SvelteKit (클라이언트 사이드 렌더링)
- **데이터 로딩**: JavaScript를 통한 동적 로딩
- **특징**: 초기 HTML에는 데이터 없음, API 호출로 데이터 획득

### 제공 기능
1. **경매일정** - 예정된 경매 물건
2. **경매신건** - 새로 등록된 물건
3. **매각결과** - 낙찰 완료 물건 ⭐ (우리가 필요한 데이터!)
4. **검색** - 다양한 필터링 옵션

---

## 🔧 API 엔드포인트 찾는 방법

### 방법 1: 브라우저 개발자 도구 사용 (추천)

**1단계: 크롬 개발자 도구 열기**
```
1. https://valueauction.co.kr 접속
2. F12 키 누르기 (또는 우클릭 → 검사)
3. "Network" 탭 선택
4. "Fetch/XHR" 필터 클릭
```

**2단계: 데이터 로드 확인**
```
1. "매각결과" 탭 클릭
2. Network 탭에서 새로운 요청 확인
3. 요청 URL 복사
```

**예상되는 API 패턴:**
```
https://valueauction.co.kr/api/auction/results
https://valueauction.co.kr/api/search
https://valueauction.co.kr/api/sold
```

**3단계: 요청 분석**
```
1. 요청 클릭 → Headers 탭
2. Request URL 확인
3. Request Method (GET/POST) 확인
4. Query Parameters 또는 Payload 확인
```

**4단계: 응답 확인**
```
1. Response 탭 클릭
2. JSON 데이터 구조 확인
3. 필요한 필드 식별:
   - 사건번호
   - 낙찰가
   - 낙찰일자
   - 감정가
   - 물건종류
   - 지역
```

---

## 💻 API 테스트 예시

### Python으로 API 호출 테스트

```python
import requests
import json

# 1. 브라우저에서 찾은 API URL
api_url = "https://valueauction.co.kr/api/auction/results"  # 예시

# 2. 헤더 설정 (브라우저에서 복사)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://valueauction.co.kr/search"
}

# 3. 요청 파라미터 (브라우저에서 확인한 것)
params = {
    "status": "sold",  # 낙찰 완료
    "page": 1,
    "limit": 20
}

# 4. API 호출
response = requests.get(api_url, headers=headers, params=params)

# 5. 응답 확인
if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
else:
    print(f"오류: {response.status_code}")
```

---

## 📊 데이터 수집 전략

### 전략 A: API 직접 호출 (권장)

**장점:**
- ✅ 빠르고 효율적
- ✅ 깨끗한 JSON 데이터
- ✅ 대량 수집 가능

**단점:**
- ⚠️ API 엔드포인트 찾기 필요
- ⚠️ 인증/제한 있을 수 있음

**수집 워크플로우:**
```python
# 1. 낙찰 완료 물건 목록 가져오기
results = fetch_sold_auctions(page=1, limit=50)

# 2. 각 물건 정보 추출
for item in results:
    case_no = item['사건번호']
    actual_price = item['낙찰가']
    actual_date = item['낙찰일']
    appraisal = item['감정가']

    # 3. 우리 DB에 예측 생성
    predict_result = predict_price(appraisal, ...)

    # 4. 즉시 검증
    verify_result(case_no, actual_price, actual_date)
```

### 전략 B: 셀레니움 크롤링

**상황:** API를 찾을 수 없는 경우

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

driver = webdriver.Chrome()
driver.get("https://valueauction.co.kr/search")

# 매각결과 탭 클릭
result_tab = driver.find_element(By.XPATH, "//button[contains(text(), '매각결과')]")
result_tab.click()
time.sleep(2)

# 물건 목록 크롤링
items = driver.find_elements(By.CLASS_NAME, "auction-item")
for item in items:
    # 데이터 추출
    pass
```

---

## ⚖️ 법적 고려사항

### 확인 필요 사항
1. **이용약관** 확인
   - 자동화 도구 사용 금지 여부
   - API 사용 제한
   - 데이터 재배포 제한

2. **robots.txt** 확인
   ```
   https://valueauction.co.kr/robots.txt
   ```

3. **요청 제한**
   - 과도한 요청 방지 (1초당 1-2회)
   - 정중한 크롤링 (User-Agent 명시)

### 안전한 사용 원칙
```python
import time

# 요청 간 딜레이
time.sleep(1)  # 1초 대기

# 정중한 User-Agent
headers = {
    "User-Agent": "AuctionPredictionBot/1.0 (Contact: your@email.com)"
}
```

---

## 🚀 구현 계획

### Phase 1: API 탐색 (수동, 30분)
```
1. 브라우저에서 valueauction.co.kr 접속
2. 개발자 도구로 Network 요청 분석
3. API 엔드포인트 문서화
4. 테스트 요청 실행
```

### Phase 2: 데이터 수집 스크립트 (2시간)
```python
# valueauction_crawler.py

import requests
from database import db
from main import predict_price_advanced

def fetch_sold_auctions(limit=50):
    """밸류옥션에서 낙찰 완료 물건 가져오기"""
    # API URL (브라우저에서 확인한 것)
    api_url = "https://valueauction.co.kr/api/..."

    response = requests.get(api_url, params={"limit": limit})
    return response.json()

def collect_and_verify():
    """낙찰 물건 수집 → 예측 → 검증"""
    items = fetch_sold_auctions(limit=50)

    for item in items:
        # 1. 예측 생성
        prediction = predict_price_advanced(
            start_price=item['감정가'],
            property_type=item['물건종류'],
            region=item['지역'],
            # ...
        )

        # 2. DB 저장
        db.save_prediction(...)

        # 3. 실제 낙찰가로 검증
        db.update_actual_result(
            case_no=...,
            actual_price=item['낙찰가'],
            actual_date=item['낙찰일']
        )

        time.sleep(1)  # 요청 제한

if __name__ == "__main__":
    collect_and_verify()
```

### Phase 3: 자동화 (선택)
```bash
# 매일 자동 수집 (Windows 작업 스케줄러)
매일 오전 9시: python valueauction_crawler.py

# 또는 Python 스케줄러
import schedule
schedule.every().day.at("09:00").do(collect_and_verify)
```

---

## 📋 다음 단계

### 즉시 시작 (수동 조사)
```
1. 브라우저에서 https://valueauction.co.kr 열기
2. F12 → Network 탭
3. "매각결과" 클릭
4. API 요청 URL 찾기
5. 메모장에 기록:
   - URL
   - Method (GET/POST)
   - Parameters
   - Response 샘플
```

### API 확인 후
```
1. Python 테스트 스크립트 작성
2. 10건 샘플 데이터 수집
3. 데이터 구조 확인
4. 자동 수집 스크립트 구현
```

---

## 💡 대안 데이터 소스

### 1. 법원 경매 공식 사이트
```
URL: https://www.courtauction.go.kr
장점: 공식 데이터, 신뢰도 높음
단점: 크롤링 어려움, 접근 제한
```

### 2. 지지옥션
```
URL: https://www.ggi.co.kr
장점: 상세한 낙찰 정보
```

### 3. 온비드
```
URL: https://www.onbid.co.kr
장점: 공매 정보 포함
```

---

## 🎯 권장 사항

### 초기 단계
1. **수동 조사 먼저**: 브라우저에서 API 확인 (30분)
2. **소량 테스트**: 10-20건만 수집해서 검증
3. **자동화 결정**: 효과 확인 후 자동화 진행

### 목표 달성
- **단기 (1주)**: 수동으로 50건 수집
- **중기 (1개월)**: 반자동으로 200건
- **장기 (3개월)**: 완전 자동화로 500건

---

## 📞 빠른 실행 가이드

### 1분 만에 시작하기
```bash
# 1. 브라우저 열기
start https://valueauction.co.kr

# 2. F12 누르기
# 3. Network 탭 클릭
# 4. Fetch/XHR 필터 선택
# 5. "매각결과" 클릭
# 6. 첫 번째 요청 클릭
# 7. URL 복사
```

---

**작성일:** 2026-02-09
**작성자:** Claude Code
**상태:** API 탐색 필요
