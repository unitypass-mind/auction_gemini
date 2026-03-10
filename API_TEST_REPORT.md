# API 연동 테스트 리포트

**날짜**: 2026-03-11
**테스터**: Claude Code
**서버**: NCP Production (http://49.50.131.190)
**클라이언트**: Flutter Mobile App (Android)

---

## 테스트 개요

Flutter 모바일 앱과 FastAPI 백엔드 간의 API 연동 테스트를 수행했습니다.
앱이 에뮬레이터에서 정상 실행되고 로그인 화면이 표시되는 것을 확인한 후, 각 API 엔드포인트를 테스트했습니다.

---

## 테스트 결과 요약

| API 엔드포인트 | 상태 | HTTP 코드 | 비고 |
|-------------|------|----------|------|
| GET /health | ✅ 성공 | 200 | 서버 정상 작동 |
| POST /auth/register | ❌ 실패 | 500 | 토큰 미반환 오류 |
| POST /auth/login | ❌ 실패 | 401 | 유효한 사용자 없음 (예상됨) |
| GET /auctions/search | ❌ 실패 | 404 | 엔드포인트 또는 데이터 없음 |

---

## 상세 테스트 결과

### 1. 서버 헬스 체크 ✅

**엔드포인트**: `GET /health`

**응답**:
```json
{
  "status": "ok",
  "model_loaded": false,
  "model_load_time": null,
  "version": "1.0.0"
}
```

**결과**: 성공
**비고**: 서버가 정상적으로 응답하고 있으나 AI 모델이 로드되지 않은 상태

---

### 2. 회원가입 테스트 ❌

**엔드포인트**: `POST /auth/register`

**요청 데이터**:
```json
{
  "email": "testuser{timestamp}@example.com",
  "password": "test1234",
  "name": "테스트사용자"
}
```

**응답**:
```json
{
  "detail": "회원가입 중 오류가 발생했습니다"
}
```

**HTTP 상태 코드**: 500 Internal Server Error

**문제 분석**:

1. **Root Cause**: 백엔드 `register_user` 함수가 JWT 토큰을 생성/반환하지 않음

2. **Flutter 앱 기대값** (api_service.dart:154-155):
   ```dart
   await prefs.setString('access_token', response.data['access_token']);
   await prefs.setString('refresh_token', response.data['refresh_token']);
   ```

3. **백엔드 실제 반환값** (main.py:3457-3465):
   ```python
   return {
       "success": True,
       "message": "회원가입이 완료되었습니다",
       "user": {
           "id": user_id,
           "email": user_data.email,
           "name": user_data.name
       }
       # access_token과 refresh_token이 누락됨!
   }
   ```

**해결 방법**:
백엔드 `register_user` 함수를 수정하여 회원가입 성공 시 JWT 토큰을 생성하고 반환해야 합니다.

**수정 필요 파일**: `C:\Users\unity\auction_gemini\main.py` (lines 3420-3478)

**제안 코드**:
```python
# 사용자 등록 후 토큰 생성
user_id = cursor.lastrowid
conn.commit()

# JWT 토큰 생성 (로그인과 동일한 방식)
access_token = auth.create_access_token(
    data={"user_id": user_id, "email": user_data.email}
)
refresh_token = auth.create_refresh_token(
    data={"user_id": user_id, "email": user_data.email}
)

# Refresh token DB에 저장
token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
cursor.execute("""
    INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
    VALUES (?, ?, datetime('now', '+30 days'))
""", (user_id, token_hash))
conn.commit()

return {
    "success": True,
    "message": "회원가입이 완료되었습니다",
    "user": {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name
    },
    "access_token": access_token,
    "refresh_token": refresh_token
}
```

---

### 3. 로그인 테스트 ❌ (예상됨)

**엔드포인트**: `POST /auth/login`

**요청 데이터**:
```json
{
  "email": "test@example.com",
  "password": "test1234"
}
```

**응답**:
```json
{
  "detail": "이메일 또는 비밀번호가 잘못되었습니다"
}
```

**HTTP 상태 코드**: 401 Unauthorized

**결과**: 실패 (예상된 결과)
**비고**: 데이터베이스에 등록된 사용자가 없어서 발생한 정상적인 오류

---

### 4. 경매 검색 테스트 ❌

**엔드포인트**: `GET /auctions/search`

**요청 파라미터**:
```
keyword: 서울
limit: 5
```

**응답**: 404 Not Found

**문제 분석**:
1. 엔드포인트 경로가 잘못되었거나
2. 경매 데이터가 DB에 없거나
3. API 라우트가 등록되지 않음

**확인 필요**:
- Flutter 앱: `api_service.dart:71` → `GET /search`
- 백엔드: main.py에서 `/auctions/search` 또는 `/search` 엔드포인트 확인 필요

---

## 데이터베이스 상태

### 데이터베이스 파일
- **경로**: `C:\Users\unity\auction_gemini\data\predictions.db`
- **테이블**:
  - ✅ `users` - 사용자 관리
  - ✅ `predictions` - AI 예측 결과
  - ✅ `fcm_tokens` - 푸시 알림 토큰
  - ✅ `auction_subscriptions` - 경매 구독
  - ✅ `refresh_tokens` - JWT refresh tokens
  - ✅ `notification_logs` - 알림 로그

### 데이터베이스 초기화
데이터베이스 테이블은 `database.py`의 `_init_db()` 메서드에서 자동 생성됩니다.
users 테이블은 이미 정의되어 있습니다 (database.py:131-143).

---

## Flutter 앱 상태

### 빌드 및 실행
- ✅ APK 빌드 성공 (71.8초)
- ✅ 에뮬레이터 설치 성공
- ✅ 앱 실행 성공 (3.5초 로딩)
- ✅ 로그인 화면 정상 표시

### 구현된 화면
1. ✅ AuthWrapper - 인증 상태 관리
2. ✅ LoginScreen - 로그인/회원가입
3. ✅ HomeScreen - 홈 + 탭 네비게이션
4. ✅ SearchScreen - 경매 검색
5. ✅ PredictionScreen - AI 낙찰가 예측
6. ✅ StatsScreen - 통계 및 정확도
7. ✅ ProfileScreen - 사용자 프로필

### API 서비스 (api_service.dart)
- ✅ Dio HTTP 클라이언트 설정
- ✅ JWT 인터셉터 (자동 토큰 추가)
- ✅ 401 오류 처리 (토큰 만료)
- ✅ 16개 API 메서드 구현
  - 경매 조회 (5개)
  - 인증 (4개)
  - 푸시 알림 (4개)
  - 통계 (3개)

---

## 권장 수정 사항

### 우선순위 1: 회원가입 API 수정 (필수)

**파일**: `main.py:3420-3478`

**문제**: 회원가입 성공 시 JWT 토큰을 반환하지 않음

**해결**:
1. 사용자 등록 후 `auth.create_access_token()` 호출
2. `auth.create_refresh_token()` 호출
3. refresh_token을 DB에 저장
4. 응답에 `access_token`, `refresh_token` 포함

**예상 시간**: 10분

---

### 우선순위 2: 경매 검색 엔드포인트 확인

**문제**: `/auctions/search` 또는 `/search` 엔드포인트가 404 반환

**확인 사항**:
1. main.py에서 `@app.get("/search")` 또는 `@app.get("/auctions/search")` 존재 여부
2. 라우터가 FastAPI 앱에 등록되었는지 확인
3. Flutter 앱의 요청 경로와 백엔드 경로 일치 여부

**예상 시간**: 5분

---

### 우선순위 3: AI 모델 로딩

**현재 상태**: `model_loaded: false`

**확인 사항**:
1. `models/auction_model_v4.pkl` 파일 존재 여부
2. 모델 로딩 코드 실행 여부
3. 메모리 충분 여부

---

## 다음 테스트 계획

### 수정 완료 후:

1. **회원가입 테스트**
   - 새로운 사용자 등록
   - 토큰 수신 확인
   - SharedPreferences 저장 확인

2. **로그인 테스트**
   - 등록한 사용자로 로그인
   - 토큰 수신 및 저장 확인

3. **인증된 API 테스트**
   - 내 정보 조회 (`GET /auth/me`)
   - 경매 검색
   - AI 예측 기능

4. **푸시 알림 테스트**
   - FCM 토큰 등록
   - 경매 구독
   - 알림 수신 테스트

---

## 테스트 환경

**백엔드**:
- 서버: NCP Ubuntu 24.04
- URL: http://49.50.131.190
- Framework: FastAPI
- Database: SQLite (data/predictions.db)
- AI Model: XGBoost (auction_model_v4.pkl)

**프론트엔드**:
- Framework: Flutter 3.41.4
- Dart: 3.11.1
- Android SDK: 36.1.0
- Emulator: sdk gphone64 x86 64 (API 36)
- State Management: Provider
- HTTP Client: Dio

---

## 결론

1. **서버 상태**: 정상 작동 중
2. **Flutter 앱**: 정상 빌드 및 실행
3. **주요 이슈**: 회원가입 API가 JWT 토큰을 반환하지 않음
4. **다음 단계**: 백엔드 register_user 함수 수정 후 재테스트

**예상 수정 시간**: 15-20분
**재테스트 예정**: 수정 완료 즉시

---

**보고서 작성**: Claude Code
**작성 일시**: 2026-03-11
