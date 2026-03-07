# 경매 AI 시스템 배포 타임라인

**전체 기간**: 10주 (2026년 3월 2일 ~ 5월 9일)
**현재 진행**: Week 3 완료 + Week 4 준비 완료 (80%)
**다음 단계**: NCP 서버 배포 실행

---

## 📊 진행 상황 요약

```
전체 진행도: ████████████████░░░░ 80% (Week 3 완료 + Week 4 준비)

Week 1-2 (3/2-3/3):   ✅ 백엔드 기반 완성 (100%)
Week 3   (3/4-3/10):  ✅ API 최적화 + JWT + FCM (100%)
Week 4   (3/11-3/17): 🔄 NCP 서버 배포 준비 완료 (40%)
Week 5-8 (3/18-4/14): ⏳ Flutter 모바일 앱 개발 (0%)
Week 9   (4/15-4/21): ⏳ 테스트 및 버그 수정 (0%)
Week 10  (4/22-5/9):  ⏳ Google Play Store 출시 (0%)
```

**현재 위치**: Week 4 진행 중
- ✅ Firebase 프로젝트 생성 완료
- ✅ NCloud 계정 및 결제 등록 완료
- 🔄 다음: 서비스 계정 키 다운로드 및 서버 배포

---

## Week 1-2: 백엔드 기반 완성 ✅ (3/2-3/3)

### Day 1-2: 보안 & 에러 처리 ✅
- [x] API 키 환경변수 분리
- [x] CORS 설정 보안
- [x] Rate Limiting 구현 (slowapi)
- [x] 표준화된 에러 처리 (error_handlers.py)
- [x] 에러 로깅 시스템

### Day 3-4: 성능 최적화 ✅
- [x] GZip 응답 압축
- [x] 브라우저 캐싱 헤더
- [x] AI 예측 결과 캐싱 (1시간)
- [x] 데이터베이스 인덱스 최적화

**진행도**: 100% (8/8 완료)
**소요 시간**: 2일
**상태**: ✅ 완료

---

## Week 3: 모바일 API 최적화 ✅ (3/4-3/10)

### Day 5-6 (3/4-3/5): API 모바일 최적화 ✅

#### 완료된 작업
- [x] **JSON 응답 간소화** (2시간)
  - `mobile=true` 파라미터로 간소화된 JSON 반환
  - /predict: 1.5KB → 0.6KB (60% 감소)
  - /accuracy: 핵심 통계만 반환
  - 불필요한 포맷팅 필드 제거

- [x] **페이지네이션 추가** (2시간)
  - /predictions: limit, offset, has_more 추가
  - /search-case: 페이징 지원 (limit=10, offset=0)
  - 무한 스크롤 지원 (has_more 플래그)

**실제 소요**: 4시간
**진행도**: 100%

---

### Day 7-8 (3/6-3/7): JWT 인증 시스템 구현 ✅

#### 완료된 작업
- [x] **JWT 토큰 시스템** (4시간)
  - PyJWT, passlib, pydantic[email] 설치 완료
  - Access Token (1시간 유효, HS256)
  - Refresh Token (30일 유효, Rotating 방식)
  - get_current_user() 의존성 함수 (토큰 검증)

- [x] **회원가입/로그인 API** (3시간)
  - POST /auth/register (이메일 검증 포함)
  - POST /auth/login (access_token + refresh_token 발급)
  - POST /auth/refresh (토큰 갱신)
  - POST /auth/logout (토큰 무효화)
  - 비밀번호 해싱 (bcrypt via passlib)

- [x] **사용자 관리** (2시간)
  - users 테이블 생성 (id, email, password_hash, name, is_active, is_admin)
  - refresh_tokens 테이블 (토큰 관리 및 revoke 지원)
  - GET /auth/me (현재 사용자 정보)
  - 인덱스 최적화 (email, is_active, token_hash)

**실제 소요**: 6시간
**진행도**: 100%

---

### Day 9-10 (3/8-3/9): FCM 푸시 알림 시스템 ✅

#### 완료된 작업
- [x] **Firebase Admin SDK 통합** (3시간)
  - firebase-admin 패키지 설치
  - notifications.py 모듈 생성
  - Firebase 초기화 로직 구현
  - FCM 메시지 전송 함수

- [x] **푸시 알림 API** (3시간)
  - POST /notifications/register-token (FCM 토큰 저장)
  - POST /notifications/subscribe (경매 알림 구독)
  - GET /notifications/subscriptions (내 구독 목록)
  - DELETE /notifications/unsubscribe/{id} (구독 해제)
  - POST /notifications/test (테스트 알림 전송)

