# Firebase Cloud Messaging 설정 가이드

## 개요
이 문서는 경매 AI 앱에서 FCM (Firebase Cloud Messaging) 푸시 알림을 사용하기 위한 Firebase 프로젝트 설정 방법을 안내합니다.

## 1. Firebase 프로젝트 생성

### 1.1 Firebase Console 접속
1. [Firebase Console](https://console.firebase.google.com/) 접속
2. Google 계정으로 로그인

### 1.2 새 프로젝트 생성
1. **"프로젝트 추가"** 버튼 클릭
2. 프로젝트 이름 입력: `auction-ai-app` (또는 원하는 이름)
3. Google Analytics 사용 여부 선택 (선택사항)
4. **"프로젝트 만들기"** 클릭
5. 프로젝트 생성 완료 대기 (약 30초~1분)

## 2. Firebase Cloud Messaging 활성화

### 2.1 Android 앱 추가
1. Firebase Console 프로젝트 개요 페이지에서 **Android 아이콘** 클릭
2. 앱 등록 정보 입력:
   - **Android 패키지 이름**: `com.auctionai.app` (Flutter 앱 패키지명과 동일해야 함)
   - **앱 닉네임**: `Auction AI` (선택사항)
   - **디버그 서명 인증서 SHA-1**: (선택사항, 나중에 추가 가능)
3. **"앱 등록"** 클릭

### 2.2 google-services.json 다운로드
1. `google-services.json` 파일 다운로드
2. 이 파일은 **Flutter 앱의 android/app/** 디렉토리에 복사해야 합니다
3. 현재는 서버 설정만 진행하므로 나중에 모바일 앱 개발 시 사용

### 2.3 FCM SDK 설정 건너뛰기
- 서버 측에서는 Firebase Admin SDK를 사용하므로 Android SDK 설정 단계는 건너뛰어도 됩니다
- **"콘솔로 이동"** 클릭

## 3. 서비스 계정 키 생성 (서버용)

### 3.1 서비스 계정 키 다운로드
1. Firebase Console에서 프로젝트 설정 (⚙️ 아이콘) 클릭
2. **"서비스 계정"** 탭 선택
3. **"새 비공개 키 생성"** 버튼 클릭
4. 확인 대화상자에서 **"키 생성"** 클릭
5. JSON 파일이 자동으로 다운로드됩니다
   - 파일명: `auction-ai-app-xxxxx-firebase-adminsdk-xxxxx.json` (예시)

### 3.2 서비스 계정 키 파일 배치
1. 다운로드한 JSON 파일의 이름을 `firebase-service-account.json`으로 변경
2. 파일을 프로젝트 루트 디렉토리에 복사:
   ```
   C:\Users\unity\auction_gemini\firebase-service-account.json
   ```

### 3.3 보안 주의사항 ⚠️
- **절대로 이 파일을 Git에 커밋하지 마세요!**
- `.gitignore`에 다음 항목이 포함되어 있는지 확인:
  ```
  firebase-service-account.json
  *.json  # 서비스 계정 키 파일
  ```

## 4. FCM 알림 테스트

### 4.1 서버 시작
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

시작 로그에서 다음 메시지 확인:
```
INFO: Firebase Admin SDK 초기화 완료
📅 알림 스케줄러 시작 완료
  - 경매 알림: 매일 오전 9시
  - 가격 하락 체크: 매일 오후 2시
```

### 4.2 테스트 알림 전송
```bash
curl -X POST "http://localhost:8000/notifications/test" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "여기에_FCM_토큰_입력",
    "title": "테스트 알림",
    "body": "FCM 설정이 정상적으로 완료되었습니다!"
  }'
```

**성공 응답:**
```json
{
  "success": true,
  "message": "테스트 알림이 전송되었습니다"
}
```

### 4.3 모바일 앱에서 FCM 토큰 얻기
실제 모바일 앱 개발 시, Flutter에서 FCM 토큰을 얻는 방법:

```dart
import 'package:firebase_messaging/firebase_messaging.dart';

// FCM 토큰 가져오기
String? fcmToken = await FirebaseMessaging.instance.getToken();
print('FCM Token: $fcmToken');

// 서버에 등록
await registerFcmToken(fcmToken);
```

## 5. 스케줄러 동작 확인

### 5.1 로그 파일 확인
```bash
# 스케줄러 로그 확인
tail -f logs/scheduler_20260305.log

# 메인 애플리케이션 로그 확인
tail -f logs/auction_api_20260305.log
```

### 5.2 예상 로그 메시지
```
=== 경매 알림 작업 시작 ===
내일(2026-03-06) 경매 3건 발견
경매 2024타경12345에 대한 구독자 5명 발견
경매 2024타경12345 알림 전송 완료: 성공=5, 실패=0
=== 경매 알림 작업 완료: 총 3건 처리 ===
```

## 6. 문제 해결

### 6.1 "Firebase 서비스 계정 키 파일을 찾을 수 없습니다"
- `firebase-service-account.json` 파일이 프로젝트 루트에 있는지 확인
- 파일명 철자가 정확한지 확인
- 파일 경로를 환경변수로 지정:
  ```bash
  export FIREBASE_SERVICE_ACCOUNT=/path/to/firebase-service-account.json
  ```

### 6.2 "Firebase 초기화 실패"
- JSON 파일 형식이 올바른지 확인
- 서비스 계정 키가 만료되지 않았는지 확인
- Firebase Console에서 새 키 생성 후 재시도

### 6.3 "유효하지 않은 FCM 토큰"
- 모바일 앱이 아직 개발되지 않은 경우 정상 (토큰이 없음)
- 모바일 앱에서 올바른 토큰을 얻었는지 확인
- 토큰이 만료되었을 수 있으므로 재발급 필요

### 6.4 알림이 전송되지 않음
- Firebase Console > Cloud Messaging에서 프로젝트 설정 확인
- 서버 로그에서 오류 메시지 확인
- FCM 토큰이 데이터베이스에 등록되어 있고 `is_active=1`인지 확인:
  ```sql
  SELECT * FROM fcm_tokens WHERE is_active = 1;
  ```

## 7. 프로덕션 배포 체크리스트

- [ ] Firebase 프로젝트 생성 완료
- [ ] 서비스 계정 키 다운로드 및 배치
- [ ] `.gitignore`에 서비스 계정 키 제외 설정
- [ ] 서버에서 Firebase 초기화 성공 확인
- [ ] 스케줄러 정상 동작 확인
- [ ] 테스트 알림 전송 성공
- [ ] 로그 파일 모니터링 설정
- [ ] NCP 서버에 서비스 계정 키 안전하게 업로드
- [ ] 환경변수 설정 (필요시)

## 8. 보안 모범 사례

### 8.1 서비스 계정 키 관리
- 프로덕션 환경에서는 **환경변수**로 키 경로 지정
- NCP Object Storage 또는 Secrets Manager 사용 고려
- 키 파일 접근 권한을 최소화 (chmod 600)

### 8.2 FCM 토큰 관리
- 만료된 토큰은 주기적으로 정리
- 로그아웃 시 토큰 비활성화 처리
- 토큰 유효성 검증 (`validate_fcm_token()` 함수 사용)

### 8.3 알림 남용 방지
- 동일 사용자에게 과도한 알림 방지 (rate limiting)
- 사용자가 알림 구독 해제할 수 있는 기능 제공
- 알림 로그 분석으로 이상 패턴 감지

## 9. 참고 자료

- [Firebase 공식 문서](https://firebase.google.com/docs)
- [Firebase Admin SDK - Python](https://firebase.google.com/docs/admin/setup)
- [FCM 메시지 구성](https://firebase.google.com/docs/cloud-messaging/concept-options)
- [FCM 서버 통합 가이드](https://firebase.google.com/docs/cloud-messaging/server)

## 10. 지원 및 문의

문제 발생 시:
1. 서버 로그 확인 (`logs/` 디렉토리)
2. Firebase Console > Cloud Messaging > 사용량 통계 확인
3. GitHub Issues에 로그와 함께 문의

---

**작성일**: 2026-03-05
**버전**: 1.0
**작성자**: Claude AI Assistant
