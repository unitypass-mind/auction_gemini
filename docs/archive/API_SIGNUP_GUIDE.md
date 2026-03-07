# 법원 경매 API 신청 단계별 가이드

작성일: 2026-02-03
대상: 대한민국 법원 등기정보광장 Open API

---

## 📌 시작하기 전에

### 필요한 준비물
- [ ] 이메일 주소 (회원가입용)
- [ ] 휴대폰 (본인인증)
- [ ] 신분증 또는 사업자등록증 (필요 시)
- [ ] 서비스 설명 자료 (간단한 문서)

### 예상 소요 시간
- **신청 작성**: 20-30분
- **승인 대기**: 3-14일 (영업일 기준)

---

## 🚀 Step 1: 사이트 접속 및 회원가입

### 1-1. 법원 등기정보광장 접속

```
URL: https://data.iros.go.kr
```

**화면에서 찾을 메뉴:**
- 우측 상단 "로그인" 또는 "회원가입" 버튼

### 1-2. 회원가입 진행

#### A. 회원 유형 선택
```
□ 개인회원 (개인 개발자, 스타트업)
□ 기업회원 (법인 사업자)
□ 기관회원 (공공기관, 학교)
```

**추천:** 개인 프로젝트라면 "개인회원" 선택

#### B. 약관 동의
```
□ 이용약관 동의 (필수)
□ 개인정보 수집 및 이용 동의 (필수)
□ 마케팅 정보 수신 동의 (선택)
```

#### C. 정보 입력
```
- 이메일: your_email@example.com
- 비밀번호: *********** (8자 이상, 영문+숫자+특수문자)
- 이름: 홍길동
- 휴대폰: 010-1234-5678
- 생년월일: 1990-01-01
```

#### D. 본인인증
```
□ 휴대폰 인증
□ 아이핀 인증
□ 공동인증서 (구 공인인증서)
```

**추천:** 휴대폰 인증 (가장 빠름)

#### E. 회원가입 완료
```
✅ 인증 메일 확인 (이메일 인증)
✅ 로그인 테스트
```

---

## 🚀 Step 2: Open API 메뉴 접속

### 2-1. 로그인 후 메뉴 찾기

```
메인 페이지 → "Open API" 메뉴 클릭
또는
메인 페이지 → "서비스" → "Open API"
```

### 2-2. Open API 소개 페이지 확인

**확인 사항:**
- [ ] 제공하는 API 목록
- [ ] 이용 요금 (무료/유료)
- [ ] 이용 제한 (월 1,000건 등)
- [ ] 신청 자격

---

## 🚀 Step 3: Open API 신청서 작성

### 3-1. "API 신청" 버튼 클릭

```
Open API 페이지 → "API 신청하기" 또는 "신청" 버튼
```

### 3-2. 신청서 작성 (9단계 프로세스)

#### ✏️ 신청서 양식 예시

```
┌─────────────────────────────────────────────┐
│         Open API 이용 신청서                 │
└─────────────────────────────────────────────┘

1️⃣ 신청자 정보
   - 이름: 홍길동
   - 이메일: your_email@example.com
   - 연락처: 010-1234-5678
   - 소속: 개인 / 프리랜서 / 회사명

2️⃣ 서비스 정보
   - 서비스명: AI 경매 낙찰가 예측 시스템
   - 서비스 유형: 웹 애플리케이션
   - 서비스 URL: http://your-domain.com (또는 "개발 중")
   - 개발 언어: Python (FastAPI)

3️⃣ 사용 목적
   ┌──────────────────────────────────────────┐
   │ 법원 경매 물건 정보를 조회하여            │
   │ AI 머신러닝 모델로 낙찰가를 예측하는      │
   │ 서비스를 개발하고 있습니다.              │
   │                                          │
   │ 사용자가 물건번호를 입력하면             │
   │ 해당 경매 물건의 상세 정보를 조회하고,    │
   │ 감정가, 입찰자 수 등의 데이터를 기반으로  │
   │ 예상 낙찰가를 제공합니다.                │
   │                                          │
   │ 개인 프로젝트이며, 비상업적 용도입니다.   │
   └──────────────────────────────────────────┘

4️⃣ 필요한 API 선택
   □ 부동산 경매 물건 조회 API
   □ 경매 입찰 정보 조회 API
   □ 경매 진행 상태 조회 API
   □ 기타: ___________________________

5️⃣ 예상 사용량
   - 일평균 호출 횟수: 100건
   - 월평균 호출 횟수: 3,000건
   - 최대 동시 사용자: 10명

6️⃣ 사용 기간
   - 시작일: 2026-02-03
   - 종료일: 2028-02-03 (2년, 기본값)
   □ 장기 사용 (2년 이상)

7️⃣ 개인정보 처리
   - 개인정보 수집 여부: □ 예  ☑ 아니오
   - 개인정보 처리방침: (URL 또는 "해당없음")

8️⃣ 첨부 서류 (선택)
   □ 서비스 소개서 (PDF)
   □ 사업자등록증 (법인일 경우)
   □ 개인정보처리방침 (개인정보 수집 시)

9️⃣ 약관 동의
   ☑ Open API 이용약관 동의
   ☑ 개인정보 제3자 제공 동의
   ☑ 데이터 이용 정책 동의
```

