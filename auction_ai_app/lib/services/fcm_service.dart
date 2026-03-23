import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'api_service.dart';

/// Firebase Cloud Messaging 서비스
class FCMService {
  static final FCMService _instance = FCMService._internal();
  factory FCMService() => _instance;
  FCMService._internal();

  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  final ApiService _apiService = ApiService();

  String? _fcmToken;
  String? get fcmToken => _fcmToken;

  /// FCM 초기화
  Future<void> initialize() async {
    try {
      // iOS 권한 요청
      NotificationSettings settings = await _messaging.requestPermission(
        alert: true,
        announcement: false,
        badge: true,
        carPlay: false,
        criticalAlert: false,
        provisional: false,
        sound: true,
      );

      if (settings.authorizationStatus == AuthorizationStatus.authorized) {
        debugPrint('✅ FCM: 알림 권한이 승인되었습니다');
      } else {
        debugPrint('⚠️ FCM: 알림 권한이 거부되었습니다');
        return;
      }

      // FCM 토큰 가져오기
      _fcmToken = await _messaging.getToken();
      if (_fcmToken != null) {
        debugPrint('✅ FCM Token: $_fcmToken');
        // 서버에 토큰 등록
        await registerToken(_fcmToken!);
      }

      // 토큰 갱신 리스너
      _messaging.onTokenRefresh.listen((newToken) {
        debugPrint('🔄 FCM Token 갱신: $newToken');
        _fcmToken = newToken;
        registerToken(newToken);
      });

      // 포그라운드 메시지 리스너
      FirebaseMessaging.onMessage.listen(_handleForegroundMessage);

      // 백그라운드에서 알림 탭하여 앱 열기
      FirebaseMessaging.onMessageOpenedApp.listen(_handleMessageOpenedApp);

      // 앱이 종료된 상태에서 알림 탭하여 앱 열기
      _messaging.getInitialMessage().then((message) {
        if (message != null) {
          _handleMessageOpenedApp(message);
        }
      });

      debugPrint('✅ FCM 초기화 완료');
    } catch (e) {
      debugPrint('❌ FCM 초기화 실패: $e');
    }
  }

  /// FCM 토큰을 서버에 등록
  Future<void> registerToken(String token) async {
    try {
      await _apiService.registerFCMToken(token);
      debugPrint('✅ FCM Token 서버 등록 완료');
    } catch (e) {
      debugPrint('❌ FCM Token 서버 등록 실패: $e');
    }
  }

  /// 포그라운드 메시지 처리
  void _handleForegroundMessage(RemoteMessage message) {
    debugPrint('📩 포그라운드 메시지 수신');
    debugPrint('  제목: ${message.notification?.title}');
    debugPrint('  내용: ${message.notification?.body}');
    debugPrint('  데이터: ${message.data}');

    // TODO: 인앱 알림 표시 (Fluttertoast 등 사용)
  }

  /// 백그라운드에서 알림 탭하여 앱 열기
  void _handleMessageOpenedApp(RemoteMessage message) {
    debugPrint('🔔 알림 탭으로 앱 열기');
    debugPrint('  제목: ${message.notification?.title}');
    debugPrint('  내용: ${message.notification?.body}');
    debugPrint('  데이터: ${message.data}');

    // TODO: 알림 데이터에 따라 특정 화면으로 이동
    // 예: case_no가 있으면 해당 경매 상세 화면으로 이동
  }

  /// FCM 토큰 삭제 (로그아웃 시)
  Future<void> deleteToken() async {
    try {
      await _messaging.deleteToken();
      _fcmToken = null;
      debugPrint('✅ FCM Token 삭제 완료');
    } catch (e) {
      debugPrint('❌ FCM Token 삭제 실패: $e');
    }
  }
}

/// 백그라운드 메시지 핸들러 (최상위 함수여야 함)
@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  debugPrint('📩 백그라운드 메시지 수신');
  debugPrint('  제목: ${message.notification?.title}');
  debugPrint('  내용: ${message.notification?.body}');
  debugPrint('  데이터: ${message.data}');
}
