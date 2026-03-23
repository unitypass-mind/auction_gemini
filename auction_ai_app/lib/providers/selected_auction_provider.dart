import 'package:flutter/foundation.dart';
import '../models/models.dart';

/// 선택된 경매 물건 정보를 관리하는 Provider
class SelectedAuctionProvider with ChangeNotifier {
  AuctionItem? _selectedItem;
  String? _selectedCaseNumber;

  // 구독 상태 관리 (사건번호별 구독 여부)
  final Map<String, bool> _subscriptionStates = {};

  AuctionItem? get selectedItem => _selectedItem;
  String? get selectedCaseNumber => _selectedCaseNumber;

  /// 물건 선택
  void selectItem(AuctionItem item) {
    _selectedItem = item;
    _selectedCaseNumber = null;
    notifyListeners();
  }

  /// 사건번호로 선택 (검색 기록/즐겨찾기에서 사용)
  void selectByCaseNumber(String caseNumber) {
    _selectedCaseNumber = caseNumber;
    _selectedItem = null;
    notifyListeners();
  }

  /// 선택 해제
  void clearSelection() {
    _selectedItem = null;
    _selectedCaseNumber = null;
    notifyListeners();
  }

  /// 구독 상태 설정
  void setSubscriptionState(String caseNumber, bool isSubscribed) {
    print('=== Provider: Setting subscription state ===');
    print('Case Number: $caseNumber');
    print('Is Subscribed: $isSubscribed');

    _subscriptionStates[caseNumber] = isSubscribed;
    notifyListeners();
  }

  /// 구독 상태 조회
  bool? getSubscriptionState(String caseNumber) {
    return _subscriptionStates[caseNumber];
  }

  /// 구독 상태 캐시 초기화 (로그아웃 등에 사용)
  void clearSubscriptionStates() {
    _subscriptionStates.clear();
    notifyListeners();
  }
}