### 3-3. 신청서 제출

```
1. 입력 내용 최종 확인
2. "신청하기" 버튼 클릭
3. 신청 완료 메시지 확인
4. 신청번호 메모 (예: API-2026020301)
```

---

## 🚀 Step 4: 신청 결과 확인

### 4-1. 신청 내역 확인

```
마이페이지 → "API 신청 내역" → 상태 확인
```

**상태 종류:**
- 🟡 **신청 완료**: 검토 대기 중
- 🟢 **승인**: API 사용 가능
- 🔴 **반려**: 추가 정보 필요 또는 거절
- 🔵 **보완 요청**: 정보 수정 필요

### 4-2. 이메일 확인

```
수신 이메일 예시:

제목: [법원 등기정보광장] Open API 신청이 접수되었습니다.

안녕하세요, 홍길동님.

Open API 신청이 정상적으로 접수되었습니다.

- 신청번호: API-2026020301
- 신청일시: 2026-02-03 14:30:00
- 서비스명: AI 경매 낙찰가 예측 시스템

검토 결과는 영업일 기준 3-7일 이내에
이메일로 안내드리겠습니다.

감사합니다.
```

---

## 🚀 Step 5: 승인 대기 (3-14일)

### 5-1. 대기 기간 할 일

#### A. 개발 환경 준비
```bash
# 가상환경 생성
python -m venv venv

# 필요한 패키지 설치
pip install requests python-dotenv
```

#### B. API 연동 코드 작성 (템플릿)
```python
# court_api.py
import requests
from typing import Dict, Any

class CourtAuctionAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://data.iros.go.kr/api/v1"

    def get_auction_info(self, item_no: str) -> Dict[str, Any]:
        """경매 물건 정보 조회"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 실제 API 엔드포인트는 승인 후 문서 확인 필요
        endpoint = f"{self.base_url}/auction/{item_no}"

        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()

        return response.json()
```

#### C. .env 파일 준비
```env
# .env
COURT_API_KEY=발급받을_API_키
COURT_API_BASE_URL=https://data.iros.go.kr/api/v1
```

### 5-2. 추가 문의 (필요 시)

```
📧 이메일: (사이트에서 확인)
📞 전화: 1577-1691 (등기정보광장 고객센터)
🕐 운영시간: 평일 9:00-18:00
```

**문의 시 준비 사항:**
- 신청번호: API-2026020301
- 등록 이메일: your_email@example.com
- 문의 내용: "API 승인 진행 상황 문의"

---

## 🚀 Step 6: 승인 완료 및 인증키 발급

### 6-1. 승인 이메일 수신

```
제목: [법원 등기정보광장] Open API 신청이 승인되었습니다.

안녕하세요, 홍길동님.

Open API 신청이 승인되었습니다.

- 신청번호: API-2026020301
- 승인일시: 2026-02-10 10:00:00
- 서비스명: AI 경매 낙찰가 예측 시스템

인증키는 마이페이지에서 확인하실 수 있습니다.

📌 중요 사항:
- 월 1,000건 이용 제한
- 3개월 미사용 시 인증키 자동 폐지
- 인증키 외부 유출 금지

감사합니다.
```

### 6-2. 인증키 확인 및 복사

```
1. 로그인
2. 마이페이지 → "API 관리"
3. "인증키 보기" 버튼 클릭
4. 인증키 복사 (예: abc123def456ghi789...)
```

#### 인증키 예시
```
API Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
발급일: 2026-02-10
만료일: 2028-02-10 (2년)
상태: 활성화
```

### 6-3. 인증키 저장

```bash
# .env 파일 수정
echo "COURT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." >> .env
```

---

## 🚀 Step 7: API 문서 다운로드 및 확인

### 7-1. API 매뉴얼 다운로드

```
마이페이지 → "API 관리" → "API 문서 다운로드"
```

**다운로드 파일:**
- `API_Guide.pdf` - 전체 가이드
- `API_Reference.pdf` - API 레퍼런스
- `Sample_Code.zip` - 샘플 코드 (Java, Python 등)

### 7-2. 주요 확인 사항

