/// API 서비스 클래스
/// FastAPI 백엔드와 통신하는 HTTP 클라이언트

import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  late Dio _dio;
  static const String baseUrl = 'http://49.50.131.190'; // NCP 프로덕션 서버

  // 개발 환경에서는 로컬 서버 사용
  // static const String baseUrl = 'http://localhost:8000';

  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));

    // 인터셉터 추가 (JWT 토큰 자동 추가)
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        // SharedPreferences에서 JWT 토큰 가져오기
        final prefs = await SharedPreferences.getInstance();
        final token = prefs.getString('access_token');

        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }

        return handler.next(options);
      },
      onError: (error, handler) async {
        // 401 Unauthorized 에러 처리 (토큰 만료)
        if (error.response?.statusCode == 401) {
          // 토큰 갱신 로직 또는 로그아웃 처리
          final prefs = await SharedPreferences.getInstance();
          await prefs.remove('access_token');
          await prefs.remove('refresh_token');
        }

        return handler.next(error);
      },
    ));
  }

  // ========================================
  // 경매 정보 조회 API
  // ========================================

  /// 경매 검색
  ///
  /// [query]: 검색어
  /// [region]: 지역
  /// [propertyType]: 물건종류
  /// [minPrice]: 최소가격
  /// [maxPrice]: 최대가격
  Future<Map<String, dynamic>> searchAuctions({
    String? query,
    String? region,
    String? propertyType,
    int? minPrice,
    int? maxPrice,
  }) async {
    try {
      final response = await _dio.get('/search', queryParameters: {
        if (query != null) 'query': query,
        if (region != null) 'region': region,
        if (propertyType != null) 'property_type': propertyType,
        if (minPrice != null) 'min_price': minPrice,
        if (maxPrice != null) 'max_price': maxPrice,
      });

      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  /// 사건번호로 경매 조회
  Future<Map<String, dynamic>> getAuctionByCaseNumber(String caseNumber) async {
    try {
      final response = await _dio.get('/case-number/$caseNumber');
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  /// 경매 상세 정보 조회
  Future<Map<String, dynamic>> getAuctionDetail(String caseNumber) async {
    try {
      final response = await _dio.get('/detail/$caseNumber');
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  /// AI 낙찰가 예측
  ///
  /// [startPrice]: 감정가
  /// [propertyType]: 물건종류
  /// [region]: 지역
  /// [area]: 면적
  /// [auctionRound]: 경매회차
  Future<Map<String, dynamic>> predictPrice({
    required int startPrice,
    String? propertyType,
    String? region,
    double? area,
    int auctionRound = 1,
  }) async {
    try {
      final response = await _dio.post('/predict/simple', data: {
        'start_price': startPrice,
        if (propertyType != null) 'property_type': propertyType,
        if (region != null) 'region': region,
        if (area != null) 'area': area,
        'auction_round': auctionRound,
      });

      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  // ========================================
  // 사용자 인증 API
  // ========================================

  /// 회원가입
  Future<Map<String, dynamic>> register({
    required String email,
    required String password,
    required String name,
  }) async {
    try {
      final response = await _dio.post('/auth/register', data: {
        'email': email,
        'password': password,
        'name': name,
      });

      // 토큰 저장
      if (response.data['success'] == true) {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('access_token', response.data['access_token']);
        await prefs.setString('refresh_token', response.data['refresh_token']);
      }

      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  /// 로그인
  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _dio.post('/auth/login', data: {
        'email': email,
        'password': password,
      });

      // 토큰 저장
      if (response.data['success'] == true) {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('access_token', response.data['access_token']);
        await prefs.setString('refresh_token', response.data['refresh_token']);
      }

      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  /// 로그아웃
  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
    await prefs.remove('refresh_token');
  }

  /// 내 정보 조회
  Future<Map<String, dynamic>> getMyInfo() async {
    try {
      final response = await _dio.get('/auth/me');
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  // ========================================
  // 푸시 알림 API
  // ========================================

  /// FCM 토큰 등록
  Future<Map<String, dynamic>> registerFcmToken(String fcmToken) async {
    try {
      final response = await _dio.post('/notifications/register-token', data: {
        'fcm_token': fcmToken,
      });

      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  /// 경매 알림 구독
  Future<Map<String, dynamic>> subscribeAuction({
    required String caseNumber,
    bool? priceDropAlert,
    bool? bidReminderAlert,
  }) async {
    try {
      final response = await _dio.post('/notifications/subscribe', data: {
        'case_number': caseNumber,
        if (priceDropAlert != null) 'price_drop_alert': priceDropAlert,
        if (bidReminderAlert != null) 'bid_reminder_alert': bidReminderAlert,
      });

      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  /// 내 구독 목록 조회
  Future<Map<String, dynamic>> getMySubscriptions() async {
    try {
      final response = await _dio.get('/notifications/subscriptions');
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  /// 구독 해제
  Future<Map<String, dynamic>> unsubscribe(int subscriptionId) async {
    try {
      final response = await _dio.delete('/notifications/unsubscribe/$subscriptionId');
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  // ========================================
  // 통계 API
  // ========================================

  /// 모델 정확도 조회
  Future<Map<String, dynamic>> getAccuracy() async {
    try {
      final response = await _dio.get('/accuracy');
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  /// 가격대별 통계
  Future<Map<String, dynamic>> getPriceRangeStats() async {
    try {
      final response = await _dio.get('/price-range-stats');
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  /// 지역별 통계
  Future<Map<String, dynamic>> getRegionalStats() async {
    try {
      final response = await _dio.get('/regional-stats');
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  // ========================================
  // 에러 처리
  // ========================================

  String _handleError(dynamic error) {
    if (error is DioException) {
      if (error.response != null) {
        // 서버 응답이 있는 경우
        final data = error.response!.data;
        if (data is Map && data.containsKey('detail')) {
          return data['detail'];
        }
        return '서버 오류: ${error.response!.statusCode}';
      } else {
        // 네트워크 오류
        return '네트워크 연결을 확인해주세요';
      }
    }
    return '알 수 없는 오류가 발생했습니다';
  }
}
