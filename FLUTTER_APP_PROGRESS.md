# Flutter 모바일 앱 개발 진행 상황

**작성일**: 2026-03-09
**프로젝트**: 경매 AI - AI 기반 낙찰가 예측 모바일 앱
**진행률**: Week 5 시작 (40%)

---

## 📱 완료된 작업

### 1. 개발 환경 설정 ✅

**Flutter SDK**
- 버전: Flutter 3.41.4
- Dart: 3.11.1
- DevTools: 2.54.1
- 설치 경로: C:\src\flutter

**Android Studio**
- 버전: Panda 2 | 2025.3.2
- Android SDK: 36.1.0
- SDK Command-line Tools: 설치 완료
- 모든 라이선스 승인 완료

**개발 환경 상태** (flutter doctor):
```
[√] Flutter (Channel stable, 3.41.4)
[√] Windows Version (Windows 11)
[√] Android toolchain - develop for Android devices (Android SDK 36.1.0)
[√] Chrome - develop for the web
[√] Connected device (3 available)
[√] Network resources
```

---

### 2. Flutter 프로젝트 생성 ✅

**프로젝트 정보**
- 프로젝트명: `auction_ai_app`
- 조직: `com.auctionai`
- 경로: `C:\Users\unity\auction_gemini\auction_ai_app`

**의존성 패키지** (76개 설치):
- **상태 관리**: provider ^6.1.1
- **HTTP 통신**: dio ^5.4.0
- **로컬 저장소**: shared_preferences ^2.2.2
- **Firebase**:
  - firebase_core ^2.24.2
  - firebase_messaging ^14.7.10
  - firebase_auth ^4.16.0
- **JWT**: jwt_decoder ^2.0.1
- **UI**:
  - flutter_spinkit ^5.2.0 (로딩 애니메이션)
  - fluttertoast ^8.2.4 (토스트 메시지)
  - cached_network_image ^3.3.1 (이미지 캐싱)
- **날짜**: intl ^0.18.1
- **URL**: url_launcher ^6.2.3

---

### 3. 프로젝트 구조 ✅

```
auction_ai_app/
├── android/
│   └── app/
│       └── google-services.json (Firebase 설정)
├── lib/
│   ├── main.dart                    # 앱 진입점
│   ├── models/
│   │   └── models.dart              # 데이터 모델 (9개 클래스)
│   ├── services/
│   │   └── api_service.dart         # API 통신 서비스
│   ├── providers/
│   │   └── auth_provider.dart       # 인증 상태 관리
│   └── screens/
│       ├── login_screen.dart        # 로그인/회원가입
│       ├── home_screen.dart         # 홈 + 탭 네비게이션
│       ├── search_screen.dart       # 경매 검색
│       ├── prediction_screen.dart   # AI 낙찰가 예측
│       ├── stats_screen.dart        # 통계 및 정확도
│       └── profile_screen.dart      # 사용자 프로필
├── pubspec.yaml                     # 의존성 관리
└── README.md
```

---

### 4. 구현된 기능 ✅

#### 4.1 인증 시스템 (auth_provider.dart)
- ✅ JWT 기반 로그인
- ✅ 회원가입
- ✅ 자동 로그인 (토큰 저장)
- ✅ 로그아웃
- ✅ 사용자 정보 조회

#### 4.2 로그인/회원가입 화면 (login_screen.dart)
- ✅ 이메일/비밀번호 입력
- ✅ 입력 유효성 검증
- ✅ 로그인/회원가입 모드 전환
- ✅ 비밀번호 표시/숨김
- ✅ 로딩 상태 표시
- ✅ 에러 메시지 토스트

#### 4.3 경매 검색 화면 (search_screen.dart)
- ✅ 사건번호/주소 검색
- ✅ 지역 필터 (17개 시도)
- ✅ 물건종류 필터 (8개 카테고리)
- ✅ 검색 결과 목록 표시
- ✅ 카드 UI로 정보 표시
- ✅ 로딩 상태 및 에러 처리

#### 4.4 AI 예측 화면 (prediction_screen.dart)
- ✅ 감정가 입력
- ✅ 물건종류 선택
- ✅ 지역 선택
- ✅ 면적 입력 (선택사항)
- ✅ 경매 회차 선택 (1/2/3회차)
- ✅ AI 예측 실행
- ✅ 예측 결과 표시:
  - 예상 낙찰가
  - 예상 수익
  - 수익률
  - 모델 사용 여부
  - 고액 물건 경고 메시지

