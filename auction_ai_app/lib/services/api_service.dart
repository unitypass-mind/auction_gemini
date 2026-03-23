/// API 서비스 클래스
/// FastAPI 백엔드와 통신하는 HTTP 클라이언트

import 'dart:io';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  late Dio _dio;
  // 프로덕션 환경: 도메인 사용
  static const String baseUrl = 'https://auction-ai.kr';

  // 에뮬레이터 테스트용: IP 주소 직접 사용
  // static const String baseUrl = 'https://49.50.131.190'; // NCP 서버 IP

  // 개발 환경에서는 로컬 서버 사용
  // static const String baseUrl = 'http://localhost:8000';

  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));

    // 인터셉터 추가 (JWT 토큰 자동 추가)
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        // 디버그 로깅
        print('=== API Request ===');
        print('URL: ${options.baseUrl}${options.path}');
        print('Method: ${options.method}');
        print('Query Parameters: ${options.queryParameters}');
        print('Headers: ${options.headers}');

        // SharedPreferences에서 JWT 토큰 가져오기
        final prefs = await SharedPreferences.getInstance();
        final token = prefs.getString('access_token');

        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }

        return handler.next(options);
      },
      onResponse: (response, handler) {
        // 응답 로깅
        print('=== API Response ===');
        print('Status Code: ${response.statusCode}');
        final dataStr = response.data?.toString() ?? '';
        print('Data: ${dataStr.length > 200 ? dataStr.substring(0, 200) + '...' : dataStr}');
        return handler.next(response);
      },
      onError: (error, handler) async {
        // 에러 로깅
        print('=== API Error ===');
        print('Error Type: ${error.type}');
        print('Error Message: ${error.message}');
        print('Status Code: ${error.response?.statusCode}');
        print('Response Data: ${error.response?.data}');
        print('Request URL: ${error.requestOptions.baseUrl}${error.requestOptions.path}');
        print('Request Method: ${error.requestOptions.method}');

        // DioException 타입별 상세 정보
        if (error.type == DioExceptionType.connectionTimeout) {
          print('Connection Timeout - Server took too long to respond');
        } else if (error.type == DioExceptionType.receiveTimeout) {
          print('Receive Timeout - Server is sending data too slowly');
        } else if (error.type == DioExceptionType.sendTimeout) {
          print('Send Timeout - Request took too long to send');
        } else if (error.type == DioExceptionType.badResponse) {
          print('Bad Response - Server returned an error');
        } else if (error.type == DioExceptionType.badCertificate) {
          print('Bad Certificate - SSL/TLS certificate error');
          print('Certificate error: ${error.error}');
        } else if (error.type == DioExceptionType.connectionError) {
          print('Connection Error - Cannot connect to server');
          print('Underlying error: ${error.error}');
        } else if (error.type == DioExceptionType.cancel) {
          print('Request Cancelled');
        } else if (error.type == DioExceptionType.unknown) {
          print('Unknown Error: ${error.error}');
        }

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
      final response = await _dio.get('/auctions/search', queryParameters: {
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
      final response = await _dio.get('/auction', queryParameters: {
        'case_no': caseNumber,
      });
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  /// 경매 상세 정보 조회
  Future<Map<String, dynamic>> getAuctionDetail(String caseNumber) async {
    try {
      final response = await _dio.get('/auction', queryParameters: {
        'case_no': caseNumber,
      });
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  /// 사건번호로 경매 물건 목록 조회
  ///
  /// 같은 사건번호에 여러 법원/물건이 있을 경우 모두 반환
  /// [caseNumber]: 경매 사건 번호 (예: 2024타경579705)
  Future<Map<String, dynamic>> listAuctionsByCaseNumber(String caseNumber) async {
    try {
      final response = await _dio.get('/auctions/list-by-case', queryParameters: {
        'case_no': caseNumber,
      });
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  /// 경매 전체 분석 (Full Analysis)
  ///
  /// 경매 물건에 대한 종합적인 분석을 제공합니다:
  /// - 경매 기본 정보
  /// - AI 낙찰가 예측
  /// - 수익 분석
  /// - 투자 매력도 점수
  /// - 입찰 전략 추천
  /// - 권리분석
  ///
  /// [caseNumber]: 경매 사건 번호 (예: 2024타경579705)
  /// [site]: 담당법원명 (중복 사건번호 구분용, 선택사항)
  Future<Map<String, dynamic>> fullAnalysis(String caseNumber, {String? site}) async {
    try {
      final response = await _dio.get('/auction', queryParameters: {
        'case_no': caseNumber,
        if (site != null) 'site': site,
      });
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
      final response = await _dio.post('/notifications/auction/subscribe', data: {
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
      final response = await _dio.delete('/notifications/auction/unsubscribe/$subscriptionId');
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
  // 푸시 알림 (FCM)
  // ========================================

  /// FCM 토큰 등록
  Future<Map<String, dynamic>> registerFCMToken(String token) async {
    try {
      // device_id는 FCM 토큰의 해시값 사용 (디바이스마다 고유)
      final deviceId = token.hashCode.toRadixString(36);

      final response = await _dio.post('/notifications/subscribe', data: {
        'fcm_token': token,
        'device_id': deviceId,
        'device_type': Platform.isAndroid ? 'android' : 'ios',
      });
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  // ========================================
  // 알림 설정 (마스터 스위치)
  // ========================================

  /// 알림 마스터 스위치 상태 조회
  Future<Map<String, dynamic>> getNotificationSettings() async {
    try {
      final response = await _dio.get('/notifications/settings');
      return response.data;
    } catch (e) {
      throw _handleError(e);
    }
  }

  /// 알림 마스터 스위치 ON/OFF
  Future<Map<String, dynamic>> updateNotificationSettings(bool enabled) async {
    try {
      final response = await _dio.post('/notifications/settings', queryParameters: {
        'enabled': enabled,
      });
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
        final statusCode = error.response!.statusCode;
        final data = error.response!.data;

        // 서버가 보낸 detail 메시지 우선 사용
        if (data is Map && data.containsKey('detail')) {
          final detail = data['detail'];

          // detail이 Map인 경우 (중첩된 응답)
          if (detail is Map) {
            // message 필드가 있으면 사용
            if (detail.containsKey('message') && detail['message'] is String) {
              return detail['message'];
            }
            // error 필드가 있으면 사용
            if (detail.containsKey('error') && detail['error'] is String) {
              return detail['error'];
            }
          }

          // detail이 String인 경우 직접 사용
          if (detail is String) {
            return detail;
          }
        }

        // HTTP 상태 코드별 사용자 친화적 메시지
        switch (statusCode) {
          case 400:
            return '입력하신 정보를 확인해주세요';
          case 401:
            return '로그인이 필요합니다\n다시 로그인해주세요';
          case 403:
            return '접근 권한이 없습니다';
          case 404:
            return '해당 사건번호를 찾을 수 없습니다\n사건번호를 다시 확인해주세요';
          case 422:
            return '입력값이 올바르지 않습니다';
          case 500:
            return '서버 오류가 발생했습니다\n잠시 후 다시 시도해주세요';
          case 503:
            return '서버가 일시적으로 사용 불가능합니다';
          default:
            return '오류가 발생했습니다 (코드: ${statusCode})';
        }
      } else {
        // 네트워크 오류 (서버 응답 없음)
        // 타입별로 더 상세한 메시지 제공
        switch (error.type) {
          case DioExceptionType.connectionTimeout:
            return '서버 연결 시간이 초과되었습니다\\n네트워크를 확인하고 다시 시도해주세요';
          case DioExceptionType.receiveTimeout:
            return '응답 대기 시간이 초과되었습니다\\n잠시 후 다시 시도해주세요';
          case DioExceptionType.sendTimeout:
            return '요청 전송 시간이 초과되었습니다\\n네트워크를 확인해주세요';
          case DioExceptionType.badCertificate:
            return 'SSL 인증서 오류가 발생했습니다\\n네트워크 설정을 확인해주세요';
          case DioExceptionType.connectionError:
            return '서버에 연결할 수 없습니다\\n네트워크 연결을 확인해주세요';
          default:
            return '네트워크 연결을 확인해주세요';
        }
      }
    }
    return '알 수 없는 오류가 발생했습니다';
  }
}
