# Play Store 출시 가이드

## 📱 경매 AI 앱 - Google Play Store 출시 준비

### 목차
1. [Play Console 등록](#1-play-console-등록)
2. [앱 서명 키 생성](#2-앱-서명-키-생성)
3. [앱 정보 작성](#3-앱-정보-작성)
4. [스크린샷 준비](#4-스크린샷-준비)
5. [개인정보처리방침](#5-개인정보처리방침)
6. [출시 체크리스트](#6-출시-체크리스트)

---

## 1. Play Console 등록

### 비용
- **일회성 등록 비용**: $25 (약 33,000원)
- 신용카드 결제 필요

### 등록 단계
1. [Google Play Console](https://play.google.com/console) 접속
2. "개발자 계정 만들기" 클릭
3. $25 등록 비용 결제
4. 개발자 정보 입력
   - 이름 또는 회사명
   - 이메일 주소
   - 전화번호
   - 주소

---

## 2. 앱 서명 키 생성

### 현재 상태
- ✅ APK 빌드 완료: `build/app/outputs/flutter-apk/app-release.apk`
- ✅ 크기: 51.0MB
- ✅ Firebase 통합 완료

### 서명 키 생성 (처음 출시 시)
```bash
cd C:\Users\unity\auction_gemini\auction_ai_app\android\app

keytool -genkey -v -keystore upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload

# 입력 정보:
# - 키 저장소 비밀번호: [안전한 비밀번호 입력]
# - 이름: [개발자 이름]
# - 조직 단위: [선택사항]
# - 조직: [회사명 또는 개인]
# - 시/도: Seoul
# - 국가 코드: KR
```

### key.properties 파일 생성
`android/key.properties` 파일 생성:
```properties
storePassword=[키 저장소 비밀번호]
keyPassword=[키 비밀번호]
keyAlias=upload
storeFile=upload-keystore.jks
```

### build.gradle 수정
`android/app/build.gradle`에 서명 설정 추가:
```gradle
def keystoreProperties = new Properties()
def keystorePropertiesFile = rootProject.file('key.properties')
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
}

android {
    ...
    signingConfigs {
        release {
            keyAlias keystoreProperties['keyAlias']
            keyPassword keystoreProperties['keyPassword']
            storeFile keystoreProperties['storeFile'] ? file(keystoreProperties['storeFile']) : null
            storePassword keystoreProperties['storePassword']
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
        }
    }
}
```

### ⚠️ 보안 주의사항
`.gitignore`에 추가:
```gitignore
# 키 파일 - 절대 Git에 커밋하지 마세요!
**/key.properties
**/upload-keystore.jks
```

---

## 3. 앱 정보 작성

### 앱 이름
**한글**: 경매 AI - 부동산 경매 낙찰가 예측
**영문**: Auction AI - Real Estate Auction Price Prediction

### 짧은 설명 (80자 이내)
```
AI 기반 부동산 경매 낙찰가 예측 및 실시간 경매 정보 제공
```

### 자세한 설명
```markdown
# 경매 AI - 부동산 경매의 스마트한 동반자

## 📊 주요 기능

### 1. AI 낙찰가 예측
- XGBoost 머신러닝 모델 기반 (평균 오차율 11-12%)
- 58개 특성 분석으로 정확한 예측
- 감정가, 면적, 지역, 경매회차 등 종합 분석

### 2. 실시간 경매 정보
- 전국 법원 경매 정보 실시간 조회
- 사건번호, 지역, 물건종류로 검색
- 경매 일정 및 입찰 정보 확인

### 3. 전체 분석
- AI 예측가와 수익성 분석
- 실거래가 기반 시세 정보
- 입찰 전략 추천

### 4. 통계 및 정확도
- 과거 예측 정확도 통계
- 지역별, 물건별 낙찰 데이터
- 투명한 AI 성능 공개

### 5. 맞춤 예측
- 사용자 입력 기반 예측
- 다양한 시나리오 테스트
- 수익성 계산

## 💡 이런 분들에게 추천합니다
- 부동산 경매 투자를 고려하는 분
- 경매 물건의 적정 낙찰가를 알고 싶은 분
- 데이터 기반 투자 결정을 원하는 분
- 경매 정보를 한눈에 보고 싶은 분

## 🔒 개인정보 보호
- 최소한의 정보만 수집 (이메일, 비밀번호)
- 안전한 JWT 토큰 인증
- HTTPS 보안 통신

## 📞 고객 지원
- 이메일: support@auction-ai.kr
- 웹사이트: https://auction-ai.kr
- 운영 시간: 평일 09:00 - 18:00

## ⚠️ 중요 공지
본 앱의 AI 예측은 참고 자료일 뿐이며, 실제 투자 결정은 사용자의 책임입니다.
경매 투자 시 충분한 조사와 전문가 상담을 권장합니다.
```

### 카테고리
- **주 카테고리**: 금융 (Finance)
- **보조 카테고리**: 비즈니스 (Business)

### 연락처 정보
- **이메일**: support@auction-ai.kr
- **웹사이트**: https://auction-ai.kr
- **전화번호**: [선택사항]

---

## 4. 스크린샷 준비

### 필수 스크린샷 (최소 2장, 최대 8장)
**크기**: 1080 x 1920px (16:9 비율)

### 추천 스크린샷 구성 (5장)
1. **메인 화면** - 검색 탭
   - 사건번호 검색 예시
   - 깔끔한 UI

2. **전체분석 화면**
   - AI 예측가 표시
   - 수익성 분석
   - 입찰 전략 추천

3. **통계 화면**
   - 과거 예측 정확도
   - 그래프 시각화

4. **AI예측 화면**
   - 사용자 입력 폼
   - 맞춤 예측 결과

5. **로그인 화면**
   - 세련된 디자인
   - 회원가입 옵션

### 스크린샷 캡처 방법
```bash
# Android 에뮬레이터에서 캡처
1. Android Studio 에뮬레이터 실행
2. 각 화면 이동
3. 에뮬레이터 사이드바 > 스크린샷 버튼 클릭
4. 1080x1920 크기로 저장
```

### 프로모션 그래픽 (선택사항)
**크기**: 1024 x 500px
**내용**: 앱의 주요 기능 3개를 한눈에 보여주는 배너

---

## 5. 개인정보처리방침

### 필수 항목
Play Store 출시를 위해 개인정보처리방침 페이지 필요

### 작성 내용
```markdown
# 경매 AI 개인정보처리방침

## 1. 수집하는 개인정보
- 이메일 주소
- 비밀번호 (암호화 저장)
- 이름
- FCM 토큰 (푸시 알림용)

## 2. 개인정보의 이용 목적
- 회원 가입 및 로그인
- 푸시 알림 서비스 제공
- 고객 문의 응대

## 3. 개인정보 보유 기간
- 회원 탈퇴 시까지
- 탈퇴 후 즉시 삭제

## 4. 개인정보 제3자 제공
- 제3자에게 개인정보를 제공하지 않습니다
- Firebase (Google)를 통한 푸시 알림 서비스만 사용

## 5. 개인정보 파기 절차
- 탈퇴 요청 시 즉시 파기
- 복구 불가능하게 영구 삭제

## 6. 이용자의 권리
- 개인정보 열람 요청
- 개인정보 수정 요청
- 회원 탈퇴 (삭제 요청)

## 7. 개인정보 보호책임자
- 이메일: support@auction-ai.kr
- 응답 시간: 평일 09:00 - 18:00

## 8. 개인정보처리방침 변경
- 변경 시 앱 내 공지
- 최종 수정일: 2026-03-21
```

### 호스팅
개인정보처리방침은 웹사이트에 게시 필요:
- URL: https://auction-ai.kr/privacy-policy
- 또는 GitHub Pages 활용

---

## 6. 출시 체크리스트

### 앱 준비
- [ ] APK 빌드 완료 (app-release.apk)
- [ ] 서명 키 생성 및 보안 저장
- [ ] Firebase 연동 테스트
- [ ] 푸시 알림 테스트
- [ ] 로그인/회원가입 테스트
- [ ] 모든 기능 테스트 (실기기)

### Play Console 준비
- [ ] Google Play Console 계정 생성 ($25)
- [ ] 앱 이름 작성
- [ ] 짧은 설명 작성
- [ ] 자세한 설명 작성
- [ ] 카테고리 선택
- [ ] 연락처 정보 입력

### 미디어 준비
- [ ] 스크린샷 5장 (1080x1920)
- [ ] 앱 아이콘 (512x512)
- [ ] 프로모션 그래픽 (1024x500, 선택사항)

### 법적 준비
- [ ] 개인정보처리방침 작성
- [ ] 개인정보처리방침 웹 페이지 게시
- [ ] 이용약관 작성 (선택사항)

### 출시 전 최종 확인
- [ ] 대상 국가: 대한민국
- [ ] 연령 등급: 전체 이용가
- [ ] 콘텐츠 등급 설문 완료
- [ ] 광고 포함 여부: 아니오
- [ ] 가격: 무료

---

## 7. 출시 프로세스

### 1단계: 앱 생성
1. Play Console > "앱 만들기" 클릭
2. 앱 이름 입력: "경매 AI"
3. 기본 언어: 한국어
4. 앱 또는 게임: 앱
5. 무료 또는 유료: 무료

### 2단계: 대시보드 완성
Play Console 대시보드의 모든 필수 항목 완료:
- ✅ 앱 액세스
- ✅ 광고
- ✅ 콘텐츠 등급
- ✅ 대상층 및 콘텐츠
- ✅ 스토어 등록정보

### 3단계: 프로덕션 릴리스
1. "프로덕션" 트랙 선택
2. "새 릴리스 만들기" 클릭
3. APK 업로드
4. 출시 노트 작성
5. 검토 후 "출시" 클릭

### 4단계: 심사 대기
- 심사 시간: 보통 1-3일
- 상태 확인: Play Console 대시보드

### 5단계: 출시 완료
- 승인 후 Google Play Store에서 검색 가능
- 링크: `https://play.google.com/store/apps/details?id=com.example.auction_ai_app`

---

## 8. 출시 후 관리

### 모니터링
- 다운로드 수
- 평점 및 리뷰
- 충돌 보고서
- ANR (Application Not Responding) 보고서

### 업데이트
- 버그 수정
- 새 기능 추가
- 사용자 피드백 반영

### 마케팅
- 앱 스토어 최적화 (ASO)
- 소셜 미디어 홍보
- 블로그/카페 홍보

---

## 9. 문의 및 지원

### 문제 발생 시
1. Play Console 고객센터
2. Flutter 커뮤니티
3. Firebase 지원 포럼

### 참고 자료
- [Play Console 도움말](https://support.google.com/googleplay/android-developer)
- [Flutter 앱 출시 가이드](https://flutter.dev/docs/deployment/android)
- [Firebase 설정 가이드](https://firebase.google.com/docs/flutter/setup)

---

**작성일**: 2026-03-21
**작성자**: Claude Code
**앱 버전**: 1.0.0+1
**상태**: 출시 준비 중 🚀