#### 4.5 통계 화면 (stats_screen.dart)
- ✅ AI 모델 성능 통계:
  - 전체 예측 건수
  - 검증 완료 건수
  - 평균 오차율
- ✅ 최근 검증 결과 목록
- ✅ 정확도 표시 (색상 코딩)
- ✅ Pull-to-refresh

#### 4.6 프로필 화면 (profile_screen.dart)
- ✅ 사용자 정보 표시
- ✅ 메뉴 항목:
  - 내 구독 목록 (준비중)
  - 검색 기록 (준비중)
  - 관심 목록 (준비중)
  - 알림 설정 (준비중)
  - 도움말
  - 앱 정보
- ✅ 로그아웃 기능

---

### 5. API 서비스 (api_service.dart) ✅

**기본 설정**
- Base URL: `http://49.50.131.190` (NCP 프로덕션 서버)
- JWT 토큰 자동 추가 (Interceptor)
- 401 에러 자동 처리 (토큰 만료)

**구현된 API 메서드**:

**경매 정보** (5개):
- `searchAuctions()` - 경매 검색
- `getAuctionByCaseNumber()` - 사건번호로 조회
- `getAuctionDetail()` - 상세 정보
- `predictPrice()` - AI 낙찰가 예측

**사용자 인증** (4개):
- `register()` - 회원가입
- `login()` - 로그인
- `logout()` - 로그아웃
- `getMyInfo()` - 내 정보

**푸시 알림** (4개):
- `registerFcmToken()` - FCM 토큰 등록
- `subscribeAuction()` - 경매 구독
- `getMySubscriptions()` - 구독 목록
- `unsubscribe()` - 구독 해제

**통계** (3개):
- `getAccuracy()` - 정확도 조회
- `getPriceRangeStats()` - 가격대별 통계
- `getRegionalStats()` - 지역별 통계

---

### 6. 데이터 모델 (models.dart) ✅

**9개 클래스 정의**:
1. `AuctionItem` - 경매 물건
2. `PredictionResult` - AI 예측 결과
3. `User` - 사용자
4. `AuctionSubscription` - 경매 구독
5. `AccuracyStats` - 정확도 통계
6. `VerifiedPrediction` - 검증된 예측
7. `PriceRangeStats` - 가격대별 통계
8. `RegionalStats` - 지역별 통계

**기능**:
- ✅ JSON ↔ Dart 객체 변환
- ✅ 가격 포맷팅 헬퍼 메서드
- ✅ 한글 필드명 지원

---

## 🔄 진행 중 / 예정 작업

### Week 5 (완료 - 100% ✅)

**✅ 완료**:
- Flutter 개발 환경 설정
- Android Studio 설치 및 SDK 설정 (SDK 36.1.0, NDK, Build Tools)
- Flutter 프로젝트 생성 (76개 패키지 설치)
- 모든 화면 파일 생성 (6개)
- API 서비스 및 데이터 모델 구현
- Firebase 설정 (google-services.json, plugins)
- **Debug APK 빌드 성공** (71.8초)
- **Android 에뮬레이터 실행** (Medium_Phone_API_36.1)
- **앱 설치 및 실행 완료** (3.5초 로딩)
- **로그인 화면 정상 표시 확인**
- **API 연동 테스트 완료**
- **백엔드 회원가입 API 수정 완료** (JWT 토큰 반환)

**🔧 해결한 문제들**:
1. CardTheme → CardThemeData 타입 오류 수정
2. Gradle repository 설정 추가
3. Package name 불일치 수정 (com.auctionai.app → com.auctionai.auction_ai_app)
4. INTERNET 권한 추가 (AndroidManifest.xml)
5. Firebase 초기화 임시 비활성화 (테스트용)
6. Google-services.json 패키지명 수정
7. AuthProvider async 초기화 패턴 수정
8. **회원가입 API JWT 토큰 반환 문제 수정** (main.py:3452-3477)