- [x] **데이터베이스 테이블** (1시간)
  - fcm_tokens 테이블 (디바이스 토큰 관리)
  - auction_subscriptions 테이블 (경매 구독)
  - notification_logs 테이블 (알림 전송 기록)

- [x] **알림 스케줄러** (3시간)
  - APScheduler 통합 (main.py)
  - 매일 오전 9시: 내일 경매 리마인더
  - 매일 오후 2시: 가격 하락 알림
  - FastAPI 생명주기 이벤트 연동

- [x] **문서화** (1시간)
  - FIREBASE_SETUP.md 작성 (207줄)
  - Firebase 프로젝트 생성 가이드
  - 서비스 계정 키 설정 방법
  - 테스트 및 문제 해결 가이드

**실제 소요**: 11시간
**진행도**: 100%

---

## Week 4: NCP 서버 배포 🔄 (3/11-3/17)

### 준비 완료 체크리스트 ✅

- [x] **Firebase 프로젝트 생성** (30분) ✅
  - Firebase Console에서 프로젝트 생성 완료
  - FCM 활성화 완료
  - Android 앱 등록 완료

- [x] **NCloud 계정 준비** (10분) ✅
  - https://www.ncloud.com 가입 완료
  - 결제 수단 등록 완료
  - 무료 크레딧 확인 완료

- [x] **배포 가이드 문서** ✅
  - NCP_DEPLOYMENT_GUIDE.md 작성 완료
  - DEPLOYMENT_READINESS.md 작성 완료
  - README.md 업데이트 완료

**진행도**: 40% (준비 단계 완료)

---

### Day 11-12 (3/11-3/12): NCP 서버 배포 실행 🔄

#### 즉시 실행 가능한 작업

**1단계: Firebase 서비스 계정 키 다운로드 및 배치** (10분)

```bash
# Firebase Console 접속
1. https://console.firebase.google.com/ 접속
2. 생성한 프로젝트 선택
3. 프로젝트 설정 (⚙️ 아이콘) > 서비스 계정 탭
4. "새 비공개 키 생성" 버튼 클릭
5. JSON 파일 다운로드

# 파일 배치
1. 다운로드한 파일 이름을 firebase-service-account.json으로 변경
2. C:\Users\unity\auction_gemini\ 경로에 복사
3. .gitignore에 해당 파일이 포함되어 있는지 확인
```

**2단계: 로컬에서 Firebase 연동 테스트** (10분)

```bash
# 서버 재시작
cd C:\Users\unity\auction_gemini
python -m uvicorn main:app --reload

# 로그 확인 (다음 메시지가 보이면 성공)
INFO: Firebase Admin SDK 초기화 완료
📅 알림 스케줄러 시작 완료
  - 경매 알림: 매일 오전 9시
  - 가격 하락 체크: 매일 오후 2시
```

**3단계: NCP 서버 인스턴스 생성** (1시간)

```bash
# NCP Console 접속
1. https://console.ncloud.com/ 로그인
2. Compute > Server 메뉴 선택
3. 서버 생성 버튼 클릭

# 서버 설정
- Zone: KR-1 (한국)
- Server 타입: Standard
- CPU/Memory: 2 vCPU, 4GB RAM (월 45,000원)
- OS: Ubuntu Server 22.04 LTS
- 스토리지: 50GB SSD
- 인증키: 새로운 인증키 생성 (다운로드 후 안전하게 보관)
- ACG(방화벽): 기본 ACG 사용
- 공인 IP: 할당

# 서버 생성 완료 후
- 공인 IP 주소 기록 (예: 123.456.78.90)
- 인증키 파일 저장 (예: auction-ai-key.pem)
```

**4단계: SSH 접속 및 초기 설정** (30분)

```bash
# Windows에서 SSH 접속 (Git Bash 또는 PowerShell)
chmod 600 auction-ai-key.pem
ssh -i auction-ai-key.pem root@[공인IP주소]

# 접속 후 패키지 업데이트
sudo apt update
sudo apt upgrade -y

# Python 3.10 설치
sudo apt install -y python3.10 python3.10-venv python3-pip

# Nginx 설치
sudo apt install -y nginx

# Git 설치
sudo apt install -y git
```

**5단계: 프로젝트 배포** (1시간)

