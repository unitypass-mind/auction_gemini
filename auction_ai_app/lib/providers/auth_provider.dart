import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';
import '../models/models.dart';

class AuthProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();

  User? _user;
  bool _isAuthenticated = false;
  bool _isLoading = false;
  String? _error;

  User? get user => _user;
  bool get isAuthenticated => _isAuthenticated;
  bool get isLoading => _isLoading;
  String? get error => _error;

  AuthProvider(); // 생성자에서 아무것도 하지 않음

  /// 앱 시작 시 저장된 토큰 확인 (명시적으로 호출 필요)
  Future<void> checkAuthStatus() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('access_token');

      if (token != null) {
        try {
          // 토큰이 있으면 사용자 정보 가져오기
          final response = await _apiService.getMyInfo();
          if (response['success'] == true) {
            _user = User.fromJson(response['user']);
            _isAuthenticated = true;
            notifyListeners();
          }
        } catch (e) {
          // 토큰이 만료되었거나 잘못됨
          print('Token validation failed: $e');
          await logout();
        }
      }
    } catch (e) {
      print('Auth status check failed: $e');
      // SharedPreferences 오류 등 - 무시하고 계속 진행
    }
  }

  /// 로그인
  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiService.login(
        email: email,
        password: password,
      );

      if (response['success'] == true) {
        _user = User.fromJson(response['user']);
        _isAuthenticated = true;
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _error = response['message'] ?? '로그인에 실패했습니다';
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  /// 회원가입
  Future<bool> register(String email, String password, String name) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiService.register(
        email: email,
        password: password,
        name: name,
      );

      if (response['success'] == true) {
        _user = User.fromJson(response['user']);
        _isAuthenticated = true;
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _error = response['message'] ?? '회원가입에 실패했습니다';
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  /// 로그아웃
  Future<void> logout() async {
    await _apiService.logout();
    _user = null;
    _isAuthenticated = false;
    notifyListeners();
  }

  /// 에러 메시지 클리어
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