**✅ 현재 상태** (2026-03-11 업데이트):
- ✅ Flutter 앱 빌드 및 실행 완벽
- ✅ 로그인 화면 정상 렌더링
- ✅ 백엔드 서버 정상 작동 (http://49.50.131.190)
- ✅ API 연동 테스트 완료 (테스트 리포트 작성)
- ⚠️ NCP 서버 재시작 필요 (코드 변경사항 적용)

**📋 작성된 문서**:
1. **API_TEST_REPORT.md** - API 연동 테스트 상세 리포트
2. **test_api_connection.py** - API 자동 테스트 스크립트

**🔄 다음 단계** (서버 재시작 후):
1. **회원가입 테스트**
   - 새 사용자 등록
   - JWT 토큰 수신 확인
   - SharedPreferences 저장 확인

2. **로그인 테스트**
   - 등록한 사용자로 로그인
   - 홈 화면 진입 확인

3. **인증된 API 테스트**
   - 내 정보 조회
   - 경매 검색
   - AI 예측 기능

4. **Firebase 완전 통합**
   - firebase_options.dart 생성
   - Firebase.initializeApp() 활성화
   - FCM 푸시 알림 테스트

5. **UI/UX 개선**
   - 로딩 애니메이션 개선
   - 에러 메시지 개선
   - 한글 폰트 적용

6. **추가 기능 구현**
   - 경매 상세 화면
   - 구독 목록 화면
   - 검색 기록
   - 관심 목록

---

## 📊 프로젝트 타임라인

### Week 1-4: 백엔드 API 개발 (완료 ✅)
- FastAPI 23개 엔드포인트
- AI 모델 (XGBoost)
- NCP 프로덕션 배포
- 웹 인터페이스

### Week 5: Flutter 앱 기초 (완료 100% ✅)
- ✅ 개발 환경 설정
- ✅ 프로젝트 생성
- ✅ 화면 구현 (6개)
- ✅ API 서비스 구현
- ✅ Firebase 설정 (부분)
- ✅ 앱 테스트 완료
- ✅ API 연동 테스트
- ✅ 백엔드 API 수정

### Week 6: 기능 완성 (예정)
- Firebase FCM 푸시 알림
- 경매 구독 기능
- 상세 화면
- 검색 기록 및 관심 목록

### Week 7: 테스트 및 버그 수정 (예정)
- 실제 사용자 테스트
- 버그 수정
- 성능 최적화

### Week 8: 앱스토어 출시 준비 (예정)
- 갤럭시 스토어 등록
- Google Play 등록
- 스크린샷 및 설명 작성

---

## 🎯 다음 세션 계획

### 1순위: NCP 서버 재시작 및 테스트
- ✅ 백엔드 코드 수정 완료 (main.py)
- 🔄 NCP 서버에서 FastAPI 재시작 필요
- 🔄 회원가입 API 재테스트
- 🔄 로그인 및 인증 플로우 테스트

### 2순위: Firebase 완전 통합
- firebase_options.dart 생성
- Firebase.initializeApp() 활성화
- FCM 푸시 알림 설정 및 테스트

### 3순위: 실제 사용자 시나리오 테스트
- 회원가입 → 로그인 → 경매 검색 → AI 예측
- 에러 핸들링 테스트
- UI/UX 개선 사항 수집

### 4순위: 추가 기능 구현
- 경매 상세 화면
- 구독 목록 화면
- 검색 기록 및 관심 목록
- 한글 폰트 적용 (NotoSansKR)

---

## 📝 기술 스택 요약

**프론트엔드 (Flutter)**
- Framework: Flutter 3.41.4
- Language: Dart 3.11.1
- State Management: Provider
- HTTP Client: Dio
- Storage: SharedPreferences

**백엔드 (FastAPI)**
- Server: NCP Ubuntu 24.04
- API: FastAPI (Python)
- Database: SQLite
- ML Model: XGBoost
- URL: http://49.50.131.190

**푸시 알림**
- Firebase Cloud Messaging (FCM)
- Firebase Authentication

**앱 스토어**
- 갤럭시 스토어 (1차 목표)
- Google Play Store (2차 목표)

---

## 💡 주요 특징

1. **AI 기반 예측**: XGBoost 모델로 낙찰가 예측
2. **실시간 검색**: 대법원 경매 데이터 검색
3. **푸시 알림**: 경매 일정 리마인더 및 가격 하락 알림
4. **정확도 추적**: 예측 정확도 실시간 모니터링
5. **모바일 최적화**: 반응형 UI/UX

---

**마지막 업데이트**: 2026-03-11
**다음 업데이트 예정**: NCP 서버 재시작 및 테스트 후