```bash
# 작업 디렉토리 생성
cd /home
sudo mkdir -p auction_gemini
cd auction_gemini

# Git 저장소 클론 (저장소가 있는 경우)
# git clone [your-repo-url] .

# 또는 파일 직접 업로드 (SCP 사용)
# 로컬 PC에서 실행 (Git Bash):
# scp -i auction-ai-key.pem -r C:\Users\unity\auction_gemini\* root@[공인IP]:/home/auction_gemini/

# 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# Firebase 서비스 계정 키 업로드
# 로컬 PC에서:
# scp -i auction-ai-key.pem C:\Users\unity\auction_gemini\firebase-service-account.json root@[공인IP]:/home/auction_gemini/

# 환경변수 설정 (필요 시)
nano .env
# 내용 추가 후 Ctrl+X, Y, Enter로 저장
```

**6단계: Gunicorn 설정** (30분)

```bash
# Gunicorn 설치
pip install gunicorn

# Gunicorn 설정 파일 생성
nano gunicorn_config.py

# 아래 내용 복사 후 붙여넣기:
```

```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120

accesslog = "/home/auction_gemini/logs/gunicorn_access.log"
errorlog = "/home/auction_gemini/logs/gunicorn_error.log"
loglevel = "info"

proc_name = "auction_ai_api"
```

```bash
# 로그 디렉토리 생성
mkdir -p logs

# Gunicorn 테스트 실행
gunicorn main:app -c gunicorn_config.py

# 다른 터미널에서 테스트
curl http://localhost:8000/

# 성공하면 Ctrl+C로 중단
```

**7단계: systemd 서비스 등록** (30분)

```bash
# systemd 서비스 파일 생성
sudo nano /etc/systemd/system/auction-ai.service

# 아래 내용 복사 후 붙여넣기:
```

```ini
[Unit]
Description=Auction AI FastAPI Application
After=network.target

[Service]
Type=notify
User=root
Group=root
WorkingDirectory=/home/auction_gemini
Environment="PATH=/home/auction_gemini/venv/bin"
ExecStart=/home/auction_gemini/venv/bin/gunicorn main:app -c /home/auction_gemini/gunicorn_config.py
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 등록 및 시작
sudo systemctl daemon-reload
sudo systemctl enable auction-ai
sudo systemctl start auction-ai

# 서비스 상태 확인
sudo systemctl status auction-ai

# 로그 확인
sudo journalctl -u auction-ai -f
```

**8단계: Nginx 리버스 프록시 설정** (30분)

```bash
# Nginx 설정 파일 생성
sudo nano /etc/nginx/sites-available/auction-ai

# 아래 내용 복사 후 붙여넣기:
```

```nginx
upstream auction_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name [공인IP주소 또는 도메인];

    client_max_body_size 10M;

    access_log /var/log/nginx/auction_api_access.log;
    error_log /var/log/nginx/auction_api_error.log;

    location / {
        proxy_pass http://auction_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /docs {
        proxy_pass http://auction_api/docs;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://auction_api/openapi.json;
        proxy_set_header Host $host;
    }
}
```

```bash
# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/auction-ai /etc/nginx/sites-enabled/

# Nginx 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx

# 브라우저에서 테스트
# http://[공인IP주소]/
# http://[공인IP주소]/docs
```

**9단계: 방화벽 설정** (10분)

```bash
# UFW 방화벽 활성화
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS (나중에 사용)
sudo ufw enable

# 방화벽 상태 확인
sudo ufw status
```

**10단계: 도메인 연결 및 HTTPS (선택사항)** (1시간)

```bash
# 도메인이 있는 경우:

# 1. DNS A 레코드 추가
#    도메인 제공업체 관리 페이지에서:
#    타입: A
#    이름: api (또는 @)
#    값: [NCP 공인 IP 주소]
#    TTL: 3600

# 2. Let's Encrypt SSL 인증서 설치
sudo apt install -y certbot python3-certbot-nginx

# 3. 인증서 발급
sudo certbot --nginx -d api.yourdomain.com

# 4. 자동 갱신 설정
sudo systemctl enable certbot.timer
```

**예상 총 소요 시간**: 4-6시간

---

### Day 13-17 (3/13-3/17): 배포 최적화 및 모니터링 설정

#### 추가 작업
- [ ] **데이터베이스 백업 스크립트** (1시간)
  - 자동 백업 cron job 설정
  - NCP Object Storage 연동 (선택)

- [ ] **로그 관리** (1시간)
  - 로그 로테이션 설정
  - 오래된 로그 자동 삭제

- [ ] **성능 모니터링** (2시간)
  - 서버 리소스 모니터링
  - API 응답 시간 추적

---

### Week 4 체크리스트

