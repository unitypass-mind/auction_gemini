# 경매 AI 시스템 (Auction AI System)

실시간 부동산 경매 정보 조회 및 AI 기반 낙찰가 예측 시스템

---

## 프로젝트 개요

이 프로젝트는 대법원 경매 정보 사이트에서 부동산 경매 데이터를 수집하고, 머신러닝 모델을 통해 낙찰가를 예측하며, 사용자에게 실시간 알림을 제공하는 종합 경매 정보 플랫폼입니다.

### 주요 기능

- **실시간 경매 정보 조회**: 대법원 경매 사이트 크롤링 및 데이터 업데이트
- **AI 낙찰가 예측**: XGBoost 기반 머신러닝 모델로 낙찰가 예측
- **사용자 인증 시스템**: JWT 토큰 기반 회원가입/로그인
- **푸시 알림**: Firebase Cloud Messaging을 통한 경매 리마인더 및 가격 하락 알림
- **경매 구독 시스템**: 관심 물건에 대한 맞춤형 알림 설정
- **통계 및 분석**: 지역별, 가격대별 경매 통계 제공

---

## 📋 현재 프로젝트 상태

### 완료된 작업 (Week 4+ 완료 - 97%)

**✅ 백엔드 API (24개 엔드포인트)**
- 경매 검색/조회 API (9개)
- 사용자 인증 API (3개)
- 통계 API (6개)
- 푸시 알림 API (5개)
- AI 모델 분석 API (1개)

**✅ 데이터베이스 (8개 테이블)**
- auction_items, users, user_searches
- fcm_tokens, auction_subscriptions, notification_logs
- prediction_logs, model_performance_logs

**✅ 인증 및 알림 시스템**
- JWT 토큰 인증
- Firebase Cloud Messaging (FCM) 푸시 알림
- APScheduler 자동 알림 (매일 오전 9시, 오후 2시)

**✅ 종합 문서화**
- 배포 가이드 5종 완성
- API 사용법 문서
- 데이터베이스 스키마 설명