#### A. API 엔드포인트
```
Base URL: https://data.iros.go.kr/api/v1

엔드포인트 예시:
- GET /auction/info/{itemNo} - 물건 정보 조회
- GET /auction/list - 물건 목록 조회
- GET /auction/status/{itemNo} - 진행 상태 조회
```

#### B. 인증 방식
```
HTTP Header:
Authorization: Bearer {API_KEY}
Content-Type: application/json
```

#### C. 응답 형식
```json
{
  "resultCode": "0000",
  "resultMsg": "성공",
  "data": {
    "itemNo": "20240000001",
    "caseNo": "2024타경12345",
    "courtName": "서울중앙지방법원",
    "itemType": "아파트",
    "location": "서울특별시 강남구",
    "appraisalPrice": 300000000,
    "minBidPrice": 300000000,
    "bidDate": "2026-02-15",
    "status": "진행중"
  }
}
```

#### D. 에러 코드
```
0000: 성공
1001: 인증 실패 (잘못된 API Key)
1002: 권한 없음
2001: 물건번호 없음
2002: 데이터 없음
9999: 서버 오류
```

---

## 🚀 Step 8: 테스트 API 호출

### 8-1. Postman으로 테스트

#### A. Postman 설치 및 설정
```
1. Postman 다운로드: https://www.postman.com/downloads/
2. 설치 및 실행
3. "New Request" 생성
```

#### B. 요청 설정
```
Method: GET
URL: https://data.iros.go.kr/api/v1/auction/info/20240000001

Headers:
- Authorization: Bearer {YOUR_API_KEY}
- Content-Type: application/json
```

#### C. 요청 전송 및 응답 확인
```
Send 버튼 클릭
→ Status: 200 OK
→ Response 확인
```

### 8-2. Python으로 테스트

```python
# test_api.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_court_api():
    """법원 경매 API 테스트"""

    api_key = os.getenv("COURT_API_KEY")
    base_url = os.getenv("COURT_API_BASE_URL")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 테스트 물건번호
    item_no = "20240000001"
    url = f"{base_url}/auction/info/{item_no}"

    try:
        print(f"API 호출: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        print("✅ API 호출 성공!")
        print(f"결과 코드: {data.get('resultCode')}")
        print(f"결과 메시지: {data.get('resultMsg')}")
        print(f"\n물건 정보:")
        print(f"- 물건번호: {data['data']['itemNo']}")
        print(f"- 사건번호: {data['data']['caseNo']}")
        print(f"- 감정가: {data['data']['appraisalPrice']:,}원")

        return data

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP 오류: {e}")
        print(f"응답 내용: {e.response.text}")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_court_api()
```

#### 실행
```bash
python test_api.py
```

#### 예상 출력
```
API 호출: https://data.iros.go.kr/api/v1/auction/info/20240000001
✅ API 호출 성공!
결과 코드: 0000
결과 메시지: 성공

물건 정보:
- 물건번호: 20240000001
- 사건번호: 2024타경12345
- 감정가: 300,000,000원
```

---

## 🚀 Step 9: main.py에 API 통합

### 9-1. court_api.py 파일 작성

```python
# court_api.py
import requests
import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class CourtAuctionAPI:
    """법원 경매 API 클래스"""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url

    def get_auction_info(self, item_no: str) -> Dict[str, Any]:
        """
        경매 물건 정보 조회

        Args:
            item_no: 물건번호

        Returns:
            경매 물건 정보 딕셔너리

        Raises:
            HTTPError: API 호출 실패
            ValueError: 잘못된 응답 형식
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}/auction/info/{item_no}"

        try:
            logger.info(f"API 호출: {item_no}")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 결과 코드 확인
            if data.get("resultCode") != "0000":
                raise ValueError(f"API 오류: {data.get('resultMsg')}")

            # 데이터 정규화
            auction_data = data.get("data", {})

            return {
                "물건번호": auction_data.get("itemNo"),
                "사건번호": auction_data.get("caseNo"),
                "법원명": auction_data.get("courtName"),
                "물건종류": auction_data.get("itemType"),
                "위치": auction_data.get("location"),
                "감정가": f"{auction_data.get('appraisalPrice'):,}원",
                "감정가_숫자": auction_data.get("appraisalPrice"),
                "최저입찰가": auction_data.get("minBidPrice"),
                "입찰일": auction_data.get("bidDate"),
                "상태": auction_data.get("status"),
                "크롤링방식": "Court API"
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"API 호출 실패: {e}")
            raise

        except Exception as e:
            logger.error(f"데이터 처리 실패: {e}")
            raise

# API 싱글톤 인스턴스
_court_api_instance = None

def get_court_api() -> CourtAuctionAPI:
    """Court API 인스턴스 반환"""
    global _court_api_instance

    if _court_api_instance is None:
        api_key = os.getenv("COURT_API_KEY")
        base_url = os.getenv("COURT_API_BASE_URL", "https://data.iros.go.kr/api/v1")

        if not api_key:
            raise ValueError("COURT_API_KEY 환경변수가 설정되지 않았습니다")

        _court_api_instance = CourtAuctionAPI(api_key, base_url)

    return _court_api_instance
```