```
준비 단계: ✅
☑ Firebase 프로젝트 생성
☑ NCloud 계정 및 결제 등록
☑ 배포 가이드 문서 작성

Day 11-12 (3/11-3/12): 🔄
□ Firebase 서비스 계정 키 다운로드 및 배치
□ NCP 서버 인스턴스 생성
□ SSH 접속 및 초기 설정
□ 프로젝트 배포
□ Gunicorn + systemd 서비스 등록
□ Nginx 리버스 프록시 설정
□ http://[공인IP]/docs 접속 가능

Day 13-17 (3/13-3/17): ⏳
□ 데이터베이스 백업 설정
□ 로그 관리 설정
□ 성능 모니터링 구축

완료 기준:
□ API 서버 정상 작동 (Uptime 99%)
□ Swagger UI 접속 가능
□ FCM 테스트 알림 전송 성공
□ 스케줄러 정상 작동 (로그 확인)
```

---

## Week 5-8: Flutter 모바일 앱 개발 ⏳ (3/18-4/14)

### Week 5 (3/18-3/24): Flutter 환경 설정 및 기본 화면

#### 개발 환경 구축
- [ ] **Flutter SDK 설치** (1시간)
  - https://flutter.dev 에서 다운로드
  - Android Studio 설치
  - Flutter Doctor 실행

- [ ] **프로젝트 생성** (2시간)
  - flutter create auction_ai_app
  - 기본 프로젝트 구조 설정
  - 패키지명 설정: com.auctionai.app

- [ ] **Firebase Flutter SDK 통합** (2시간)
  - firebase_core, firebase_messaging 패키지 추가
  - google-services.json 배치 (android/app/)
  - Firebase 초기화 코드 작성

#### 기본 화면 구현
- [ ] **홈 화면** (4시간)
  - 앱바, 내비게이션
  - 검색 바
  - 추천 경매 목록

- [ ] **검색 화면** (3시간)
  - 검색 입력 필드
  - 필터 옵션
  - 검색 결과 리스트

**예상 소요**: 12시간 (3일)

---

### Week 6 (3/25-3/31): API 연동 및 인증 구현