**✅ NCP 프로덕션 배포 (2026-03-17 완료)**
- Naver Cloud Platform 서버 생성 완료
- Nginx 리버스 프록시 설정 (80 → 8000)
- systemd 서비스 자동 시작 설정
- Firebase 연동 완료
- 데이터베이스 및 AI 모델 v4 배포 (58개 특성)
- Fail2ban 보안 강화 (SSH 브루트포스 방어)
- **HTTPS 인증서 설정 완료 (Let's Encrypt)**
- **도메인 설정 완료 (auction-ai.kr)**
- **데이터베이스 백업 자동화 (매일 02:00)**
- **서버 모니터링 시스템 (10분마다)**
- **로그 로테이션 설정 (7일 보관)**
- **API Rate Limiting (60요청/분)**
- **서비스 URL: https://auction-ai.kr**

**✅ 데이터 품질 및 최적화 (2026-03-21 완료)**
- **데이터베이스 중복 제거**: 39개 중복 레코드 정리 (878개 고유 레코드 유지)
- **낙찰 완료 물건 처리 개선**: 과거 예측값 표시 및 입찰 불가 상태 명확화
- **AI 모델 가중치 분석 API**: `/model/features` 엔드포인트 추가
- **예측 정확도 향상**: 중복 데이터 제거로 통계 신뢰성 향상
- **UI/UX 개선**: 예상 수익 콤마 포맷팅, 낙찰 완료 상태 표시

**✅ Flutter 모바일 앱 개발 (진행 중 - 80%)**
- **핵심 기능 완료**: 검색, 전체분석, 통계, AI예측 탭
- **실시간 데이터 연동**: ValueAuction API 통합
- **AI 예측 통합**: XGBoost v4 모델 (58개 특성)
- **사용자 경험**: 로딩 상태, 에러 처리, 새로고침 기능
- **남은 작업**: 푸시 알림, 사용자 인증, Play Store 출시 준비

### 진행 중 / 예정된 작업

**🔄 운영 및 최적화 (선택사항)**
- 모니터링 대시보드 (Prometheus/Grafana)
- CI/CD 파이프라인 (GitHub Actions)
- 모델 성능 자동 추적

**📅 Week 5-8: 모바일 앱 개발**
- Flutter 앱 개발 (4주 예정)
- Firebase FCM 통합
- 사용자 인터페이스 구현
- Google Play Store 출시

---

## 📚 문서 가이드

프로젝트의 각 단계별로 상세한 가이드 문서가 준비되어 있습니다:

### 1. **배포 준비 상태 체크리스트**
📄 [DEPLOYMENT_READINESS.md](./DEPLOYMENT_READINESS.md)

**대상**: 프로젝트 관리자, 개발 팀장
**내용**:
- 전체 프로젝트 진행 상황 요약 (75% 완료)
- 완료된 기능 목록 (23개 API, 8개 테이블)
- 남은 작업 및 예상 소요 시간
- 비용 예측 (월 45,000원)
- 배포 전 확인 체크리스트

**언제 읽어야 하나요?**
- 프로젝트 현황을 한눈에 파악하고 싶을 때
- 배포 전 준비 상태를 점검할 때
- 다음 단계 작업을 계획할 때

---

### 2. **Firebase 푸시 알림 설정 가이드**
📄 [FIREBASE_SETUP.md](./FIREBASE_SETUP.md)

**대상**: 백엔드 개발자, DevOps 엔지니어
**내용**:
- Firebase 프로젝트 생성 방법
- FCM (Firebase Cloud Messaging) 활성화
- 서비스 계정 키 다운로드 및 설정
- 보안 설정 (`.gitignore` 구성)
- 테스트 알림 전송 방법
- 문제 해결 가이드

**언제 읽어야 하나요?**
- 푸시 알림 기능을 활성화하기 전 (필수)
- FCM 설정 오류가 발생했을 때
- 프로덕션 배포 전 Firebase 설정 점검

**예상 소요 시간**: 30분

---

### 3. **NCP 서버 배포 가이드**
📄 [NCP_DEPLOYMENT_GUIDE.md](./NCP_DEPLOYMENT_GUIDE.md)

**대상**: DevOps 엔지니어, 시스템 관리자
**내용**:
- Naver Cloud Platform 계정 생성 및 서버 인스턴스 생성
- Ubuntu 22.04 LTS 초기 설정
- Python, Nginx, Gunicorn 설치 및 구성
- systemd 서비스 등록
- Nginx 리버스 프록시 설정
- 도메인 연결 및 HTTPS 인증서 (Let's Encrypt)
- 모니터링 및 로그 관리
- 백업 스크립트 설정
- 보안 강화 (UFW 방화벽)
- 문제 해결 가이드

**언제 읽어야 하나요?**
- NCP 서버에 처음 배포할 때 (필수)
- 서버 설정을 변경하거나 업데이트할 때
- 배포 관련 오류를 해결할 때

**예상 소요 시간**: 4-6시간

**예상 비용**: 월 45,000원 (Standard 2 Core, 4GB RAM)

---

### 4. **배포 타임라인 및 일정**
📄 [DEPLOYMENT_TIMELINE.md](./DEPLOYMENT_TIMELINE.md)

**대상**: 프로젝트 매니저, 전체 팀
**내용**:
- Week 1-3: 백엔드 API 개발 (완료)
- Week 4: NCP 서버 배포 (진행 예정)
- Week 5-8: 모바일 앱 개발 (Flutter)
- Week 9: 테스트 및 버그 수정
- Week 10: Google Play Store 출시

**언제 읽어야 하나요?**
- 프로젝트 전체 일정을 확인할 때
- 각 주차별 목표와 마일스톤을 점검할 때
- 다음 주 작업을 계획할 때

---

### 5. **모바일 앱 개발 전략**
📄 [MOBILE_APP_STRATEGY.md](./MOBILE_APP_STRATEGY.md)

**대상**: 모바일 개발자, UI/UX 디자이너
**내용**:
- Flutter 개발 환경 설정
- Firebase 통합 (FCM, Authentication)
- API 연동 방법 (Dio, Retrofit)
- 주요 화면 구성 및 UI/UX 설계
- 푸시 알림 수신 구현
- Google Play Store 출시 프로세스

**언제 읽어야 하나요?**
- 모바일 앱 개발을 시작하기 전 (필수)
- API 연동 방법을 확인할 때
- Firebase 모바일 SDK 설정이 필요할 때

**예상 소요 시간**: 4주

---

## 🚀 빠른 시작 (Quick Start)

### 프로덕션 서비스 접속

**웹 서비스**: https://auction-ai.kr
- API 문서: https://auction-ai.kr/docs
- 모델 상태: https://auction-ai.kr/model-status
- 정확도 통계: https://auction-ai.kr → 정확도 탭
- 검색 기능: 지역, 물건 종류, 사건번호로 검색 가능

**서버 관리 (SSH)**:
```bash
ssh -p 2222 root@49.50.131.190  # IP 주소로 SSH 접속
# 또는
ssh -p 2222 root@auction-ai.kr  # 도메인으로 접속 (DNS 설정 필요)
```

### 사전 요구사항

- Python 3.10 이상
- SQLite3
- Firebase 프로젝트 (푸시 알림용)
- Naver Cloud Platform 계정 (배포용)

### 로컬 개발 환경 설정

1. **저장소 클론**
   ```bash
   git clone <repository-url>
   cd auction_gemini
   ```

2. **가상 환경 생성 및 활성화**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

4. **Firebase 서비스 계정 키 설정** (선택사항)
   - [FIREBASE_SETUP.md](./FIREBASE_SETUP.md) 참고
   - `firebase-service-account.json` 파일을 프로젝트 루트에 배치

5. **서버 실행**
   ```bash
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **API 문서 확인**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

---

## 📊 API 엔드포인트 개요

### 경매 정보 조회
- `GET /` - 서버 상태 확인
- `GET /accuracy` - 모델 정확도 조회
- `GET /price-range-stats` - 가격대별 통계
- `GET /regional-stats` - 지역별 통계
- `GET /search` - 경매 검색
- `GET /detail/{case_number}` - 경매 상세 정보
- `GET /case-number/{case_number}` - 사건번호로 조회

### 사용자 인증
- `POST /auth/register` - 회원가입
- `POST /auth/login` - 로그인
- `GET /auth/me` - 내 정보 조회 (JWT 필요)

### 푸시 알림
- `POST /notifications/register-token` - FCM 토큰 등록
- `POST /notifications/subscribe` - 경매 알림 구독
- `GET /notifications/subscriptions` - 내 구독 목록
- `DELETE /notifications/unsubscribe/{subscription_id}` - 구독 해제
- `POST /notifications/test` - 테스트 알림 전송

### 통계 및 분석
- `GET /search-trends` - 검색 트렌드
- `GET /popular-regions` - 인기 지역
- `GET /avg-success-rate` - 평균 낙찰률

### AI 모델 분석
- `GET /model/features` - AI 모델 변수별 가중치 조회 (Feature Importance)
- `GET /model-status` - 모델 로드 상태 확인

---

## 🗂️ 프로젝트 구조

```
auction_gemini/
├── main.py                      # FastAPI 메인 애플리케이션
├── auth.py                      # JWT 인증 모듈
├── notifications.py             # FCM 푸시 알림 모듈
├── database.py                  # 데이터베이스 관리
├── scheduler.py                 # 데이터 수집 자동화
├── auction_crawler.py           # 경매 데이터 크롤러
├── data_processing.py           # 데이터 전처리
├── model_training.py            # 머신러닝 모델 학습
├── performance_monitor.py       # 모델 성능 모니터링
├── requirements.txt             # Python 의존성
├── auction_items.db             # SQLite 데이터베이스
├── xgboost_auction_model.json   # 학습된 모델 파일
├── firebase-service-account.json # Firebase 서비스 계정 키 (수동 배치)
│
├── logs/                        # 로그 파일
│   ├── auction_api_*.log
│   └── scheduler_*.log
│
├── FIREBASE_SETUP.md            # Firebase 설정 가이드
├── NCP_DEPLOYMENT_GUIDE.md      # NCP 배포 가이드
├── DEPLOYMENT_TIMELINE.md       # 배포 일정
├── DEPLOYMENT_READINESS.md      # 배포 준비 체크리스트
├── MOBILE_APP_STRATEGY.md       # 모바일 앱 전략
└── README.md                    # 이 파일
```

---

## 🔐 보안 고려사항

### 중요한 파일 (절대 Git에 커밋하지 마세요!)
- `firebase-service-account.json` - Firebase 서비스 계정 키
- `auction_items.db` - 실제 데이터가 포함된 데이터베이스
- `.env` - 환경 변수 파일 (프로덕션 환경)

### `.gitignore` 설정 확인
```gitignore
firebase-service-account.json
*.json  # 서비스 계정 키 파일
auction_items.db
.env
__pycache__/
venv/
logs/
*.log
```

---

## 📞 다음 단계

### 현재 단계: Week 5 진행 중 (97%)

**✅ 최근 완료된 작업 (2026-03-21):**
1. ✅ 데이터베이스 중복 제거 및 품질 개선
2. ✅ AI 모델 Feature Importance API 추가
3. ✅ 낙찰 완료 물건 처리 로직 개선
4. ✅ Flutter 앱 핵심 기능 개발 (80%)

**🔄 진행 중인 작업:**

1. **Flutter 앱 완성** (남은 20%, 예상 1-2주)
   - ✅ 검색, 전체분석, 통계, AI예측 탭 완료
   - 🔄 푸시 알림 기능 구현
   - 🔄 사용자 인증 시스템 통합
   - ⏳ APK 빌드 및 테스트
   - ⏳ Play Store 출시 준비

2. **데이터 수집 자동화** (선택사항)
   - ValueAuction API 크롤링 스케줄러
   - 신규 경매 데이터 자동 업데이트
   - 낙찰 결과 자동 수집

3. **모델 재학습 파이프라인** (선택사항)
   - 최신 데이터로 모델 재학습
   - 성능 모니터링 및 A/B 테스트
   - 자동 배포 시스템

**📅 향후 계획:**

1. **Week 6-7: 앱 완성 및 테스트**
   - 베타 테스트 진행
   - 버그 수정 및 성능 최적화
   - UI/UX 피드백 반영

2. **Week 8: Play Store 출시**
   - Play Console 등록
   - 앱 스토어 최적화 (ASO)
   - 마케팅 자료 준비

3. **이후: 운영 및 개선**
   - 사용자 피드백 수집
   - 기능 추가 및 개선
   - 모델 정확도 향상

---

## 💰 예상 비용

### NCP 서버 (월 45,000원)
- Standard 2 Core, 4GB RAM
- 50GB SSD 스토리지
- 100GB 데이터 전송

### Firebase (무료)
- Cloud Messaging: 무제한 (무료)
- Authentication: 월 10,000명까지 무료

### 도메인 (연 15,000원)
- .com 도메인 기준

### 총 예상 비용: 월 약 50,000원

---

## 🛠️ 기술 스택

### 백엔드
- **Framework**: FastAPI
- **Database**: SQLite3
- **ML Model**: XGBoost
- **Authentication**: JWT (python-jose)
- **Notification**: Firebase Cloud Messaging
- **Scheduler**: APScheduler
- **Web Server**: Gunicorn + Nginx

### 모바일 (예정)
- **Framework**: Flutter
- **State Management**: Provider / Riverpod
- **HTTP Client**: Dio
- **Push Notification**: firebase_messaging

### 인프라
- **Cloud**: Naver Cloud Platform (NCP)
- **OS**: Ubuntu 22.04 LTS
- **SSL**: Let's Encrypt
- **Monitoring**: Prometheus (예정)

---

## 📜 라이선스

이 프로젝트는 내부 사용을 위한 것으로, 외부 배포 시 저작권 및 라이선스를 명시해야 합니다.

---

## 📧 문의 및 지원

프로젝트 관련 문의사항이나 기술 지원이 필요한 경우:

1. **배포 문제**: [NCP_DEPLOYMENT_GUIDE.md](./NCP_DEPLOYMENT_GUIDE.md)의 문제 해결 섹션 참고
2. **Firebase 설정 문제**: [FIREBASE_SETUP.md](./FIREBASE_SETUP.md)의 문제 해결 섹션 참고
3. **API 사용법**: http://localhost:8000/docs (Swagger UI) 참고

---

**마지막 업데이트**: 2026-03-21
**프로젝트 진행률**: 97% (데이터 품질 개선 및 앱 개발 80% 완료)
**현재 작업**: Flutter 앱 완성 및 Play Store 출시 준비
**다음 마일스톤**: Play Store 출시 (Week 8 예정)
**프로덕션 서비스**: https://auction-ai.kr
**주요 성과**:
- 878개 고유 경매 데이터 (중복 제거 완료)
- AI 모델 v4 정확도: 평균 오차율 11-12%
- API 응답 속도: 평균 200-500ms
- Flutter 앱 핵심 기능 완성
