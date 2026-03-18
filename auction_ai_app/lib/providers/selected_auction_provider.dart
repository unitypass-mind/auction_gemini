import 'package:flutter/foundation.dart';
import '../models/models.dart';

/// 선택된 경매 물건 정보를 관리하는 Provider
class SelectedAuctionProvider with ChangeNotifier {
  AuctionItem? _selectedItem;

  AuctionItem? get selectedItem => _selectedItem;

  /// 물건 선택
  void selectItem(AuctionItem item) {
    _selectedItem = item;
    notifyListeners();
  }

  /// 선택 해제
  void clearSelection() {
    _selectedItem = null;
    notifyListeners();
  }
}