#### API 클라이언트 개발
- [ ] **Dio HTTP 클라이언트** (3시간)
  - Dio 패키지 설정
  - BaseUrl 설정 (http://[NCP공인IP]:80)
  - Request/Response Interceptor

- [ ] **JWT 토큰 관리** (4시간)
  - SharedPreferences로 토큰 저장
  - 자동 토큰 갱신 (Refresh Token)
  - 인증 상태 관리 (Provider/Riverpod)

#### 인증 화면
- [ ] **로그인 화면** (3시간)
  - 이메일/비밀번호 입력
  - 로그인 버튼
  - 에러 처리

- [ ] **회원가입 화면** (3시간)
  - 입력 필드 (이메일, 비밀번호, 이름)
  - 유효성 검증
  - 회원가입 API 호출

- [ ] **마이페이지** (2시간)
  - 내 정보 표시
  - 로그아웃 버튼

**예상 소요**: 15시간 (4일)

---

### Week 7 (4/1-4/7): 주요 기능 개발

#### 경매 검색 및 상세
- [ ] **경매 검색 API 연동** (3시간)
  - /search 엔드포인트 호출
  - 페이지네이션 처리
  - 무한 스크롤 구현

- [ ] **경매 상세 화면** (4시간)
  - 경매 정보 표시
  - 이미지 캐러셀
  - AI 예측 결과 표시

- [ ] **북마크 기능** (3시간)
  - 관심 경매 저장
  - 로컬 DB (sqflite)
  - 북마크 목록 화면

#### 통계 화면
- [ ] **통계 대시보드** (4시간)
  - 지역별 통계
  - 가격대별 통계
  - 차트 표시 (fl_chart)

**예상 소요**: 14시간 (3.5일)

---

### Week 8 (4/8-4/14): 푸시 알림 및 테스트

#### 푸시 알림 구현
- [ ] **FCM 토큰 관리** (3시간)
  - 앱 시작 시 FCM 토큰 가져오기
  - 서버에 토큰 등록 (POST /notifications/register-token)
  - 토큰 갱신 처리

- [ ] **알림 수신 처리** (4시간)
  - Foreground 알림
  - Background 알림
  - 알림 클릭 시 화면 이동

- [ ] **알림 구독 관리** (3시간)
  - 경매 알림 구독 설정
  - 구독 목록 표시
  - 구독 해제 기능

#### 통합 테스트
- [ ] **기능 테스트** (4시간)
  - 모든 화면 동작 확인
  - API 연동 테스트
  - 에러 처리 확인

- [ ] **성능 최적화** (3시간)
  - 이미지 캐싱
  - API 응답 캐싱
  - 빌드 최적화

**예상 소요**: 17시간 (4일)

---

## Week 9: 테스트 및 버그 수정 ⏳ (4/15-4/21)

### 베타 테스트
- [ ] **베타 테스터 모집** (1일)
  - 지인 10-20명 초대
  - 테스트 APK 배포
  - 피드백 폼 제공

- [ ] **버그 수정** (3일)
  - Critical 버그 우선 처리
  - 사용성 개선
  - UI 버그 수정

- [ ] **최종 점검** (1일)
  - 모든 기능 재테스트
  - API 연동 확인
  - 성능 측정

**예상 소요**: 5일

---

## Week 10: Google Play Store 출시 ⏳ (4/22-5/9)

### Day 64-66 (4/22-4/24): 스토어 등록 준비

#### 앱 메타데이터
- [ ] **앱 정보 작성** (3시간)
  - 앱 이름: "경매AI - AI 낙찰가 예측"
  - 짧은 설명 (80자)
  - 상세 설명 (4000자)
  - 키워드: 경매, 낙찰가, 부동산, AI, 투자

- [ ] **스크린샷 준비** (4시간)
  - 5-8개 화면 캡처
  - 1080x1920px (Android 표준)
  - 주요 기능 표시

- [ ] **앱 아이콘** (2시간)
  - 512x512px PNG
  - Adaptive 아이콘 (Android)

---

### Day 67-68 (4/25-4/26): APK 빌드 및 제출

#### Release 빌드
- [ ] **APK/AAB 생성** (2시간)
  - flutter build apk --release
  - flutter build appbundle --release
  - 코드 서명

- [ ] **Google Play Console** (3시간)
  - 개발자 계정 생성 ($25)
  - 앱 등록
  - AAB 업로드
  - 메타데이터 입력
  - 심사 제출

**예상 소요**: 5시간

---

### Day 69+ (4/27-5/9): 심사 및 런칭

#### 앱 심사
- [ ] **Google Play 심사** (1-3일)
  - 자동 심사
  - 수동 심사 (해당 시)

- [ ] **거절 시 대응**
  - 피드백 분석
  - 즉시 수정
  - 재제출

#### 정식 런칭 🚀
- [ ] **오픈일**: 5월 1-9일 (심사 기간에 따라 유동적)
- [ ] **마케팅**: SNS 홍보, 커뮤니티 공유

---

## 예상 비용 총정리

### 개발 비용 (1회)
- Google Play 개발자 계정: $25 (약 33,000원)
- 앱 아이콘 디자인: 0원 (직접 제작) ~ 100,000원
- **합계: 33,000원 ~ 133,000원**

### 운영 비용 (월)
- NCP 서버: 45,000원 (Standard 2 vCPU, 4GB RAM)
- 도메인: 1,250원 (15,000원/년 ÷ 12개월)
- Firebase: 무료 (FCM, Authentication)
- **합계: 46,250원/월**

### 6개월 후 예상 수익
- 다운로드: 5,000명
- 활성 사용자: 1,000명
- 프리미엄 (5%): 50명 × $9.99
- **월 수익: 약 500,000원**
- **ROI 달성: 2-3개월**

---

## 🎯 즉시 실행 가능한 다음 단계

### 오늘 할 일 (30분)

1. **Firebase 서비스 계정 키 다운로드** (10분)
   ```
   Firebase Console > 프로젝트 설정 > 서비스 계정
   > "새 비공개 키 생성" 클릭
   > firebase-service-account.json으로 저장
   > C:\Users\unity\auction_gemini\ 에 복사
   ```

2. **로컬 테스트** (10분)
   ```bash
   cd C:\Users\unity\auction_gemini
   python -m uvicorn main:app --reload

   # 로그에서 확인:
   INFO: Firebase Admin SDK 초기화 완료
   📅 알림 스케줄러 시작 완료
   ```

3. **NCP 서버 인스턴스 생성** (10분)
   ```
   NCP Console > Compute > Server
   > 서버 생성
   > Standard 2 vCPU, 4GB RAM
   > Ubuntu 22.04 LTS
   > 공인 IP 할당
   ```

### 이번 주말 할 일 (4-6시간)

1. SSH 접속 및 초기 설정
2. 프로젝트 배포
3. Gunicorn + systemd 서비스 등록
4. Nginx 리버스 프록시 설정
5. 방화벽 설정
6. 브라우저에서 http://[공인IP]/docs 접속 확인

---

**문서 버전**: 3.0 (Flutter 네이티브 앱 전략)
**최종 업데이트**: 2026-03-05
**현재 상태**: Week 3 완료 + Week 4 준비 완료 (80%)
**다음 마일스톤**: NCP 서버 배포 완료 (Week 4, Day 11-12)

---

**🎯 목표: 5월 9일까지 Google Play Store 런칭**