### 9-2. main.py 수정

```python
# main.py에 추가

from court_api import get_court_api, CourtAuctionAPI

# 전역 변수
court_api = None

# 앱 시작 시 초기화
try:
    court_api = get_court_api()
    logger.info("법원 경매 API 초기화 성공")
except Exception as e:
    logger.warning(f"법원 경매 API 초기화 실패: {e}")
    logger.warning("샘플 DB 모드로 작동합니다")


def get_auction_item(item_no: str) -> Dict[str, Any]:
    """
    경매 물건 정보 조회 (API 우선, 실패 시 샘플 DB)
    """
    # 1. API 시도
    if court_api:
        try:
            logger.info(f"Court API로 조회: {item_no}")
            return court_api.get_auction_info(item_no)
        except Exception as e:
            logger.warning(f"API 조회 실패, 샘플 DB 사용: {e}")

    # 2. API 실패 또는 없으면 샘플 DB 사용
    logger.info(f"샘플 DB에서 조회: {item_no}")
    return get_auction_item_from_db(item_no)


def get_auction_item_from_db(item_no: str) -> Dict[str, Any]:
    """
    샘플 DB에서 물건번호 검색
    """
    import pandas as pd

    try:
        df = pd.read_csv("data/auction_data.csv")
        result = df[df['물건번호'] == item_no]

        if not result.empty:
            data = result.iloc[0].to_dict()
            data['크롤링방식'] = "Sample DB"
            return data
        else:
            # 더미 데이터 반환
            return create_dummy_data(item_no)

    except Exception as e:
        logger.error(f"샘플 DB 조회 실패: {e}")
        return create_dummy_data(item_no)
```

---

## ✅ 완료 체크리스트

### 신청 전
- [ ] 회원가입 완료
- [ ] 로그인 확인
- [ ] 서비스 목적 정리
- [ ] 예상 사용량 계산

### 신청 중
- [ ] API 신청서 작성
- [ ] 신청 번호 확인
- [ ] 신청 접수 이메일 수신

### 승인 대기
- [ ] 개발 환경 준비
- [ ] API 연동 코드 작성 (템플릿)
- [ ] .env 파일 준비

### 승인 후
- [ ] 승인 이메일 확인
- [ ] 인증키 복사 및 저장
- [ ] API 문서 다운로드
- [ ] Postman 테스트
- [ ] Python 테스트 코드 실행
- [ ] main.py 통합
- [ ] 전체 시스템 테스트

---

## 🆘 문제 해결 (Troubleshooting)

### Q1: 승인이 너무 오래 걸려요
```
A:
1. 신청 내역에서 상태 확인
2. 영업일 기준 7일 이상이면 고객센터 전화
3. 신청번호 준비하고 문의
```

### Q2: 승인이 반려되었어요
```
A:
1. 반려 사유 확인 (이메일 또는 사이트)
2. 부족한 정보 보완
3. 재신청 또는 고객센터 문의
```

### Q3: 인증키가 작동하지 않아요
```
A:
1. 인증키 복사 확인 (공백 포함 여부)
2. Bearer 토큰 형식 확인
3. API 문서의 인증 방식 재확인
4. 테스트 엔드포인트로 확인
```

### Q4: 경매 API가 목록에 없어요
```
A:
1. 사법정보공유포털에 직접 문의
   📧 publicapi@scourt.go.kr
   📞 02-3480-1715
2. "경매 정보 조회 API 제공 여부" 질문
3. 대안 API 문의 (등기정보 등)
```

### Q5: 월 1,000건으로 부족해요
```
A:
1. 사용량 증가 신청
2. 고객센터 문의하여 한도 증설 요청
3. 또는 유료 서비스 전환 고려
```

---

## 📞 고객센터 연락처

### 대한민국 법원 등기정보광장
- 전화: 1577-1691
- 운영시간: 평일 9:00-18:00
- 이메일: (사이트에서 확인)

### 사법정보공유포털
- 이메일: publicapi@scourt.go.kr
- 전화: 02-3480-1715
- 운영시간: 평일 9:00-18:00

---

## 📚 참고 자료

- API 가이드: API_GUIDE.md
- 프로젝트 요약: PROJECT_SUMMARY.md
- 메인 문서: README.md

---

**작성자:** Claude Code
**버전:** 1.0
**최종 수정:** 2026-02-03
