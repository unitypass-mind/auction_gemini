# Flutter 개발 환경 설정 가이드 (Windows)

**작성일**: 2026-03-09
**대상**: 경매 AI 앱 개발자
**예상 소요 시간**: 30-60분

---

## 📋 목차

1. [사전 요구사항](#사전-요구사항)
2. [Flutter SDK 설치](#flutter-sdk-설치)
3. [Android Studio 설치](#android-studio-설치)
4. [환경 변수 설정](#환경-변수-설정)
5. [설치 확인](#설치-확인)
6. [프로젝트 생성](#프로젝트-생성)

---

## 사전 요구사항

### 시스템 요구사항
- Windows 10 이상 (64-bit)
- 디스크 여유 공간: 2.5GB (Flutter SDK + Android Studio 10GB)
- RAM: 8GB 이상 권장

### 필수 도구
- Git (이미 설치됨 ✅)
- PowerShell 5.0 이상

---

## Flutter SDK 설치

### 방법 1: 수동 다운로드 (권장)

1. **Flutter SDK 다운로드**
   - URL: https://docs.flutter.dev/get-started/install/windows
   - 또는 직접 다운로드: https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.19.0-stable.zip

2. **압축 해제**
   ```powershell
   # C:\src 폴더에 압축 해제 (권장 경로)
   mkdir C:\src
   # 다운로드한 zip 파일을 C:\src에 압축 해제
   # 최종 경로: C:\src\flutter
   ```

3. **환경 변수 설정**
   - 시스템 환경 변수 Path에 추가: `C:\src\flutter\bin`

   **PowerShell로 설정 (관리자 권한)**:
   ```powershell
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\src\flutter\bin", "Machine")
   ```

   **GUI로 설정**:
   - Windows 검색 → "환경 변수" 입력
   - "시스템 환경 변수 편집" 클릭
   - "환경 변수" 버튼 클릭
   - "Path" 선택 → "편집" 클릭
   - "새로 만들기" → `C:\src\flutter\bin` 입력
   - "확인" 클릭

4. **새 터미널 열기**
   - 환경 변수 적용을 위해 터미널/Git Bash 재시작

5. **Flutter 설치 확인**
   ```bash
   flutter --version
   flutter doctor
   ```

### 방법 2: Chocolatey 패키지 매니저 (빠른 설치)

```powershell
# PowerShell 관리자 권한으로 실행
choco install flutter
```

---

## Android Studio 설치

### 1. Android Studio 다운로드
- URL: https://developer.android.com/studio
- 파일: android-studio-*.exe 다운로드

### 2. 설치 과정
1. 다운로드한 exe 파일 실행
2. "Next" 클릭
3. "Android Virtual Device" 체크 확인 ✅
4. 설치 경로 확인 (기본: C:\Program Files\Android\Android Studio)
5. "Install" 클릭
6. 설치 완료 후 "Finish" 클릭

### 3. Android Studio 초기 설정
1. Android Studio 실행
2. "Standard" 설치 타입 선택
3. UI 테마 선택 (Darcula 또는 Light)
4. SDK 구성 요소 다운로드 대기 (약 2-5GB)

### 4. Flutter 플러그인 설치
1. Android Studio 실행
2. Configure → Plugins 클릭
3. "Flutter" 검색
4. "Install" 클릭
5. "Dart" 플러그인도 자동 설치됨
6. Android Studio 재시작

### 5. Android SDK 설정
1. Tools → SDK Manager
2. "SDK Platforms" 탭
   - Android 14.0 (API 34) 체크 ✅
   - Android 13.0 (API 33) 체크 ✅
3. "SDK Tools" 탭
   - Android SDK Build-Tools 체크 ✅
   - Android SDK Command-line Tools 체크 ✅
   - Android Emulator 체크 ✅
4. "Apply" 클릭

---

## 설치 확인

### Flutter Doctor 실행

```bash
flutter doctor -v
```

**정상 출력 예시**:
```
[✓] Flutter (Channel stable, 3.19.0, on Microsoft Windows)
[✓] Android toolchain - develop for Android devices (Android SDK version 34.0.0)
[✓] Chrome - develop for the web
[✓] Visual Studio - develop Windows apps (Visual Studio Community 2022)
[✓] Android Studio (version 2023.2)
[✓] Connected device (1 available)
[✓] Network resources
```

### 문제 해결

#### 1. Android licenses 에러
```bash
flutter doctor --android-licenses
# 모든 라이선스에 'y' 입력
```

#### 2. Visual Studio 관련 경고 (Windows 앱 개발용, 선택사항)
- 무시 가능 (Android 앱만 개발하는 경우)

#### 3. Chrome 경고
```bash
# Chrome이 설치되어 있다면 무시 가능
# 웹 개발이 필요 없으면 무시
```

---

## Android 에뮬레이터 설정

### 1. AVD (Android Virtual Device) 생성

```bash
# Android Studio에서 생성 (권장)
# Tools → Device Manager → Create Device
```

**또는 명령줄로 생성**:
```bash
# 사용 가능한 시스템 이미지 확인
flutter emulators

# 기본 에뮬레이터 생성
flutter emulators --create
```

### 2. 에뮬레이터 실행

```bash
# AVD 목록 확인
flutter emulators

# 에뮬레이터 실행
flutter emulators --launch <emulator_id>
```

**Android Studio에서 실행**:
- Device Manager → 재생 버튼(▶) 클릭

---

## 프로젝트 생성

### 1. Flutter 프로젝트 생성

```bash
cd C:\Users\unity\auction_gemini
flutter create auction_ai_app

# 또는 조직명 지정
flutter create --org com.auctionai auction_ai_app
```

### 2. 프로젝트 구조 확인

```
auction_ai_app/
├── android/          # Android 네이티브 코드
├── ios/              # iOS 네이티브 코드
├── lib/              # Flutter Dart 코드
│   └── main.dart     # 앱 진입점
├── test/             # 테스트 코드
├── pubspec.yaml      # 의존성 관리
└── README.md
```

### 3. 프로젝트 실행

```bash
cd auction_ai_app

# 의존성 설치
flutter pub get

# 앱 실행 (에뮬레이터 실행 상태에서)
flutter run
```

---

## VS Code 설정 (선택사항)

### 1. VS Code 확장 설치
- Flutter (Dart-Code.flutter)
- Dart (Dart-Code.dart-code)

### 2. Flutter 경로 설정
```json
// settings.json
{
  "dart.flutterSdkPath": "C:\\src\\flutter"
}
```

---

## 다음 단계

Flutter 설치 완료 후:

1. ✅ Flutter 프로젝트 생성
2. Firebase 설정 (firebase-service-account.json 연동)
3. 의존성 패키지 추가 (dio, provider, firebase_messaging)
4. 로그인 화면 구현
5. API 연동

---

## 문제 해결

### Flutter 명령어가 인식되지 않을 때
```bash
# 환경 변수 Path 확인
echo $env:Path

# Flutter 경로가 있는지 확인
# 없으면 환경 변수 재설정 후 터미널 재시작
```

### Android 라이선스 동의 필요
```bash
flutter doctor --android-licenses
```

### Gradle 빌드 에러
```bash
cd auction_ai_app/android
./gradlew clean
cd ..
flutter clean
flutter pub get
flutter run
```

---

## 참고 자료

- Flutter 공식 문서: https://docs.flutter.dev
- Flutter 설치 가이드: https://docs.flutter.dev/get-started/install/windows
- Android Studio 다운로드: https://developer.android.com/studio
- Firebase Flutter 설정: https://firebase.google.com/docs/flutter/setup

---

**작성자**: Claude Code
**최종 업데이트**: 2026-03-09
