# Flutter 모바일 앱 배포 가이드

경매 AI 앱을 Google Play Store와 Apple App Store에 배포하기 위한 종합 가이드입니다.

**작성일**: 2026-03-17
**앱 버전**: 1.0.0+1
**프로덕션 API**: https://auction-ai.kr

---

## 목차

1. [현재 앱 상태](#1-현재-앱-상태)
2. [배포 전 체크리스트](#2-배포-전-체크리스트)
3. [Android 배포 가이드](#3-android-배포-가이드)
4. [iOS 배포 가이드](#4-ios-배포-가이드)
5. [Firebase 설정](#5-firebase-설정)
6. [테스트 가이드](#6-테스트-가이드)
7. [문제 해결](#7-문제-해결)

---

## 1. 현재 앱 상태

### ✅ 완료된 설정

- **API 엔드포인트**: HTTPS로 업데이트 완료 (`https://auction-ai.kr`)
- **Firebase 구성**: `google-services.json` 파일 존재
- **Android 빌드 설정**: Kotlin DSL 기반 Gradle 구성
- **의존성 패키지**:
  - dio (HTTP 통신)
  - firebase_core, firebase_messaging (푸시 알림)
  - shared_preferences (로컬 저장)
  - provider (상태 관리)

### ⚠️ 배포 전 필수 작업

1. **Firebase 초기화 활성화** (main.dart에서 주석 해제 필요)
2. **Android 릴리스 서명 설정** (현재 debug 키 사용 중)
3. **iOS App Transport Security 설정** (HTTPS 통신 허용)
4. **앱 아이콘 및 스플래시 스크린** 준비
5. **앱 스토어 메타데이터** 준비 (스크린샷, 설명, 키워드)

---

## 2. 배포 전 체크리스트

### 공통 체크리스트

- [ ] API 엔드포인트가 HTTPS로 설정되어 있는지 확인
- [ ] Firebase 프로젝트 생성 및 앱 등록 완료
- [ ] 앱 아이콘 준비 (1024x1024 PNG)
- [ ] 스플래시 스크린 준비
- [ ] 개인정보 처리방침 URL 준비
- [ ] 서비스 이용약관 URL 준비
- [ ] 앱 스토어 스크린샷 준비 (각 플랫폼별 요구사항 확인)
- [ ] 앱 설명 및 키워드 준비

### Android 체크리스트

- [ ] Google Play Console 개발자 계정 등록 ($25 일회성)
- [ ] 앱 서명 키 생성
- [ ] `key.properties` 파일 설정
- [ ] ProGuard 규칙 설정 (코드 난독화)
- [ ] 앱 번들(AAB) 빌드 테스트
- [ ] 내부 테스트 트랙 배포

### iOS 체크리스트

- [ ] Apple Developer 계정 등록 ($99/년)
- [ ] App ID 생성
- [ ] 프로비저닝 프로파일 생성
- [ ] 푸시 알림 인증서 설정
- [ ] Xcode 프로젝트 설정
- [ ] TestFlight 배포 테스트
- [ ] App Store Connect 앱 등록

---

## 3. Android 배포 가이드

### 3.1 앱 서명 키 생성

Android 앱 스토어 배포를 위해서는 릴리스 서명 키가 필요합니다.

```bash
# 키스토어 생성 (Windows에서 실행)
keytool -genkey -v -keystore C:\Users\unity\auction-ai-release.jks \
  -storetype JKS \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -alias auction-ai-key

# 입력 정보:
# - Keystore password: [안전한 비밀번호]
# - Key password: [Keystore password와 동일하게 설정 권장]
# - First and Last Name: [회사명 또는 개인 이름]
# - Organizational Unit: [부서명 또는 'Mobile Development']
# - Organization: [회사명 또는 'AuctionAI']
# - City/Locality: [도시명]
# - State/Province: [시/도]
# - Country Code: KR
```

**⚠️ 중요: 생성된 키스토어 파일과 비밀번호를 안전하게 보관하세요!**
- 키스토어를 분실하면 기존 앱을 업데이트할 수 없습니다
- 비밀번호 관리 도구(1Password, LastPass 등) 사용 권장

### 3.2 key.properties 파일 생성

앱 서명 정보를 Git에 커밋하지 않기 위해 별도 파일로 관리합니다.

```bash
# auction_ai_app/android/key.properties 파일 생성
cat > auction_ai_app/android/key.properties << 'EOF'
storePassword=<Keystore 비밀번호>
keyPassword=<Key 비밀번호>
keyAlias=auction-ai-key
storeFile=C:\\Users\\unity\\auction-ai-release.jks
EOF
```

**⚠️ 주의**: `key.properties` 파일은 `.gitignore`에 추가되어 있어야 합니다.

### 3.3 build.gradle.kts 수정

릴리스 빌드에서 실제 서명 키를 사용하도록 설정합니다.

**수정 파일**: `auction_ai_app/android/app/build.gradle.kts`

```kotlin
// 기존 코드 위에 추가 (plugins 블록 이전)
val keystorePropertiesFile = rootProject.file("key.properties")
val keystoreProperties = java.util.Properties()
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(java.io.FileInputStream(keystorePropertiesFile))
}

plugins {
    id("com.android.application")
    id("kotlin-android")
    id("dev.flutter.flutter-gradle-plugin")
    id("com.google.gms.google-services")
}

android {
    namespace = "com.auctionai.auction_ai_app"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    // ... (기존 설정 유지)

    // signingConfigs 블록 추가 (buildTypes 이전)
    signingConfigs {
        create("release") {
            if (keystorePropertiesFile.exists()) {
                keyAlias = keystoreProperties["keyAlias"] as String
                keyPassword = keystoreProperties["keyPassword"] as String
                storeFile = file(keystoreProperties["storeFile"] as String)
                storePassword = keystoreProperties["storePassword"] as String
            }
        }
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")

            // 코드 난독화 및 최적화 (선택사항)
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
}
```

### 3.4 ProGuard 규칙 설정

코드 난독화를 위한 ProGuard 규칙을 설정합니다.

**파일 생성**: `auction_ai_app/android/app/proguard-rules.pro`

```proguard
# Flutter wrapper
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.** { *; }
-keep class io.flutter.util.** { *; }
-keep class io.flutter.view.** { *; }
-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }

# Firebase
-keep class com.google.firebase.** { *; }
-keep class com.google.android.gms.** { *; }

# Dio (HTTP 클라이언트)
-keep class io.flutter.plugins.** { *; }

# Gson (JSON 직렬화)
-keepattributes Signature
-keepattributes *Annotation*
-keep class com.google.gson.** { *; }
-keep class * implements com.google.gson.TypeAdapter
-keep class * implements com.google.gson.TypeAdapterFactory
-keep class * implements com.google.gson.JsonSerializer
-keep class * implements com.google.gson.JsonDeserializer
```

### 3.5 AndroidManifest.xml 최종 확인

**파일**: `auction_ai_app/android/app/src/main/AndroidManifest.xml`

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <!-- 필수 권한 -->
    <uses-permission android:name="android.permission.INTERNET"/>

    <!-- 푸시 알림을 위한 권한 (Firebase Messaging) -->
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>

    <application
        android:label="경매 AI"
        android:name="${applicationName}"
        android:icon="@mipmap/ic_launcher"
        android:usesCleartextTraffic="false">

        <!-- MainActivity 설정 -->
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:launchMode="singleTop"
            android:theme="@style/LaunchTheme"
            android:configChanges="orientation|keyboardHidden|keyboard|screenSize|smallestScreenSize|locale|layoutDirection|fontScale|screenLayout|density|uiMode"
            android:hardwareAccelerated="true"
            android:windowSoftInputMode="adjustResize">

            <meta-data
              android:name="io.flutter.embedding.android.NormalTheme"
              android:resource="@style/NormalTheme" />

            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>

        <!-- Firebase Messaging Service -->
        <service
            android:name="io.flutter.plugins.firebase.messaging.FlutterFirebaseMessagingService"
            android:exported="false">
            <intent-filter>
                <action android:name="com.google.firebase.MESSAGING_EVENT" />
            </intent-filter>
        </service>

        <meta-data
            android:name="flutterEmbedding"
            android:value="2" />
    </application>
</manifest>
```

### 3.6 앱 번들(AAB) 빌드

```bash
# auction_ai_app 디렉토리에서 실행
cd auction_ai_app

# 의존성 업데이트
flutter pub get

# 릴리스 빌드 (Android App Bundle)
flutter build appbundle --release

# 빌드 결과: build/app/outputs/bundle/release/app-release.aab
```

**앱 번들 크기 확인:**
```bash
ls -lh build/app/outputs/bundle/release/app-release.aab
```

### 3.7 Google Play Console 배포

1. **Google Play Console 접속**: https://play.google.com/console
2. **새 앱 만들기** 클릭
3. **앱 세부정보** 입력:
   - 앱 이름: 경매 AI
   - 기본 언어: 한국어(대한민국)
   - 앱 또는 게임: 앱
   - 무료 또는 유료: 무료
4. **프로덕션 트랙** → **새 릴리스 만들기**
5. **App Bundle 업로드**: `app-release.aab` 파일 업로드
6. **출시 노트** 작성
7. **검토 및 출시** 클릭

**심사 기간**: 보통 1-3일 소요

---

## 4. iOS 배포 가이드

### 4.1 Apple Developer 계정 등록

1. **Apple Developer Program 가입**: https://developer.apple.com/programs/
2. **연간 비용**: $99 (약 ₩130,000)
3. **승인 기간**: 24-48시간

### 4.2 App ID 생성

1. **Apple Developer Console** 접속
2. **Certificates, Identifiers & Profiles** → **Identifiers**
3. **App ID 생성**:
   - Description: Auction AI App
   - Bundle ID: `com.auctionai.auction-ai-app` (Explicit)
   - Capabilities:
     - ✅ Push Notifications
     - ✅ Associated Domains (선택사항)

### 4.3 Info.plist 설정

**파일**: `auction_ai_app/ios/Runner/Info.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- 기존 설정 유지 -->

    <!-- 앱 이름 (한글) -->
    <key>CFBundleDisplayName</key>
    <string>경매 AI</string>

    <!-- 앱 버전 -->
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>

    <key>CFBundleVersion</key>
    <string>1</string>

    <!-- App Transport Security (HTTPS 통신) -->
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <false/>
        <key>NSExceptionDomains</key>
        <dict>
            <key>auction-ai.kr</key>
            <dict>
                <key>NSIncludesSubdomains</key>
                <true/>
                <key>NSTemporaryExceptionAllowsInsecureHTTPLoads</key>
                <false/>
                <key>NSTemporaryExceptionMinimumTLSVersion</key>
                <string>TLSv1.2</string>
            </dict>
        </dict>
    </dict>

    <!-- 카메라 권한 (나중에 필요할 경우) -->
    <!-- <key>NSCameraUsageDescription</key>
    <string>경매 물건 사진 촬영을 위해 카메라 접근이 필요합니다.</string> -->

    <!-- 사진 라이브러리 권한 (나중에 필요할 경우) -->
    <!-- <key>NSPhotoLibraryUsageDescription</key>
    <string>경매 물건 사진 업로드를 위해 사진 라이브러리 접근이 필요합니다.</string> -->

    <!-- 위치 권한 (나중에 필요할 경우) -->
    <!-- <key>NSLocationWhenInUseUsageDescription</key>
    <string>주변 경매 물건 검색을 위해 위치 정보가 필요합니다.</string> -->

    <!-- 푸시 알림 -->
    <key>UIBackgroundModes</key>
    <array>
        <string>remote-notification</string>
    </array>
</dict>
</plist>
```

### 4.4 Xcode 프로젝트 설정

```bash
# iOS 디렉토리로 이동
cd auction_ai_app/ios

# Pod 업데이트
pod install

# Xcode로 프로젝트 열기
open Runner.xcworkspace
```

**Xcode에서 설정:**

1. **General 탭**:
   - Display Name: `경매 AI`
   - Bundle Identifier: `com.auctionai.auction-ai-app`
   - Version: `1.0.0`
   - Build: `1`
   - Deployment Target: `iOS 13.0` 이상

2. **Signing & Capabilities 탭**:
   - ✅ Automatically manage signing
   - Team: [Apple Developer 계정 선택]
   - Provisioning Profile: Xcode Managed Profile
   - Capabilities 추가:
     - Push Notifications
     - Background Modes → Remote notifications

3. **Build Settings 탭**:
   - Enable Bitcode: `No` (Flutter 앱은 Bitcode 불필요)

### 4.5 iOS 앱 빌드 및 아카이브

```bash
# auction_ai_app 디렉토리에서 실행
cd auction_ai_app

# 의존성 업데이트
flutter pub get

# iOS 빌드 (릴리스 모드)
flutter build ios --release

# Xcode에서 아카이브
# Xcode → Product → Archive
# 아카이브 완료 후 → Distribute App → App Store Connect
```

### 4.6 App Store Connect 배포

1. **App Store Connect 접속**: https://appstoreconnect.apple.com
2. **My Apps** → **새로운 앱** 클릭
3. **앱 정보** 입력:
   - 플랫폼: iOS
   - 이름: 경매 AI
   - 기본 언어: 한국어
   - 번들 ID: com.auctionai.auction-ai-app
   - SKU: `auction-ai-app-ios`
4. **가격 및 사용 가능 여부**: 무료
5. **1.0 버전 준비** → 빌드 선택 (Xcode에서 업로드한 빌드)
6. **앱 스토어 정보** 입력:
   - 앱 이름
   - 부제목
   - 설명
   - 키워드
   - 스크린샷 (필수)
   - 개인정보 처리방침 URL
7. **심사 제출**

**심사 기간**: 보통 2-5일 소요

---

## 5. Firebase 설정

### 5.1 Firebase 프로젝트 확인

현재 `google-services.json` 파일이 존재하므로 Firebase 프로젝트는 이미 생성되어 있습니다.

**확인 사항:**
```bash
# google-services.json 내용 확인
cat auction_ai_app/android/app/google-services.json

# project_id 확인
```

### 5.2 iOS Firebase 설정 파일 추가

iOS 앱에도 Firebase 설정 파일이 필요합니다.

1. **Firebase Console** 접속: https://console.firebase.google.com
2. **프로젝트 선택** (google-services.json과 동일한 프로젝트)
3. **iOS 앱 추가** 클릭
4. **Apple 번들 ID** 입력: `com.auctionai.auction-ai-app`
5. **GoogleService-Info.plist** 다운로드
6. **Xcode**에서 `Runner` 폴더에 파일 추가 (Copy items if needed 체크)

### 5.3 main.dart Firebase 초기화 활성화

**파일**: `auction_ai_app/lib/main.dart`

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:firebase_core/firebase_core.dart';
import 'firebase_options.dart'; // Firebase CLI로 생성된 파일
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'providers/auth_provider.dart';
import 'providers/selected_auction_provider.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Firebase 초기화 (주석 해제)
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );

  runApp(const MyApp());
}

// ... (나머지 코드 동일)
```

### 5.4 firebase_options.dart 생성

Firebase CLI를 사용하여 플랫폼별 설정 파일을 자동 생성합니다.

```bash
# Firebase CLI 설치 (Node.js 필요)
npm install -g firebase-tools

# Firebase 로그인
firebase login

# Flutter 프로젝트에서 Firebase 설정
cd auction_ai_app
flutterfire configure
```

**선택 사항:**
- Select platforms: Android, iOS
- Firebase project: [기존 프로젝트 선택]

**생성 결과**: `lib/firebase_options.dart` 파일 자동 생성

### 5.5 Firebase Messaging (FCM) 설정

푸시 알림을 위한 FCM 설정은 이미 `pubspec.yaml`에 포함되어 있습니다.

**추가 설정 필요 (백엔드):**
- FastAPI 서버에서 FCM Admin SDK 설정
- 사용자 FCM 토큰 등록 API 구현 (이미 완료: `/notifications/register-token`)

---

## 6. 테스트 가이드

### 6.1 로컬 테스트

```bash
cd auction_ai_app

# Android 디바이스/에뮬레이터에서 테스트
flutter run --release

# iOS 시뮬레이터/디바이스에서 테스트
flutter run --release -d [device-id]

# 디바이스 목록 확인
flutter devices
```

### 6.2 API 연결 테스트

앱 실행 후 확인 사항:

1. **로그인/회원가입**: `https://auction-ai.kr/auth/login` 엔드포인트 연결 확인
2. **경매 검색**: `/auctions/search` API 호출 확인
3. **AI 예측**: `/predict/simple` 또는 `/auction?case_no=XXX` API 확인
4. **푸시 알림 등록**: FCM 토큰 등록 확인

**네트워크 로그 확인 (Android):**
```bash
# 앱 실행 중 Logcat 확인
flutter run --release
# 터미널에서 HTTP 요청/응답 로그 확인
```

### 6.3 릴리스 빌드 테스트

**Android APK 설치 테스트:**
```bash
# APK 빌드 (테스트용)
flutter build apk --release

# 생성된 APK 위치
# build/app/outputs/flutter-apk/app-release.apk

# 디바이스에 직접 설치
adb install build/app/outputs/flutter-apk/app-release.apk
```

**iOS 테스트 (TestFlight):**
1. Xcode에서 Archive 생성
2. App Store Connect에 업로드
3. TestFlight → 내부 테스트 그룹 생성
4. 테스터 초대 (이메일 주소)
5. TestFlight 앱에서 베타 테스트

### 6.4 성능 테스트

```bash
# 앱 크기 분석
flutter build appbundle --release --analyze-size

# 빌드 성능 분석
flutter build apk --release --analyze-size

# 프로파일 모드 실행 (성능 측정)
flutter run --profile
```

---

## 7. 문제 해결

### 7.1 일반적인 오류

**1. "Unable to connect to server" 오류**
- **원인**: HTTPS 인증서 문제 또는 네트워크 연결 실패
- **해결**:
  - 서버 상태 확인: `https://auction-ai.kr/model-status`
  - SSL 인증서 유효성 확인
  - 디바이스 인터넷 연결 확인

**2. "Firebase initialization failed" 오류**
- **원인**: `google-services.json` 또는 `GoogleService-Info.plist` 설정 오류
- **해결**:
  - Firebase Console에서 앱 등록 확인
  - 번들 ID/패키지명이 일치하는지 확인
  - `firebase_options.dart` 재생성: `flutterfire configure`

**3. "Signing for 'Runner' requires a development team" (iOS)**
- **원인**: Apple Developer 계정 미설정
- **해결**:
  - Xcode → Signing & Capabilities → Team 선택
  - Apple Developer 계정 등록 필요

**4. "Execution failed for task ':app:lintVitalRelease'" (Android)**
- **원인**: Lint 검사 실패
- **해결**:
  ```kotlin
  // android/app/build.gradle.kts에 추가
  android {
      lintOptions {
          checkReleaseBuilds = false
      }
  }
  ```

### 7.2 빌드 오류

**Gradle 빌드 오류:**
```bash
# Gradle 캐시 정리
cd auction_ai_app/android
./gradlew clean

# Flutter 클린 빌드
cd ..
flutter clean
flutter pub get
flutter build appbundle --release
```

**iOS Pod 오류:**
```bash
# Pod 재설치
cd auction_ai_app/ios
rm -rf Pods Podfile.lock
pod install

cd ..
flutter clean
flutter pub get
flutter build ios --release
```

### 7.3 배포 후 모니터링

**Firebase Crashlytics 설정 (선택사항):**
```yaml
# pubspec.yaml에 추가
dependencies:
  firebase_crashlytics: ^3.4.9
```

```dart
// main.dart에 추가
import 'package:firebase_crashlytics/firebase_crashlytics.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);

  // Crashlytics 설정
  FlutterError.onError = FirebaseCrashlytics.instance.recordFlutterFatalError;

  runApp(const MyApp());
}
```

**Google Play Console / App Store Connect에서 모니터링:**
- 크래시 리포트
- ANR (Application Not Responding) 분석
- 사용자 리뷰 및 평점
- 다운로드 및 설치 통계

---

## 8. 다음 단계

### 배포 후 할 일

1. **사용자 피드백 수집**: 앱 스토어 리뷰, 인앱 피드백 양식
2. **버전 업데이트 계획**: 주요 기능 추가, 버그 수정
3. **마케팅**:
   - 네이버 블로그, 카페 홍보
   - SNS 마케팅 (Instagram, Facebook)
   - Google Ads, Apple Search Ads
4. **분석 도구 통합**:
   - Google Analytics for Firebase
   - Mixpanel, Amplitude 등
5. **성능 최적화**:
   - 앱 크기 줄이기
   - 로딩 속도 개선
   - 메모리 사용량 최적화

### 참고 자료

- **Flutter 공식 배포 가이드**: https://flutter.dev/docs/deployment
- **Google Play Console 도움말**: https://support.google.com/googleplay/android-developer
- **App Store Connect 도움말**: https://developer.apple.com/help/app-store-connect/
- **Firebase 문서**: https://firebase.google.com/docs/flutter/setup

---

**작성자**: Claude Code
**최종 수정**: 2026-03-17
**버전**: 1.0
