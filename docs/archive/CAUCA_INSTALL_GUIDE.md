# CAUCA 오픈소스 설치 가이드 (Windows)

작성일: 2026-02-03
프로젝트: 법원 경매 정보 REST API 서비스
GitHub: https://github.com/guriguri/cauca

---

## 📋 목차

1. [CAUCA 소개](#cauca-소개)
2. [시스템 요구사항](#시스템-요구사항)
3. [사전 준비](#사전-준비)
4. [단계별 설치](#단계별-설치)
5. [실행 및 테스트](#실행-및-테스트)
6. [API 사용법](#api-사용법)
7. [main.py 연동](#mainpy-연동)
8. [문제 해결](#문제-해결)

---

## 🔍 CAUCA 소개

### 프로젝트 개요
```
이름: CAUCA (Court AUCtion Api service)
언어: Clojure
목적: 법원 경매 사이트 크롤링 + REST API 제공
라이선스: Apache-2.0
```

### 주요 기능
- ✅ 법원 경매 사이트 자동 크롤링 (24시간 주기)
- ✅ MySQL 데이터베이스에 경매 정보 저장
- ✅ REST API 서버 제공
- ✅ 경매 물건 조회 API

### 구성 요소
```
1. Crawler (크롤러)
   - 법원 경매 사이트 주기적 크롤링
   - 데이터베이스에 저장

2. REST API Server
   - 저장된 데이터를 API로 제공
   - HTTP 엔드포인트 제공
```

---

## 💻 시스템 요구사항

### 필수 환경
```
✅ JDK 6 이상 (권장: JDK 8 또는 11)
✅ MySQL 5.x 이상 (또는 MariaDB)
✅ Leiningen (Clojure 빌드 도구)
✅ Git (GitHub 클론용)
```

### 예상 디스크 공간
```
- JDK: 약 300MB
- MySQL: 약 400MB
- CAUCA 프로젝트: 약 50MB
- 데이터베이스 (경매 데이터): 100MB~1GB
합계: 약 1~2GB
```

### 예상 소요 시간
```
- 환경 설치: 1-2시간
- CAUCA 설치: 30분
- 테스트 및 설정: 30분-1시간
합계: 2-4시간
```

---

## 🚀 단계별 설치

## Step 1: JDK 설치

### 1-1. JDK 다운로드

#### 옵션 A: OpenJDK (무료, 권장)
```
1. 브라우저에서 접속:
   https://adoptium.net/

2. "Temurin 11 (LTS)" 선택
   - Operating System: Windows
   - Architecture: x64
   - Package Type: JDK
   - Version: 11 (LTS)

3. "Download" 버튼 클릭
   파일명: OpenJDK11U-jdk_x64_windows_hotspot_11.x.x.msi
```

#### 옵션 B: Oracle JDK
```
1. https://www.oracle.com/java/technologies/downloads/
2. Java 11 또는 Java 8 선택
3. Windows x64 Installer 다운로드
```

### 1-2. JDK 설치

```
1. 다운로드한 .msi 파일 실행
2. 설치 마법사 진행
   - 설치 경로: C:\Program Files\Eclipse Adoptium\jdk-11... (기본값)
   - "Add to PATH" 옵션 체크 ✓
3. "Install" 클릭
4. 완료
```

### 1-3. 설치 확인

```bash
# 명령 프롬프트 또는 Git Bash에서
java -version
```

**예상 출력:**
```
openjdk version "11.0.xx" 2024-xx-xx
OpenJDK Runtime Environment Temurin-11.0.xx+xx (build 11.0.xx+xx)
OpenJDK 64-Bit Server VM Temurin-11.0.xx+xx (build 11.0.xx+xx, mixed mode)
```

### 1-4. 환경변수 설정 (자동 설정 안 된 경우)

```
1. Windows 검색 → "환경 변수" 입력
2. "시스템 환경 변수 편집" 클릭
3. "환경 변수" 버튼 클릭
4. 시스템 변수에서 "새로 만들기"
   - 변수 이름: JAVA_HOME
   - 변수 값: C:\Program Files\Eclipse Adoptium\jdk-11.0.xx
5. Path 변수 편집
   - 새로 만들기: %JAVA_HOME%\bin
6. 확인 클릭
7. 명령 프롬프트 재시작
```

---

## Step 2: MySQL 설치

### 2-1. MySQL 다운로드

```
1. 브라우저에서 접속:
   https://dev.mysql.com/downloads/installer/

2. "MySQL Installer for Windows" 선택
   - mysql-installer-community-8.x.x.msi (약 400MB)

3. "Download" 클릭
   (로그인 없이 "No thanks, just start my download" 클릭)
```

### 2-2. MySQL 설치

```
1. 다운로드한 파일 실행
2. Setup Type 선택
   → "Developer Default" 또는 "Server only" 선택
3. "Next" 클릭
4. "Execute" 클릭하여 필요한 컴포넌트 설치
5. MySQL Server Configuration
   - Type and Networking
     * Config Type: Development Computer
     * Port: 3306 (기본값)
     * ✓ Open Windows Firewall ports

   - Authentication Method
     * ✓ Use Strong Password Encryption (권장)

   - Accounts and Roles
     * Root Password: 강력한 비밀번호 설정 (메모!)
     * 예: CaucaRoot123!@#

   - Windows Service
     * ✓ Configure MySQL Server as a Windows Service
     * Service Name: MySQL80 (기본값)
     * ✓ Start the MySQL Server at System Startup

6. "Execute" 클릭
7. "Finish" 클릭
```

### 2-3. MySQL 설치 확인

```bash
# 명령 프롬프트에서
mysql --version
```

**예상 출력:**
```
mysql  Ver 8.x.x for Win64 on x86_64 (MySQL Community Server - GPL)
```

### 2-4. MySQL 접속 테스트

```bash
# MySQL 접속
mysql -u root -p
```

**비밀번호 입력 후:**
```sql
-- MySQL 프롬프트에서
SHOW DATABASES;

-- 종료
EXIT;
```

---

## Step 3: Leiningen 설치

### 3-1. Leiningen이란?

```
Clojure 프로젝트의 빌드 도구
(Java의 Maven, Python의 pip와 유사)
```

### 3-2. Leiningen 다운로드 (Windows)

```
1. 브라우저에서 접속:
   https://leiningen.org/

2. Windows용 설치 스크립트 다운로드
   https://raw.githubusercontent.com/technomancy/leiningen/stable/bin/lein.bat

3. 파일 저장 위치 선택
   권장: C:\Program Files\Leiningen\lein.bat
```

### 3-3. Leiningen 설치

#### 방법 A: 수동 설치 (권장)

```
1. C:\Program Files\Leiningen 폴더 생성

2. lein.bat 파일을 이 폴더에 저장

3. 환경변수 Path에 추가
   - Windows 검색 → "환경 변수"
   - Path 편집
   - 새로 만들기: C:\Program Files\Leiningen

4. 명령 프롬프트 재시작

5. Leiningen 자동 설치 실행
   lein

   (첫 실행 시 필요한 파일 자동 다운로드, 약 5분 소요)
```

#### 방법 B: Chocolatey 사용 (고급)

```bash
# Chocolatey가 설치되어 있다면
choco install lein
```

### 3-4. 설치 확인

```bash
lein version
```

**예상 출력:**
```
Leiningen 2.x.x on Java 11.0.xx OpenJDK 64-Bit Server VM
```

---

## Step 4: CAUCA 프로젝트 클론

### 4-1. Git 확인

```bash
# Git 설치 확인
git --version
```

**Git이 없다면:**
```
1. https://git-scm.com/download/win
2. 다운로드 및 설치
3. 기본 옵션으로 진행
```

### 4-2. CAUCA 클론

```bash
# auction_gemini 프로젝트 폴더로 이동
cd C:\Users\unity\auction_gemini

# CAUCA 클론
git clone https://github.com/guriguri/cauca.git

# 클론된 폴더로 이동
cd cauca
```

### 4-3. 프로젝트 구조 확인

```bash
# 파일 목록 확인
ls
```

**예상 구조:**
```
cauca/
├── src/
│   ├── cauca/
│   │   ├── core.clj
│   │   ├── crawler.clj
│   │   └── rest.clj
│   └── resources/
│       └── cauca-context.yaml  ← 설정 파일
├── project.clj
├── README.md
└── ...
```

---

## Step 5: MySQL 데이터베이스 설정

### 5-1. MySQL 접속

```bash
mysql -u root -p
```

### 5-2. CAUCA 데이터베이스 생성

```sql
-- 데이터베이스 생성
CREATE DATABASE cauca CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 데이터베이스 확인
SHOW DATABASES;

-- cauca가 목록에 있는지 확인
```

### 5-3. CAUCA 사용자 생성 및 권한 부여

```sql
-- 사용자 생성
CREATE USER 'cauca_user'@'localhost' IDENTIFIED BY 'cauca_password_123';

-- 권한 부여
GRANT ALL PRIVILEGES ON cauca.* TO 'cauca_user'@'localhost';

-- 권한 적용
FLUSH PRIVILEGES;

-- 사용자 확인
SELECT user, host FROM mysql.user WHERE user = 'cauca_user';

-- MySQL 종료
EXIT;
```

### 5-4. 접속 테스트

```bash
# 새 사용자로 접속
mysql -u cauca_user -p cauca
```

**비밀번호: cauca_password_123**

```sql
-- 접속 확인
SELECT DATABASE();

-- 종료
EXIT;
```

---

## Step 6: CAUCA 설정 파일 수정

### 6-1. 설정 파일 위치

```
cauca/src/resources/cauca-context.yaml
```

### 6-2. 설정 파일 열기

```bash
cd C:\Users\unity\auction_gemini\cauca

# Notepad로 열기
notepad src\resources\cauca-context.yaml
```

### 6-3. 설정 파일 수정

**원본:**
```yaml
db:
  classname: com.mysql.jdbc.Driver
  subprotocol: mysql
  subname: //localhost:3306/cauca
  user: $CAUCA_USER$
  password: $CAUCA_PASSWORD$
```

**수정 후:**
```yaml
db:
  classname: com.mysql.jdbc.Driver
  subprotocol: mysql
  subname: //localhost:3306/cauca
  user: cauca_user
  password: cauca_password_123
```

### 6-4. 저장 및 확인

```
1. Ctrl + S (저장)
2. Notepad 닫기
3. 설정 완료!
```

---

## Step 7: CAUCA 빌드

### 7-1. 의존성 다운로드 및 빌드

```bash
# cauca 디렉토리에서
cd C:\Users\unity\auction_gemini\cauca

# 빌드 실행
lein do clean, uberjar
```

**예상 출력:**
```
Retrieving ... from clojars
...
Compiling cauca.core
Compiling cauca.crawler
Compiling cauca.rest
...
Created C:\Users\unity\auction_gemini\cauca\target\cauca-0.1.0-standalone.jar
```

**소요 시간:** 5-10분 (첫 빌드 시)

### 7-2. 빌드 확인

```bash
# JAR 파일 확인
ls target\
```

**생성된 파일:**
```
cauca-0.1.0-standalone.jar  ← 이 파일 확인
```

---

## Step 8: CAUCA 실행

### 8-1. 크롤러 실행 (백그라운드)

#### 방법 A: Leiningen으로 실행 (Linux/Mac)

```bash
# Linux/Mac에서만 작동
lein daemon start crawler -1 86400
```

#### 방법 B: JAR 파일 직접 실행 (Windows 권장)

```bash
# 크롤러 실행 (별도 터미널 창)
java -jar target\cauca-0.1.0-standalone.jar crawler -1 86400
```

**파라미터 설명:**
```
-1: 무한 반복
86400: 24시간 주기 (초 단위)
```

**예상 출력:**
```
Starting crawler...
Crawling court auction site...
...
```

**주의:** 이 창은 계속 열어둬야 합니다!

### 8-2. REST API 서버 실행

**새 명령 프롬프트 창 열기**

```bash
# cauca 디렉토리로 이동
cd C:\Users\unity\auction_gemini\cauca

# REST API 서버 실행
java -jar target\cauca-0.1.0-standalone.jar rest
```

**예상 출력:**
```
Starting REST API server...
Server running on port 8080
```

### 8-3. 서버 접속 테스트

**브라우저에서:**
```
http://localhost:8080
```

**응답 확인:**
```
CAUCA REST API 서버 실행 중
```

---

## Step 9: API 테스트

### 9-1. API 엔드포인트

```
1. 전체 경매 목록 조회
   GET http://localhost:8080/api/courtauction

2. 특정 경매 물건 조회
   GET http://localhost:8080/api/courtauction/:id
```

### 9-2. 브라우저에서 테스트

```
http://localhost:8080/api/courtauction
```

**예상 응답 (JSON):**
```json
[
  {
    "id": 1,
    "item_no": "20240000001",
    "case_no": "2024타경12345",
    "location": "서울특별시 강남구",
    "appraisal_price": 300000000,
    ...
  },
  {
    "id": 2,
    ...
  }
]
```

### 9-3. curl로 테스트

```bash
# 전체 목록 조회
curl http://localhost:8080/api/courtauction

# 특정 ID 조회
curl http://localhost:8080/api/courtauction/1
```

### 9-4. Postman으로 테스트

```
1. Postman 설치 (https://www.postman.com/downloads/)
2. New Request 생성
3. GET http://localhost:8080/api/courtauction
4. Send 클릭
5. 응답 확인
```

---

## Step 10: main.py에 CAUCA API 연동

### 10-1. cauca_api.py 파일 생성

```bash
cd C:\Users\unity\auction_gemini
```

```python
# cauca_api.py
import requests
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class CaucaAPI:
    """CAUCA REST API 클라이언트"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url

    def get_all_auctions(self) -> List[Dict[str, Any]]:
        """
        전체 경매 목록 조회

        Returns:
            경매 물건 리스트
        """
        try:
            url = f"{self.base_url}/api/courtauction"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"CAUCA API 조회 실패: {e}")
            return []

    def get_auction_by_id(self, auction_id: int) -> Dict[str, Any]:
        """
        ID로 경매 물건 조회

        Args:
            auction_id: 경매 물건 ID

        Returns:
            경매 물건 정보
        """
        try:
            url = f"{self.base_url}/api/courtauction/{auction_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"CAUCA API 조회 실패 (ID: {auction_id}): {e}")
            return {}

    def search_by_item_no(self, item_no: str) -> Dict[str, Any]:
        """
        물건번호로 검색

        Args:
            item_no: 물건번호

        Returns:
            경매 물건 정보
        """
        try:
            # 전체 목록 조회
            auctions = self.get_all_auctions()

            # 물건번호로 필터링
            for auction in auctions:
                if auction.get("item_no") == item_no:
                    return auction

            # 찾지 못함
            return {}

        except Exception as e:
            logger.error(f"물건번호 검색 실패 ({item_no}): {e}")
            return {}


# 싱글톤 인스턴스
_cauca_api = None

def get_cauca_api() -> CaucaAPI:
    """CAUCA API 인스턴스 반환"""
    global _cauca_api

    if _cauca_api is None:
        _cauca_api = CaucaAPI()

    return _cauca_api
```

### 10-2. main.py 수정

```python
# main.py 상단에 추가
from cauca_api import get_cauca_api, CaucaAPI

# 전역 변수
cauca_api = None

# 앱 시작 시 초기화
try:
    cauca_api = get_cauca_api()
    logger.info("CAUCA API 초기화 성공")
except Exception as e:
    logger.warning(f"CAUCA API 초기화 실패: {e}")


# get_auction_item 함수 수정
def get_auction_item(item_no: str) -> Dict[str, Any]:
    """
    경매 물건 정보 조회 (CAUCA API 우선)
    """
    # 1. CAUCA API 시도
    if cauca_api:
        try:
            logger.info(f"CAUCA API로 조회: {item_no}")
            result = cauca_api.search_by_item_no(item_no)

            if result:
                # 데이터 정규화
                return {
                    "물건번호": result.get("item_no"),
                    "사건번호": result.get("case_no"),
                    "위치": result.get("location"),
                    "감정가": f"{result.get('appraisal_price', 0):,}원",
                    "감정가_숫자": result.get("appraisal_price", 0),
                    "크롤링방식": "CAUCA API"
                }
        except Exception as e:
            logger.warning(f"CAUCA API 조회 실패: {e}")

    # 2. CAUCA 실패 시 샘플 DB 사용
    logger.info(f"샘플 DB로 조회: {item_no}")
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
            return create_dummy_data(item_no)

    except Exception as e:
        logger.error(f"샘플 DB 조회 실패: {e}")
        return create_dummy_data(item_no)
```

### 10-3. 테스트

```bash
# main.py 실행
cd C:\Users\unity\auction_gemini
python main.py
```

**브라우저에서:**
```
http://localhost:8000
```

**물건번호 검색 테스트:**
```
CAUCA에서 크롤링된 실제 물건번호 입력
→ 실시간 데이터 반환!
```

---

## 🔧 문제 해결 (Troubleshooting)

### Q1: Java가 인식되지 않습니다

```bash
# 증상
'java'은(는) 내부 또는 외부 명령, 실행할 수 있는 프로그램...
```

**해결:**
```
1. JAVA_HOME 환경변수 확인
2. Path에 %JAVA_HOME%\bin 추가
3. 명령 프롬프트 재시작
```

### Q2: MySQL 접속 오류

```bash
# 증상
ERROR 1045 (28000): Access denied for user 'cauca_user'@'localhost'
```

**해결:**
```sql
-- MySQL root로 접속
mysql -u root -p

-- 사용자 재생성
DROP USER 'cauca_user'@'localhost';
CREATE USER 'cauca_user'@'localhost' IDENTIFIED BY 'cauca_password_123';
GRANT ALL PRIVILEGES ON cauca.* TO 'cauca_user'@'localhost';
FLUSH PRIVILEGES;
```

### Q3: Leiningen 빌드 실패

```bash
# 증상
Could not find artifact...
```

**해결:**
```bash
# 캐시 삭제
rm -rf ~/.m2/repository

# 재빌드
lein do clean, uberjar
```

### Q4: CAUCA 서버가 시작되지 않습니다

```bash
# 증상
Exception in thread "main"...
```

**해결:**
```
1. MySQL 서버 실행 확인
   - 작업 관리자 → 서비스 → MySQL80

2. 데이터베이스 존재 확인
   mysql -u root -p
   SHOW DATABASES;

3. 설정 파일 확인
   cauca-context.yaml의 DB 정보 재확인

4. 포트 충돌 확인
   netstat -ano | findstr :8080
```

### Q5: 크롤링이 작동하지 않습니다

**증상:**
```
API 조회 시 빈 배열 [] 반환
```

**해결:**
```
1. 크롤러 프로세스 확인
   - 크롤러 터미널 창이 열려있는지 확인

2. 크롤러 로그 확인
   - 에러 메시지 확인

3. 법원 사이트 차단 가능성
   - CAUCA도 Selenium과 마찬가지로 차단될 수 있음
   - 프로젝트 최신 업데이트 확인

4. 데이터베이스 확인
   mysql -u cauca_user -p cauca
   SHOW TABLES;
   SELECT COUNT(*) FROM auction_items;
```

### Q6: Port 8080이 이미 사용 중입니다

```bash
# 증상
Port 8080 is already in use
```

**해결:**
```bash
# 포트 사용 중인 프로세스 찾기
netstat -ano | findstr :8080

# PID 확인 후 종료
taskkill /PID [프로세스ID] /F

# 또는 다른 포트 사용
# cauca 설정 파일에서 포트 변경
```

---

## 📊 완료 체크리스트

### 환경 설치
- [ ] JDK 설치 및 확인 (`java -version`)
- [ ] MySQL 설치 및 확인 (`mysql --version`)
- [ ] Leiningen 설치 및 확인 (`lein version`)
- [ ] Git 설치 확인 (`git --version`)

### CAUCA 설치
- [ ] CAUCA 저장소 클론
- [ ] 프로젝트 구조 확인
- [ ] MySQL 데이터베이스 생성 (`cauca`)
- [ ] MySQL 사용자 생성 (`cauca_user`)
- [ ] 설정 파일 수정 (`cauca-context.yaml`)
- [ ] 프로젝트 빌드 (`lein do clean, uberjar`)
- [ ] JAR 파일 생성 확인

### 실행 및 테스트
- [ ] 크롤러 실행
- [ ] REST API 서버 실행
- [ ] 브라우저에서 접속 테스트 (http://localhost:8080)
- [ ] API 엔드포인트 테스트
- [ ] 데이터 조회 확인

### main.py 연동
- [ ] cauca_api.py 파일 생성
- [ ] main.py 수정
- [ ] FastAPI 서버 재시작
- [ ] 통합 테스트

---

## 🎯 예상 결과

### 성공 시
```
✅ CAUCA 크롤러가 24시간 주기로 법원 경매 사이트 크롤링
✅ MySQL 데이터베이스에 실시간 경매 정보 저장
✅ REST API 서버가 8080 포트에서 실행
✅ FastAPI 서버가 CAUCA API를 통해 실제 경매 데이터 제공
✅ 사용자가 실제 물건번호로 검색 가능
```

### 데이터 흐름
```
법원 경매 사이트
    ↓ (크롤링)
CAUCA Crawler
    ↓ (저장)
MySQL Database
    ↓ (조회)
CAUCA REST API (port 8080)
    ↓ (호출)
main.py FastAPI (port 8000)
    ↓ (응답)
사용자 웹 브라우저
```

---

## ⚠️ 중요 주의사항

### 1. 크롤링 관련
```
⚠️ CAUCA도 법원 사이트 차단 가능성 있음
⚠️ 프로젝트 마지막 업데이트 확인 필요
⚠️ 법원 사이트 구조 변경 시 작동 안 할 수 있음
```

### 2. 서버 운영
```
⚠️ 크롤러와 REST API 서버 항상 실행 상태 유지 필요
⚠️ MySQL 서버 항상 실행 상태 유지 필요
⚠️ 재부팅 시 수동으로 재시작 필요
```

### 3. 데이터베이스
```
⚠️ 경매 데이터가 쌓이면 디스크 공간 사용 증가
⚠️ 주기적인 백업 권장
⚠️ 오래된 데이터 정리 필요
```

---

## 📚 추가 자료

- CAUCA GitHub: https://github.com/guriguri/cauca
- Leiningen 공식 문서: https://leiningen.org/
- Clojure 공식 사이트: https://clojure.org/
- MySQL 문서: https://dev.mysql.com/doc/

---

## 📞 문제 발생 시

1. CAUCA GitHub Issues 확인
   https://github.com/guriguri/cauca/issues

2. 프로젝트 최신 커밋 확인
   - 마지막 업데이트가 오래되었다면 작동 안 할 가능성

3. 대안 고려
   - CODEF 유료 API
   - 샘플 DB 활용

---

**작성자:** Claude Code
**버전:** 1.0
**최종 수정:** 2026-02-03
