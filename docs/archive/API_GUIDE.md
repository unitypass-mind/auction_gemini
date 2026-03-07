# 법원 경매 데이터 API 연동 가이드

작성일: 2026-02-03
프로젝트: AI 경매 낙찰가 예측 시스템

---

## 📋 목차

1. [조사 결과 요약](#조사-결과-요약)
2. [사용 가능한 API 옵션](#사용-가능한-api-옵션)
3. [추천 방안](#추천-방안)
4. [API 신청 절차](#api-신청-절차)
5. [구현 계획](#구현-계획)

---

## 🔍 조사 결과 요약

### 법원 경매 데이터 제공 현황

1. **대법원 법원경매정보제공 시스템** (https://www.courtauction.go.kr)
   - 공식 법원 경매 사이트
   - ❌ 공개 API 없음
   - ❌ 봇/크롤링 차단 (Selenium 접근 불가 확인)
   - ⚠️ "시스템 작업 안내" 차단 페이지 표시

2. **사법정보공유포털** (https://openapi.scourt.go.kr)
   - 대한민국 법원의 공식 API 포털
   - 📧 문의: publicapi@scourt.go.kr
   - ☎️ 전화: 02-3480-1715 (평일 9시~18시)
   - ⚠️ 경매 API는 현재 개발 중 또는 제한적 제공
   - 인증키 발급 필요 (기본 2년 기간)

3. **공공데이터포털** (https://www.data.go.kr)
   - 한국주택금융공사 법적절차진행이력정보
   - 파일 데이터 형태 (Open API 아님)
   - 2015년 경매 정보 관련 분쟁 사례 있음

4. **대한민국 법원 등기정보광장** (https://data.iros.go.kr)
   - Open API 제공
   - 등기 정보 중심 (경매 정보는 제한적)
   - 서비스별 인증키 발급 필요

---

## 💡 사용 가능한 API 옵션

### ✅ 옵션 1: 사법정보공유포털 API 신청 (공식, 무료 추정)

**장점:**
- 공식 법원 API
- 무료 (예상)
- 법적 문제 없음
- 정확한 실시간 데이터

**단점:**
- 신청 및 승인 필요 (소요 시간: 3-14일 추정)
- 경매 API 제공 여부 확인 필요
- 인증키 발급 절차 필요

**신청 방법:**
1. openapi.scourt.go.kr 접속
2. 회원가입 및 API 사용 신청
3. 인증키 발급 대기
4. API 문서 확인 후 구현

**문의처:**
- 이메일: publicapi@scourt.go.kr
- 전화: 02-3480-1715

---

### ✅ 옵션 2: CODEF API (상용, 유료)

**개요:**
- 금융/공공 데이터 통합 플랫폼
- URL: https://developer.codef.io
- 법원 경매 정보 제공 (확인 필요)

**장점:**
- 즉시 사용 가능
- 안정적인 서비스
- 기술 지원

**단점:**
- 월 사용료 발생 (수만원 추정)
- 비용 부담

**신청 방법:**
1. CODEF 개발자 사이트 회원가입
2. API 키 발급
3. 요금제 선택
4. 문서 확인 후 구현

---

### ✅ 옵션 3: 오픈소스 프로젝트 활용 (CAUCA)

**프로젝트:** https://github.com/guriguri/cauca

**설명:**
- Court AUCtion Api service
- Clojure 기반 크롤링 + REST API
- 법원 경매 사이트 크롤링하여 자체 API 제공

**장점:**
- 무료
- 즉시 사용 가능 (설치 후)
- 커스터마이징 가능

**단점:**
- Clojure 환경 필요
- 유지보수 필요
- 법원 사이트 변경 시 수정 필요
- 최신 업데이트 여부 확인 필요

---

### ✅ 옵션 4: 샘플 DB 활용 (현재 권장)

**개요:**
- 현재 보유한 2000건 샘플 데이터 활용
- CSV 파일 기반 검색

**장점:**
- ✅ 즉시 구현 가능 (5분)
- ✅ 법적 문제 없음
- ✅ 안정적이고 빠름
- ✅ 비용 없음

**단점:**
- 실시간 데이터 아님
- 제한된 물건 수 (2000건)

**구현 방법:**
```python
# data/auction_data.csv에서 물건번호 검색
# 패턴 매칭으로 유사 데이터 생성
```

---

## 🎯 추천 방안

### 🏆 단기 (즉시~1주): 옵션 4 (샘플 DB)
- 현재 시스템에 즉시 적용
- 사용자에게 기능 제공 시작

### 🏆 중기 (1주~1개월): 옵션 1 (사법정보공유포털) + 옵션 4
1. **병행 진행:**
   - 샘플 DB로 서비스 운영
   - 동시에 사법정보공유포털 API 신청

2. **API 승인 후:**
   - 실시간 API로 전환
   - 샘플 DB는 백업으로 유지

### 🏆 장기 (1개월 이후): 옵션 2 (CODEF) 고려
- 트래픽 증가 시
- 비즈니스 모델 확립 후
- 유료 서비스 전환 시

---

## 📝 API 신청 절차

### 1단계: 사법정보공유포털 API 신청

#### A. 회원가입 및 신청
```
1. https://openapi.scourt.go.kr 접속
2. 회원가입 (일반 또는 기관)
3. "API 사용신청" 메뉴 선택
4. 신청서 작성:
   - 서비스명: AI 경매 낙찰가 예측 시스템
   - 사용목적: 경매 물건 정보 조회 및 예측
   - 사용기간: 2년 (기본)
   - 트래픽: 1일 1,000건 (예상)
```

#### B. 필요 정보 준비
- 사업자등록증 (법인) 또는 신분증 (개인)
- 서비스 설명서
- 개인정보처리방침 (필요 시)

#### C. 승인 대기
- 승인 기간: 3-14일 (추정)
- 승인 결과: 이메일 통보
- 인증키 발급: API-KEY 방식

#### D. 확인 사항
- 경매 API 제공 여부 확인
- 제공 데이터 항목 확인
- 사용 제한 (호출 횟수, 기간 등)

---

### 2단계: 대안 - CODEF API 신청 (유료)

```
1. https://developer.codef.io 접속
2. 회원가입
3. 상품 > 공공데이터 > 법원경매정보 선택
4. 요금제 확인 및 선택
5. API 키 발급 (즉시)
6. 개발 가이드 확인
```

---

## 🛠️ 구현 계획

### Phase 1: 샘플 DB 활용 (즉시 구현)

#### 구현 내용
```python
# main.py 수정
def get_auction_item_from_db(item_no: str) -> Dict[str, Any]:
    """
    CSV 파일에서 물건번호로 검색
    """
    import pandas as pd

    # CSV 파일 로드
    df = pd.read_csv("data/auction_data.csv")

    # 물건번호로 검색
    result = df[df['물건번호'] == item_no]

    if not result.empty:
        # 데이터 있으면 반환
        return result.iloc[0].to_dict()
    else:
        # 없으면 유사 패턴 생성
        return generate_similar_data(item_no)
```

#### 소요 시간: 10분

---

### Phase 2: 사법정보공유포털 API 연동 (승인 후)

#### 구현 내용
```python
# auction_api.py (새 파일)
import requests
from typing import Dict, Any

class CourtAuctionAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openapi.scourt.go.kr/api/..."

    def get_auction_info(self, item_no: str) -> Dict[str, Any]:
        """
        사법정보공유포털 API로 경매 정보 조회
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        params = {
            "itemNo": item_no
        }

        response = requests.get(
            f"{self.base_url}/auction/info",
            headers=headers,
            params=params
        )

        return response.json()
```

#### main.py 통합
```python
# main.py
from auction_api import CourtAuctionAPI

# API 초기화 (환경변수에서 키 로드)
api_key = os.getenv("SCOURT_API_KEY")
if api_key:
    court_api = CourtAuctionAPI(api_key)

def get_auction_item(item_no: str) -> Dict[str, Any]:
    """
    1. API가 있으면 API 사용
    2. API 없으면 샘플 DB 사용
    """
    if court_api:
        try:
            return court_api.get_auction_info(item_no)
        except Exception as e:
            logger.warning(f"API 호출 실패, 샘플 DB 사용: {e}")
            return get_auction_item_from_db(item_no)
    else:
        return get_auction_item_from_db(item_no)
```

---

### Phase 3: CODEF API 연동 (선택, 유료)

#### .env 설정
```env
# CODEF API
CODEF_CLIENT_ID=your_client_id
CODEF_CLIENT_SECRET=your_client_secret
CODEF_PUBLIC_KEY=your_public_key
```

#### 구현 예시
```python
import requests
import base64

class CodefAPI:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None

    def get_token(self):
        """OAuth 토큰 발급"""
        url = "https://oauth.codef.io/oauth/token"
        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "client_credentials",
            "scope": "read"
        }

        response = requests.post(url, headers=headers, data=data)
        self.access_token = response.json()["access_token"]

    def get_auction_info(self, item_no: str):
        """경매 정보 조회"""
        if not self.access_token:
            self.get_token()

        url = "https://api.codef.io/v1/kr/public/..."
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        body = {
            "organization": "0001",  # 법원
            "itemNo": item_no
        }

        response = requests.post(url, headers=headers, json=body)
        return response.json()
```

---

## 📞 연락처 및 문의

### 사법정보공유포털
- 웹사이트: https://openapi.scourt.go.kr
- 이메일: publicapi@scourt.go.kr
- 전화: 02-3480-1715 (평일 9-18시)

### CODEF
- 웹사이트: https://developer.codef.io
- 이메일: contact@codef.io (추정)

### 공공데이터포털
- 웹사이트: https://www.data.go.kr
- 고객센터: 1577-0133

---

## 📌 다음 단계

### 즉시 실행
1. ✅ 샘플 DB 기반 검색 기능 구현 (10분)
2. ✅ main.py 수정 및 테스트

### 병행 진행
3. ⏳ 사법정보공유포털 API 신청
   - 회원가입 및 신청서 작성
   - 승인 대기 (3-14일)
   - 인증키 발급 확인

4. ⏳ API 연동 코드 준비
   - auction_api.py 작성
   - .env 설정 준비
   - 테스트 코드 작성

### 선택 사항
5. 🔍 CODEF API 요금 조사
6. 🔍 오픈소스 CAUCA 프로젝트 분석

---

**작성자:** Claude Code
**업데이트:** 필요 시 지속 업데이트
