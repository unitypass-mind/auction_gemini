import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import '../services/api_service.dart';
import '../models/models.dart';
import '../providers/selected_auction_provider.dart';
import '../providers/auth_provider.dart';
import 'auction_search_screen.dart';

class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();

  /// SearchScreen의 GlobalKey (다른 화면에서 직접 메서드 호출용)
  static final GlobalKey<_SearchScreenState> globalKey = GlobalKey<_SearchScreenState>();
}

class _SearchScreenState extends State<SearchScreen> with WidgetsBindingObserver {
  final ApiService _apiService = ApiService();
  final _caseNumberController = TextEditingController();
  final _searchQueryController = TextEditingController();

  FullAnalysisResult? _result;
  bool _isLoading = false;
  String? _error;
  bool _isFavorite = false;
  bool _isSubscribed = false; // 구독 상태
  String? _lastProcessedCaseNumber; // 중복 실행 방지용
  DateTime? _lastSubscriptionCheck; // 마지막 구독 상태 확인 시간

  String _selectedYear = DateTime.now().year.toString();
  final String _caseType = '타경'; // 고정

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    // 더 이상 Provider를 사용하지 않음 - performAutoSearch()로 직접 호출됨
  }

  @override
  void activate() {
    super.activate();

    // 화면이 다시 활성화될 때 구독 상태 재확인
    // Consumer가 Provider 상태를 자동으로 반영하므로 캐시 확인 불필요
    if (_result != null) {
      print('=== Screen activated, rechecking subscription status via API ===');
      _checkSubscriptionStatus(_result!.caseNumber);
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    super.didChangeAppLifecycleState(state);

    // 앱이 다시 foreground로 돌아올 때 구독 상태 재확인
    if (state == AppLifecycleState.resumed && _result != null) {
      print('=== App resumed, rechecking subscription status ===');
      _checkSubscriptionStatus(_result!.caseNumber);
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _caseNumberController.dispose();
    _searchQueryController.dispose();
    super.dispose();
  }

  /// 외부에서 사건번호로 자동 검색을 실행하는 public 메서드
  void performAutoSearch(String caseNumber) {
    print('=== performAutoSearch called with: $caseNumber ===');

    // 중복 실행 방지
    if (caseNumber == _lastProcessedCaseNumber) {
      print('Skipping: already processed this case number');
      return;
    }

    // 사건번호 파싱: 예) "2024타경579705" -> 년도: 2024, 번호: 579705
    final yearMatch = RegExp(r'^(\d{4})').firstMatch(caseNumber);
    final numberMatch = RegExp(r'타경(\d+)$').firstMatch(caseNumber);

    print('Year match: ${yearMatch?.group(1)}');
    print('Number match: ${numberMatch?.group(1)}');

    if (yearMatch != null && numberMatch != null) {
      final year = yearMatch.group(1)!;
      final number = numberMatch.group(1)!;

      print('Parsed successfully - Year: $year, Number: $number');

      // 중복 실행 방지 플래그 업데이트
      _lastProcessedCaseNumber = caseNumber;

      setState(() {
        _selectedYear = year;
        _caseNumberController.text = number;
      });

      print('State updated, executing analysis...');

      // 즉시 검색 실행
      WidgetsBinding.instance.addPostFrameCallback((_) {
        print('Calling _performAnalysis()...');
        _performAnalysis();
      });
    } else {
      print('ERROR: Failed to parse case number: $caseNumber');
    }
  }


  List<String> get _years {
    final currentYear = DateTime.now().year;
    return List.generate(6, (index) => (currentYear - index).toString());
  }

  Future<void> _performAnalysis() async {
    if (_caseNumberController.text.trim().isEmpty) {
      setState(() {
        _error = '사건번호를 입력해주세요';
      });
      return;
    }

    final caseNumber = '$_selectedYear$_caseType${_caseNumberController.text.trim()}';

    setState(() {
      _isLoading = true;
      _error = null;
      _result = null;
    });

    try {
      // 전체 분석 API 직접 호출
      await _performFullAnalysis(caseNumber);
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _performFullAnalysis(String caseNumber, {String? court}) async {
    setState(() {
      _isLoading = true;
      _error = null;
      _result = null;
    });

    try {
      final response = await _apiService.fullAnalysis(caseNumber, site: court);

      if (response['success'] == true) {
        final result = FullAnalysisResult.fromJson(response);

        setState(() {
          _result = result;
          _isLoading = false;
        });

        // 검색 성공 시 검색 기록 저장
        await _saveSearchHistory(caseNumber, result);

        // 즐겨찾기 상태 확인
        await _checkFavoriteStatus(caseNumber);

        // 구독 상태 확인
        await _checkSubscriptionStatus(caseNumber);
      } else {
        setState(() {
          _error = response['message'] ?? '분석에 실패했습니다';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _saveSearchHistory(String caseNumber, FullAnalysisResult result) async {
    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userId = authProvider.user?.id ?? 0;
      if (userId == 0) return; // 로그인하지 않은 경우 저장하지 않음

      final prefs = await SharedPreferences.getInstance();
      final historyJson = prefs.getStringList('search_history_$userId') ?? [];

      // 검색 기록 항목 생성
      final historyItem = {
        'case_number': caseNumber,
        'property_type': result.propertyType,
        'address': result.address,
        'timestamp': DateTime.now().toIso8601String(),
      };

      // 중복 제거 (같은 사건번호가 있으면 제거)
      historyJson.removeWhere((item) {
        try {
          final decoded = jsonDecode(item) as Map<String, dynamic>;
          return decoded['case_number'] == caseNumber;
        } catch (e) {
          return false;
        }
      });

      // 새 항목 추가 (맨 뒤에 추가, 최신순으로 표시)
      historyJson.add(jsonEncode(historyItem));

      // 최대 50개까지만 저장
      if (historyJson.length > 50) {
        historyJson.removeAt(0);
      }

      await prefs.setStringList('search_history_$userId', historyJson);
    } catch (e) {
      // 검색 기록 저장 실패는 무시 (사용자에게 표시하지 않음)
      print('Failed to save search history: $e');
    }
  }

  Future<void> _checkFavoriteStatus(String caseNumber) async {
    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userId = authProvider.user?.id ?? 0;
      if (userId == 0) {
        setState(() => _isFavorite = false);
        return;
      }

      final prefs = await SharedPreferences.getInstance();
      final favoritesJson = prefs.getStringList('favorites_$userId') ?? [];

      final isFavorite = favoritesJson.any((item) {
        try {
          final decoded = jsonDecode(item) as Map<String, dynamic>;
          return decoded['case_number'] == caseNumber;
        } catch (e) {
          return false;
        }
      });

      setState(() {
        _isFavorite = isFavorite;
      });
    } catch (e) {
      print('Failed to check favorite status: $e');
    }
  }

  Future<void> _checkSubscriptionStatus(String caseNumber) async {
    try {
      print('=== Checking subscription status for: $caseNumber ===');

      final response = await _apiService.getMySubscriptions();

      if (response['success'] == true) {
        final subscriptions = response['subscriptions'] as List<dynamic>? ?? [];
        final isSubscribed = subscriptions.any((sub) => sub['case_number'] == caseNumber);

        print('=== Subscription status: $isSubscribed ===');

        // Provider에 상태 저장 (다른 화면에서도 사용 가능)
        if (mounted) {
          final provider = Provider.of<SelectedAuctionProvider>(context, listen: false);
          provider.setSubscriptionState(caseNumber, isSubscribed);

          setState(() {
            _isSubscribed = isSubscribed;
          });
        }
      }
    } catch (e) {
      print('Failed to check subscription status: $e');
    }
  }

  Future<void> _showSubscriptionDialog() async {
    if (_result == null) return;

    // Provider에서 현재 구독 상태 확인
    final provider = Provider.of<SelectedAuctionProvider>(context, listen: false);
    final isCurrentlySubscribed = provider.getSubscriptionState(_result!.caseNumber) ?? _isSubscribed;

    // 기본값 설정
    bool priceDropAlert = true;
    bool bidReminderAlert = true;
    Map<String, dynamic>? currentSubscription;

    // 구독 중이라면 현재 설정 가져오기
    if (isCurrentlySubscribed) {
      try {
        final response = await _apiService.getMySubscriptions();
        if (response['success'] == true) {
          final subscriptions = response['subscriptions'] as List<dynamic>? ?? [];
          currentSubscription = subscriptions.firstWhere(
            (sub) => sub['case_number'] == _result!.caseNumber,
            orElse: () => null,
          );

          if (currentSubscription != null) {
            priceDropAlert = currentSubscription['price_drop_alert'] ?? true;
            bidReminderAlert = currentSubscription['bid_reminder_alert'] ?? true;
          }
        }
      } catch (e) {
        print('Failed to get current subscription settings: $e');
      }
    }

    final confirmed = await showDialog<String>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('알림 구독'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                _result!.caseNumber,
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(
                _result!.address,
                style: TextStyle(fontSize: 12, color: Colors.grey[600]),
              ),
              const SizedBox(height: 20),
              const Text(
                '받을 알림을 선택하세요:',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 12),
              CheckboxListTile(
                title: const Text('가격 하락 알림'),
                subtitle: const Text('유찰로 인한 가격 하락 시'),
                value: priceDropAlert,
                onChanged: (value) {
                  setState(() {
                    priceDropAlert = value ?? true;
                  });
                },
                controlAffinity: ListTileControlAffinity.leading,
                contentPadding: EdgeInsets.zero,
              ),
              CheckboxListTile(
                title: const Text('입찰 마감 알림'),
                subtitle: const Text('입찰 마감일 전일'),
                value: bidReminderAlert,
                onChanged: (value) {
                  setState(() {
                    bidReminderAlert = value ?? true;
                  });
                },
                controlAffinity: ListTileControlAffinity.leading,
                contentPadding: EdgeInsets.zero,
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('취소'),
            ),
            if (isCurrentlySubscribed) ...[
              // 이미 구독 중인 경우: "저장"과 "해제" 버튼 둘 다 표시
              ElevatedButton(
                onPressed: () => Navigator.pop(context, 'save'),
                child: const Text('저장'),
              ),
              const SizedBox(width: 8),
              ElevatedButton(
                onPressed: () => Navigator.pop(context, 'unsubscribe'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                  foregroundColor: Colors.white,
                ),
                child: const Text('해제'),
              ),
            ] else ...[
              // 신규 구독: "구독" 버튼만 표시
              ElevatedButton(
                onPressed: () => Navigator.pop(context, 'subscribe'),
                child: const Text('구독'),
              ),
            ],
          ],
        ),
      ),
    );

    if (confirmed == 'unsubscribe') {
      // 구독 해제
      if (currentSubscription != null) {
        final subscriptionId = currentSubscription['id'] as int;
        try {
          final unsubscribeResponse = await _apiService.unsubscribe(subscriptionId);

          if (unsubscribeResponse['success'] == true) {
            // Provider에 상태 저장 (즉시 반영)
            provider.setSubscriptionState(_result!.caseNumber, false);

            setState(() {
              _isSubscribed = false;
            });

            if (mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('구독이 해제되었습니다')),
              );
            }
          }
        } catch (e) {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('구독 해제 실패: ${e.toString()}')),
            );
          }
        }
      }
    } else if (confirmed == 'save' || confirmed == 'subscribe') {
      // 구독 추가 또는 설정 업데이트
      await _subscribeAuction(
        priceDropAlert: priceDropAlert,
        bidReminderAlert: bidReminderAlert,
      );
    }
  }

  Future<void> _subscribeAuction({
    required bool priceDropAlert,
    required bool bidReminderAlert,
  }) async {
    if (_result == null) return;

    try {
      print('=== Subscribing to auction ===');
      print('Case Number: ${_result!.caseNumber}');

      final response = await _apiService.subscribeAuction(
        caseNumber: _result!.caseNumber,
        priceDropAlert: priceDropAlert,
        bidReminderAlert: bidReminderAlert,
      );

      print('=== Subscription Response ===');
      print('Response: $response');

      if (response['success'] == true) {
        // Provider에 상태 저장 (즉시 반영)
        final provider = Provider.of<SelectedAuctionProvider>(context, listen: false);
        provider.setSubscriptionState(_result!.caseNumber, true);

        setState(() {
          _isSubscribed = true;
        });

        if (mounted) {
          // 서버의 action 값에 따라 다른 메시지 표시
          final action = response['action'] as String?;
          final message = action == 'updated'
              ? '알림 설정이 저장되었습니다'
              : '알림 구독이 완료되었습니다';

          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(message),
              backgroundColor: Colors.green,
            ),
          );
        }
      } else {
        // 서버가 success: false를 반환한 경우
        final message = response['message'] ?? '구독에 실패했습니다';
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(message)),
          );
        }
      }
    } catch (e) {
      print('=== Subscription Error ===');
      print('Error: $e');
      print('Error type: ${e.runtimeType}');

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('구독 실패: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _unsubscribeAuction() async {
    if (_result == null) return;

    // 구독 ID 찾기
    try {
      final response = await _apiService.getMySubscriptions();

      if (response['success'] == true) {
        final subscriptions = response['subscriptions'] as List<dynamic>? ?? [];
        final subscription = subscriptions.firstWhere(
          (sub) => sub['case_number'] == _result!.caseNumber,
          orElse: () => null,
        );

        if (subscription != null) {
          final subscriptionId = subscription['id'] as int;

          final unsubscribeResponse = await _apiService.unsubscribe(subscriptionId);

          if (unsubscribeResponse['success'] == true) {
            // Provider에 상태 저장 (즉시 반영)
            final provider = Provider.of<SelectedAuctionProvider>(context, listen: false);
            provider.setSubscriptionState(_result!.caseNumber, false);

            setState(() {
              _isSubscribed = false;
            });

            if (mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('구독이 해제되었습니다')),
              );
            }
          }
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('구독 해제 실패: ${e.toString()}')),
        );
      }
    }
  }

  Future<void> _showAuctionSearchDialog() async {
    // 새로운 경매 검색 화면으로 이동
    final String? selectedCaseNo = await Navigator.push<String>(
      context,
      MaterialPageRoute(
        builder: (context) => const AuctionSearchScreen(),
      ),
    );

    // 사용자가 경매 물건을 선택한 경우
    if (selectedCaseNo != null && mounted) {
      // Parse case number: "2024타경579705" -> year: "2024", number: "579705"
      final yearMatch = RegExp(r'^(\d{4})').firstMatch(selectedCaseNo);
      final numberMatch = RegExp(r'타경(\d+)$').firstMatch(selectedCaseNo);

      if (yearMatch != null && numberMatch != null) {
        setState(() {
          _selectedYear = yearMatch.group(1)!;
          _caseNumberController.text = numberMatch.group(1)!;
        });
      }
    }
  }

  Future<void> _toggleFavorite() async {
    if (_result == null) return;

    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final userId = authProvider.user?.id ?? 0;
      if (userId == 0) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('로그인이 필요합니다')),
          );
        }
        return;
      }

      final prefs = await SharedPreferences.getInstance();
      final favoritesJson = prefs.getStringList('favorites_$userId') ?? [];

      if (_isFavorite) {
        // 즐겨찾기 삭제
        favoritesJson.removeWhere((item) {
          try {
            final decoded = jsonDecode(item) as Map<String, dynamic>;
            return decoded['case_number'] == _result!.caseNumber;
          } catch (e) {
            return false;
          }
        });

        await prefs.setStringList('favorites_$userId', favoritesJson);

        setState(() {
          _isFavorite = false;
        });

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('즐겨찾기에서 삭제되었습니다')),
          );
        }
      } else {
        // 즐겨찾기 추가
        final favoriteItem = {
          'case_number': _result!.caseNumber,
          'property_type': _result!.propertyType,
          'address': _result!.address,
          'start_price': _result!.startPrice,
          'predicted_price': _result!.predictedPrice,
          'timestamp': DateTime.now().toIso8601String(),
        };

        favoritesJson.add(jsonEncode(favoriteItem));

        // 최대 100개까지만 저장
        if (favoritesJson.length > 100) {
          favoritesJson.removeAt(0);
        }

        await prefs.setStringList('favorites_$userId', favoritesJson);

        setState(() {
          _isFavorite = true;
        });

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('즐겨찾기에 추가되었습니다')),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('오류: ${e.toString()}')),
        );
      }
    }
  }

  Future<Map<String, dynamic>?> _showItemSelectionDialog(List<dynamic> items) async {
    return showDialog<Map<String, dynamic>>(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('물건 선택'),
          content: SizedBox(
            width: double.maxFinite,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  '같은 사건번호에 여러 물건이 있습니다.\n분석할 물건을 선택해주세요.',
                  style: TextStyle(fontSize: 14),
                ),
                const SizedBox(height: 16),
                Flexible(
                  child: ListView.builder(
                    shrinkWrap: true,
                    itemCount: items.length,
                    itemBuilder: (context, index) {
                      final item = items[index] as Map<String, dynamic>;
                      return Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        child: ListTile(
                          title: Text(
                            item['address'] ?? '주소 정보 없음',
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const SizedBox(height: 4),
                              Text('법원: ${item['court'] ?? '-'}'),
                              Text('물건종류: ${item['property_type'] ?? '-'}'),
                              if (item['appraisal_price'] != null)
                                Text('감정가: ${(item['appraisal_price'] / 10000).toStringAsFixed(0)}만원'),
                              if (item['area'] != null)
                                Text('면적: ${item['area']}㎡'),
                            ],
                          ),
                          trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                          onTap: () {
                            Navigator.of(context).pop(item);
                          },
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('취소'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('전체 분석'),
        actions: _result != null
            ? [
                // 구독 버튼 (Consumer로 자동 업데이트)
                Consumer<SelectedAuctionProvider>(
                  builder: (context, provider, child) {
                    // Provider에서 구독 상태 가져오기 (없으면 로컬 상태 사용)
                    final isSubscribed = provider.getSubscriptionState(_result?.caseNumber ?? '') ?? _isSubscribed;

                    return IconButton(
                      icon: Icon(
                        isSubscribed ? Icons.notifications_active : Icons.notifications_none,
                      ),
                      onPressed: _showSubscriptionDialog,
                      tooltip: isSubscribed ? '구독 설정' : '알림 구독',
                    );
                  },
                ),
              ]
            : null,
      ),
      floatingActionButton: _result != null
          ? FloatingActionButton(
              onPressed: _toggleFavorite,
              tooltip: _isFavorite ? '즐겨찾기 삭제' : '즐겨찾기 추가',
              child: Icon(
                _isFavorite ? Icons.favorite : Icons.favorite_border,
              ),
            )
          : null,
      body: Column(
        children: [
          // 검색 입력부
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.grey.withOpacity(0.1),
                  blurRadius: 4,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Column(
              children: [
                // 경매 물건 찾기 버튼 (새로 추가)
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: _showAuctionSearchDialog,
                    icon: const Icon(Icons.list_alt),
                    label: const Text(
                      '경매 물건 찾기',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      side: BorderSide(
                        color: Colors.blue[700]!,
                        width: 1.5,
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // 사건번호 입력
                Row(
                  children: [
                    // 년도 선택
                    SizedBox(
                      width: 90,
                      child: DropdownButtonFormField<String>(
                        value: _selectedYear,
                        decoration: InputDecoration(
                          labelText: '년도',
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 8,
                          ),
                        ),
                        items: _years
                            .map((year) => DropdownMenuItem(
                                  value: year,
                                  child: Text(year,
                                      style: const TextStyle(fontSize: 14)),
                                ))
                            .toList(),
                        onChanged: (value) {
                          setState(() {
                            _selectedYear = value!;
                          });
                        },
                      ),
                    ),
                    const SizedBox(width: 6),

                    // 사건 유형 (고정: 타경)
                    SizedBox(
                      width: 80,
                      child: TextFormField(
                        initialValue: '타경',
                        enabled: false,
                        decoration: InputDecoration(
                          labelText: '유형',
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 6,
                            vertical: 8,
                          ),
                          disabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: const BorderSide(color: Colors.grey),
                          ),
                        ),
                        style: const TextStyle(
                          fontSize: 14,
                          color: Colors.black87,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    const SizedBox(width: 6),

                    // 번호 입력
                    Expanded(
                      child: TextField(
                        controller: _caseNumberController,
                        decoration: InputDecoration(
                          labelText: '번호',
                          hintText: '579705',
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 16,
                          ),
                        ),
                        keyboardType: TextInputType.number,
                        onSubmitted: (_) => _performAnalysis(),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),

                // 검색 버튼
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _performAnalysis,
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: _isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Text(
                            '전체 분석',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                  ),
                ),
              ],
            ),
          ),

          // 분석 결과
          Expanded(
            child: _buildAnalysisResult(),
          ),
        ],
      ),
    );
  }

  Widget _buildAnalysisResult() {
    if (_isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const CircularProgressIndicator(),
            const SizedBox(height: 24),
            Text(
              'AI가 경매 데이터를 분석하고 있습니다...',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[700],
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '잠시만 기다려주세요',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[500],
              ),
            ),
          ],
        ),
      );
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 64, color: Colors.red[300]),
            const SizedBox(height: 16),
            Text(
              _error!,
              style: TextStyle(color: Colors.grey[600]),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _performAnalysis,
              child: const Text('다시 시도'),
            ),
          ],
        ),
      );
    }

    if (_result == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.analytics, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(
              '사건번호를 입력하고 전체 분석 버튼을 눌러주세요',
              style: TextStyle(color: Colors.grey[600]),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              '예: 2024 + 타경 + 579705',
              style: TextStyle(color: Colors.grey[500], fontSize: 12),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 경매 기본 정보
          _buildAuctionInfoCard(),
          const SizedBox(height: 16),

          // AI 예측 및 수익 분석
          _buildPredictionCard(),
          const SizedBox(height: 16),

          // 입찰 전략
          _buildBiddingStrategyCard(),
          const SizedBox(height: 16),

          // 가격 비교 분석
          _buildPriceComparisonCard(),
          const SizedBox(height: 16),

          // 투자 매력도
          _buildInvestmentScoreCard(),
          const SizedBox(height: 16),

          // 10가지 고급 기능 카드들
          if (_result!.competitionLevel != null) ...[
            _buildCompetitionCard(),
            const SizedBox(height: 16),
          ],

          if (_result!.similarProperties != null && _result!.similarProperties!.isNotEmpty) ...[
            _buildSimilarPropertiesCard(),
            const SizedBox(height: 16),
          ],

          if (_result!.riskScore != null) ...[
            _buildRiskAnalysisCard(),
            const SizedBox(height: 16),
          ],

          if (_result!.bidSimulations != null && _result!.bidSimulations!.isNotEmpty) ...[
            _buildBidSimulatorCard(),
            const SizedBox(height: 16),
          ],

          // 권리분석
          if (_result!.auctionInfo['권리분석'] != null) ...[
            _buildRightsAnalysisCard(),
            const SizedBox(height: 16),
          ],

          if (_result!.expertTips != null && _result!.expertTips!.isNotEmpty) ...[
            _buildExpertTipsCard(),
            const SizedBox(height: 16),
          ],

          if (_result!.confidenceScore != null) ...[
            _buildConfidenceCard(),
          ],
        ],
      ),
    );
  }

  Widget _buildAuctionInfoCard() {
    final result = _result!;
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.blue[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.gavel, color: Colors.blue[700]),
                ),
                const SizedBox(width: 12),
                const Text(
                  '경매 기본 정보',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const Divider(height: 24),
            _buildInfoRow('사건번호', result.caseNumber),
            _buildInfoRow('물건종류', result.propertyType),
            _buildInfoRow('소재지', result.address),
            _buildInfoRow('면적', result.formattedArea),
            _buildInfoRow('감정가', result.formattedStartPrice),
            _buildInfoRow('경매회차', '${result.auctionRound}회차'),
            if (result.formattedCourt.isNotEmpty)
              _buildInfoRow('법원', result.formattedCourt),
            if (result.biddingDate.isNotEmpty)
              _buildInfoRow(
                '경매정보',
                '${result.formattedBiddingDate} ${_calculateDaysUntilAuction(result.biddingDate)}'
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: TextStyle(
                color: Colors.grey[700],
                fontSize: 14,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _calculateDaysUntilAuction(String auctionDateStr) {
    try {
      // 날짜 문자열 파싱 (예: "20260316", "2024-12-15" 또는 "2024년 12월 15일")
      DateTime auctionDate;

      if (auctionDateStr.length == 8 && int.tryParse(auctionDateStr) != null) {
        // "20260316" 형식 (YYYYMMDD)
        final year = int.parse(auctionDateStr.substring(0, 4));
        final month = int.parse(auctionDateStr.substring(4, 6));
        final day = int.parse(auctionDateStr.substring(6, 8));
        auctionDate = DateTime(year, month, day);
      } else if (auctionDateStr.contains('년')) {
        // "2024년 12월 15일" 형식
        final parts = auctionDateStr.replaceAll('년', '-').replaceAll('월', '-').replaceAll('일', '').trim().split('-');
        if (parts.length >= 3) {
          auctionDate = DateTime(
            int.parse(parts[0].trim()),
            int.parse(parts[1].trim()),
            int.parse(parts[2].trim()),
          );
        } else {
          return '-';
        }
      } else {
        // "2024-12-15" 형식
        auctionDate = DateTime.parse(auctionDateStr);
      }

      final now = DateTime.now();
      final today = DateTime(now.year, now.month, now.day);
      final targetDate = DateTime(auctionDate.year, auctionDate.month, auctionDate.day);
      final difference = targetDate.difference(today).inDays;

      if (difference < 0) {
        return '입찰 마감 (${-difference}일 경과)';
      } else if (difference == 0) {
        return '오늘 마감';
      } else if (difference == 1) {
        return '입찰 1일 전';
      } else {
        return '입찰 ${difference}일 전';
      }
    } catch (e) {
      return '-';
    }
  }

  Widget _buildPredictionCard() {
    final result = _result!;
    final profit = result.profitAnalysis;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.purple[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.psychology, color: Colors.purple[700]),
                ),
                const SizedBox(width: 12),
                const Text(
                  'AI 낙찰가 예측',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // 예측 낙찰가
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [Colors.purple[400]!, Colors.purple[600]!],
                ),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                children: [
                  const Text(
                    '예상 낙찰가',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    result.predictedPriceFormatted,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // 수익 정보
            Row(
              children: [
                Expanded(
                  child: _buildMetricCard(
                    '예상 수익',
                    profit.formattedExpectedProfit,
                    Icons.trending_up,
                    Colors.green,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildMetricCard(
                    '수익률',
                    profit.formattedProfitRate,
                    Icons.percent,
                    Colors.orange,
                  ),
                ),
              ],
            ),

            // AI 신뢰도
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey[100],
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(Icons.verified, color: Colors.blue[700], size: 20),
                  const SizedBox(width: 8),
                  Text(
                    'AI 신뢰도: ${result.advancedAnalysis.aiConfidence.score}점',
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const Spacer(),
                  Row(
                    children: List.generate(
                      5,
                      (index) => Icon(
                        index < result.advancedAnalysis.aiConfidence.stars
                            ? Icons.star
                            : Icons.star_border,
                        color: Colors.amber,
                        size: 18,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // 실거래가 경고
            if (result.realTransactionWarning.isNotEmpty) ...{
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.orange[50],
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.orange[300]!),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.warning_amber, color: Colors.orange[700], size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        result.realTransactionWarning,
                        style: TextStyle(
                          color: Colors.orange[900],
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            },
          ],
        ),
      ),
    );
  }

  Widget _buildMetricCard(String label, String value, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(
              color: Colors.grey[700],
              fontSize: 12,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(
              color: color,
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPriceComparisonCard() {
    final result = _result!;
    final strategy = result.advancedAnalysis.biddingStrategy;

    // 가격 데이터
    final appraisalPrice = result.startPrice; // 감정가
    final aiPrice = result.predictedPrice; // AI 예측가
    final minBidPrice = strategy.currentMinimum; // 현재 최저입찰가
    final marketPrice = result.startPrice; // 시세 (감정가와 동일하게 처리)

    final maxPrice = [appraisalPrice, aiPrice, minBidPrice, marketPrice].reduce((a, b) => a > b ? a : b);

    // 퍼센티지 계산
    final appraisalPercent = 1.0;
    final aiPercent = aiPrice / maxPrice;
    final minBidPercent = minBidPrice / maxPrice;
    final marketPercent = marketPrice / maxPrice;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.indigo[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.bar_chart, color: Colors.indigo[700]),
                ),
                const SizedBox(width: 12),
                const Text(
                  '가격 비교 분석',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const Divider(height: 24),

            // 감정가
            _buildPriceBar(
              '감정가',
              result.formattedStartPrice,
              appraisalPercent,
              Colors.purple,
              '100%',
            ),
            const SizedBox(height: 12),

            // AI 예측가
            _buildPriceBar(
              'AI 예측가',
              result.predictedPriceFormatted,
              aiPercent,
              Colors.blue,
              '${(aiPercent * 100).toStringAsFixed(1)}%',
            ),
            const SizedBox(height: 12),

            // 최저입찰가
            _buildPriceBar(
              '최저입찰가 (${result.auctionRound}회차)',
              strategy.formattedCurrentMinimum,
              minBidPercent,
              Colors.red,
              '${(minBidPercent * 100).toStringAsFixed(1)}%',
            ),
            const SizedBox(height: 12),

            // 시세
            _buildPriceBar(
              '시세',
              result.formattedStartPrice,
              marketPercent,
              Colors.green,
              '${(marketPercent * 100).toStringAsFixed(1)}%',
            ),

            const SizedBox(height: 20),
            const Divider(),
            const SizedBox(height: 12),

            // 경매 진행 히스토리
            Row(
              children: [
                Icon(Icons.timeline, color: Colors.grey[700], size: 20),
                const SizedBox(width: 8),
                Text(
                  '경매 진행 히스토리',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Colors.grey[800],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // 타임라인
            Row(
              children: [
                // 1회
                Expanded(
                  child: _buildTimelineItem(
                    '1회',
                    '100.0%',
                    result.formattedStartPrice,
                    '현재',
                    Colors.grey,
                    isFirst: true,
                  ),
                ),

                // 연결선
                Expanded(
                  child: Container(
                    height: 2,
                    color: result.auctionRound >= 2 ? Colors.grey[300] : Colors.transparent,
                  ),
                ),

                // 2회 (또는 현재 회차)
                Expanded(
                  child: _buildTimelineItem(
                    '${result.auctionRound}회',
                    '${(minBidPercent * 100).toStringAsFixed(1)}%',
                    strategy.formattedCurrentMinimum,
                    '현재',
                    Colors.blue,
                    isCurrent: true,
                  ),
                ),

                // 연결선
                Expanded(
                  child: Container(
                    height: 2,
                    color: Colors.amber[300],
                  ),
                ),

                // AI 예상
                Expanded(
                  child: _buildTimelineItem(
                    'AI',
                    '${(aiPercent * 100).toStringAsFixed(1)}%',
                    result.predictedPriceFormatted,
                    '예상',
                    Colors.amber,
                    isLast: true,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPriceBar(String label, String value, double percent, Color color, String percentText) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
            Text(
              '$value ($percentText)',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: percent,
            backgroundColor: Colors.grey[200],
            valueColor: AlwaysStoppedAnimation<Color>(color),
            minHeight: 24,
          ),
        ),
      ],
    );
  }

  Widget _buildTimelineItem(
    String round,
    String percent,
    String amount,
    String status,
    Color color,
    {bool isFirst = false, bool isCurrent = false, bool isLast = false}
  ) {
    return Column(
      children: [
        // 원형 인디케이터
        Container(
          width: 50,
          height: 50,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
            boxShadow: isCurrent
                ? [
                    BoxShadow(
                      color: color.withOpacity(0.5),
                      blurRadius: 8,
                      spreadRadius: 2,
                    ),
                  ]
                : null,
          ),
          child: Center(
            child: Text(
              round,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
        const SizedBox(height: 8),

        // 퍼센티지
        Text(
          percent,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),

        // 금액 (억 단위로 표시)
        Text(
          _formatToEok(amount),
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            color: Colors.grey[800],
          ),
          textAlign: TextAlign.center,
        ),

        const SizedBox(height: 4),

        // 상태
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
          decoration: BoxDecoration(
            color: color.withOpacity(0.2),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Text(
            status,
            style: TextStyle(
              fontSize: 10,
              color: color,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildInvestmentScoreCard() {
    final score = _result!.advancedAnalysis.investmentScore;

    Color scoreColor;
    switch (score.color) {
      case 'excellent':
        scoreColor = Colors.green;
        break;
      case 'good':
        scoreColor = Colors.blue;
        break;
      case 'normal':
        scoreColor = Colors.orange;
        break;
      case 'low':
        scoreColor = Colors.deepOrange;
        break;
      default:
        scoreColor = Colors.red;
    }

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: scoreColor.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.star, color: scoreColor),
                ),
                const SizedBox(width: 12),
                const Text(
                  '투자 매력도',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // 총점
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [scoreColor.withOpacity(0.6), scoreColor],
                ),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        '총점',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 14,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        score.formattedScore,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.3),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      score.level,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // 세부 점수
            ...score.details.map((detail) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            detail.category,
                            style: const TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          Text(
                            '${detail.score}/${detail.maxScore}점',
                            style: TextStyle(
                              fontSize: 14,
                              color: scoreColor,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      LinearProgressIndicator(
                        value: detail.score / detail.maxScore,
                        backgroundColor: Colors.grey[200],
                        color: scoreColor,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${detail.level} - ${detail.description}',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                  ),
                )),
          ],
        ),
      ),
    );
  }

  Widget _buildBiddingStrategyCard() {
    final strategy = _result!.advancedAnalysis.biddingStrategy;

    Color recommendationColor;
    IconData recommendationIcon;
    String recommendationText;

    switch (strategy.recommendation) {
      case 'bid_now':
        recommendationColor = Colors.green;
        recommendationIcon = Icons.check_circle;
        recommendationText = '입찰 권장';
        break;
      case 'wait_for_next':
        recommendationColor = Colors.orange;
        recommendationIcon = Icons.schedule;
        recommendationText = '유찰 대기 권장';
        break;
      case 'cannot_bid':
        recommendationColor = Colors.red;
        recommendationIcon = Icons.cancel;
        recommendationText = '입찰 불가';
        break;
      case 'completed':
        recommendationColor = Colors.blue;
        recommendationIcon = Icons.gavel;
        recommendationText = '입찰 불가';
        break;
      default:
        recommendationColor = Colors.grey;
        recommendationIcon = Icons.help;
        recommendationText = '분석 중';
    }

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: recommendationColor.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.lightbulb, color: recommendationColor),
                ),
                const SizedBox(width: 12),
                const Text(
                  '입찰 전략',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // 추천 사항
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: recommendationColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: recommendationColor),
              ),
              child: Row(
                children: [
                  Icon(recommendationIcon, color: recommendationColor, size: 32),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          recommendationText,
                          style: TextStyle(
                            color: recommendationColor,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          strategy.message,
                          style: TextStyle(
                            color: Colors.grey[700],
                            fontSize: 13,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // 상세 정보
            _buildInfoRow('현재 회차', '${strategy.currentRound}회차'),
            _buildInfoRow('현재 최저입찰가', strategy.formattedCurrentMinimum),
            _buildInfoRow('AI 예측가', strategy.formattedPredictedPrice),
            if (strategy.recommendation == 'completed' && strategy.actualSellingPrice != null) ...{
              _buildInfoRow('실제 낙찰가', strategy.formattedActualSellingPrice ?? '정보 없음'),
            },
            if (strategy.waitUntilRound != null) ...{
              _buildInfoRow('대기 권장 회차', '${strategy.waitUntilRound}회차'),
              _buildInfoRow('예상 절감액', strategy.formattedPotentialSavings),
            },
          ],
        ),
      ),
    );
  }

  Widget _buildRightsAnalysisCard() {
    final rightsInfo = _result!.auctionInfo['권리분석'] as Map<String, dynamic>;

    // 청구금액 비율에 따른 위험도 색상
    double claimRatio = rightsInfo['청구금액비율'] ?? 0.0;
    Color riskColor;
    String riskLevel;

    if (claimRatio >= 0.7) {
      riskColor = Colors.red;
      riskLevel = '높음';
    } else if (claimRatio >= 0.5) {
      riskColor = Colors.orange;
      riskLevel = '보통';
    } else if (claimRatio >= 0.3) {
      riskColor = Colors.amber;
      riskLevel = '낮음';
    } else {
      riskColor = Colors.green;
      riskLevel = '안전';
    }

    // 권리분석 태그 파싱
    List<String> tags = [];
    if (rightsInfo.containsKey('권리분석_원문') &&
        rightsInfo['권리분석_원문'] != null &&
        rightsInfo['권리분석_원문'].toString().isNotEmpty) {
      tags = rightsInfo['권리분석_원문']
          .toString()
          .split('/')
          .map((e) => e.trim())
          .where((e) => e.isNotEmpty)
          .toList();
    }

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.red[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.warning, color: Colors.red[700]),
                ),
                const SizedBox(width: 12),
                const Text(
                  '권리분석',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const Divider(height: 24),

            // 권리분석 태그들
            if (tags.isNotEmpty) ...{
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: tags.map((tag) => _buildRightsTag(tag)).toList(),
              ),
              const SizedBox(height: 16),
            },

            // 주요 지표 (간략하게 표시)
            Row(
              children: [
                if (rightsInfo['청구금액'] != null)
                  Expanded(
                    child: _buildCompactInfo(
                      '청구금액',
                      '${(rightsInfo['청구금액'] / 10000).toStringAsFixed(0)}만원',
                      Icons.account_balance_wallet,
                    ),
                  ),
                if (rightsInfo['청구금액비율'] != null) ...{
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildCompactInfo(
                      '청구금액 비율',
                      '${(claimRatio * 100).toStringAsFixed(1)}% ($riskLevel)',
                      Icons.pie_chart,
                      color: riskColor,
                    ),
                  ),
                },
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRightsTag(String tag) {
    // 태그별 색상 결정
    Color tagColor;
    Color bgColor;

    // ValueAuction 긍정적 태그 (초록색)
    if (tag.contains('안전한 물건') ||
        tag.contains('모든 권리 소멸') ||
        tag.contains('권리소멸') ||
        tag.contains('임차인 없음') ||
        tag.contains('로얄층') ||
        tag.contains('대단지') ||
        tag.contains('감정평가 1년 이상') ||
        tag.contains('안전한물건') ||
        tag.contains('시세대비') && tag.contains('이하')) {
      // 긍정적 태그 (초록색)
      tagColor = Colors.green[700]!;
      bgColor = Colors.green[50]!;
    } else if (tag.contains('중복사건') ||
        tag.contains('대항력포기') ||
        tag.contains('경매취하') ||
        tag.contains('유찰') && tag.contains('회')) {
      // 부정적/위험 태그 (빨간색)
      tagColor = Colors.red[700]!;
      bgColor = Colors.red[50]!;
    } else if (tag.contains('대항력있는임차인') ||
        tag.contains('임차인') ||
        tag.contains('근저당') ||
        tag.contains('유치권')) {
      // 주의 태그 (주황색)
      tagColor = Colors.orange[700]!;
      bgColor = Colors.orange[50]!;
    } else if (tag.contains('HUG') ||
        tag.contains('LH') ||
        tag.contains('공공임대')) {
      // HUG/공공 태그 (보라색)
      tagColor = Colors.purple[700]!;
      bgColor = Colors.purple[50]!;
    } else if (tag.contains('지하철') ||
        tag.contains('역세권') ||
        tag.contains('신설 예정') ||
        tag.contains('재개발') ||
        tag.contains('재건축')) {
      // 정보성/긍정 태그 (파란색)
      tagColor = Colors.blue[700]!;
      bgColor = Colors.blue[50]!;
    } else {
      // 기본 태그 (회색)
      tagColor = Colors.grey[700]!;
      bgColor = Colors.grey[100]!;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: tagColor.withOpacity(0.3)),
      ),
      child: Text(
        tag,
        style: TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.w600,
          color: tagColor,
        ),
      ),
    );
  }

  Widget _buildCompactInfo(String label, String value, IconData icon, {Color? color}) {
    final displayColor = color ?? Colors.grey[700]!;

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: displayColor.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 16, color: displayColor),
              const SizedBox(width: 4),
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(
                    fontSize: 11,
                    color: Colors.grey[600],
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.bold,
              color: displayColor,
            ),
          ),
        ],
      ),
    );
  }

  // 금액을 억 단위로 변환하는 헬퍼 함수
  String _formatToEok(String amountStr) {
    try {
      // "896,000,000원" -> "896000000" -> 896000000
      String numberStr = amountStr.replaceAll(RegExp(r'[,원]'), '');
      int amount = int.parse(numberStr);

      // 1억 미만일 경우 만 단위로 표시
      if (amount < 100000000) {
        double man = amount / 10000;
        if (man >= 1000) {
          return '${(man / 1000).toStringAsFixed(1)}천만';
        }
        return '${man.toStringAsFixed(0)}만';
      }

      // 1억 이상일 경우 억 단위로 표시
      double eok = amount / 100000000;
      return '${eok.toStringAsFixed(2)}억';
    } catch (e) {
      return amountStr; // 파싱 실패 시 원본 반환
    }
  }

  // ============================================
  // 10가지 고급 기능 카드 빌더 메서드들
  // ============================================

  // 2. 예측 신뢰도 카드
  Widget _buildConfidenceCard() {
    final result = _result!;
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.green[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.verified, color: Colors.green[700]),
                ),
                const SizedBox(width: 12),
                const Text('예측 신뢰도', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Text('신뢰도: ${result.confidenceScore ?? 0}점',
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                const SizedBox(width: 12),
                ...List.generate(
                  result.confidenceStars ?? 0,
                  (index) => const Icon(Icons.star, color: Colors.amber, size: 20),
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (result.similarCasesCount != null)
              Text('유사 사례: ${result.similarCasesCount}건'),
            if (result.regionalDataCount != null)
              Text('지역 데이터: ${result.regionalDataCount}건'),
            if (result.confidenceReasons != null && result.confidenceReasons!.isNotEmpty) ...[
              const SizedBox(height: 8),
              const Text('신뢰 근거:', style: TextStyle(fontWeight: FontWeight.bold)),
              ...result.confidenceReasons!.map((r) => Text('• $r')),
            ],
            if (result.confidenceWarnings != null && result.confidenceWarnings!.isNotEmpty) ...[
              const SizedBox(height: 8),
              const Text('주의사항:', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.orange)),
              ...result.confidenceWarnings!.map((w) => Text('• $w', style: const TextStyle(color: Colors.orange))),
            ],
          ],
        ),
      ),
    );
  }

  // 3. 경쟁 분석 카드
  Widget _buildCompetitionCard() {
    final result = _result!;
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.purple[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.people, color: Colors.purple[700]),
                ),
                const SizedBox(width: 12),
                const Text('경쟁 분석', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 16),
            if (result.competitionLevel != null)
              Text('경쟁 강도: ${result.competitionLevel}',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            if (result.viewCount != null) Text('조회수: ${result.viewCount}회'),
            if (result.avgBidderCount != null) Text('평균 입찰자: ${result.avgBidderCount}명'),
            if (result.avgSuccessRate != null)
              Text('평균 낙찰률: ${result.avgSuccessRate!.toStringAsFixed(1)}%'),
            if (result.recentCasesSummary != null) ...[
              const SizedBox(height: 8),
              Text(result.recentCasesSummary!),
            ],
          ],
        ),
      ),
    );
  }

  // 4. 리스크 분석 카드
  Widget _buildRiskAnalysisCard() {
    final result = _result!;
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.red[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.warning, color: Colors.red[700]),
                ),
                const SizedBox(width: 12),
                const Text('리스크 분석', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 16),
            if (result.riskLevel != null)
              Text('리스크 수준: ${result.riskLevel}',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            if (result.riskScore != null) Text('리스크 점수: ${result.riskScore}/10'),
            if (result.riskFactors != null && result.riskFactors!.isNotEmpty) ...[
              const SizedBox(height: 8),
              const Text('위험 요소:', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.red)),
              ...result.riskFactors!.map((r) => Text('• $r', style: const TextStyle(color: Colors.red))),
            ],
            if (result.safetyFactors != null && result.safetyFactors!.isNotEmpty) ...[
              const SizedBox(height: 8),
              const Text('안전 요소:', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.green)),
              ...result.safetyFactors!.map((s) => Text('• $s', style: const TextStyle(color: Colors.green))),
            ],
            if (result.legalAdvice != null) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.yellow[100],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(result.legalAdvice!, style: const TextStyle(fontWeight: FontWeight.bold)),
              ),
            ],
          ],
        ),
      ),
    );
  }

  // 5. 회차별 가격 추이 카드
  Widget _buildRoundHistoryCard() {
    final result = _result!;
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.teal[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.trending_down, color: Colors.teal[700]),
                ),
                const SizedBox(width: 12),
                const Text('회차별 가격 추이', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 16),
            if (result.priceTrend != null) Text('추세: ${result.priceTrend}'),
            const SizedBox(height: 8),
            ...result.roundHistory!.map((h) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('${h.round}회차'),
                      Text(h.formattedPrice),
                      Text(
                        '${h.changeRate.toStringAsFixed(1)}%',
                        style: TextStyle(
                          color: h.changeRate < 0 ? Colors.blue : Colors.grey,
                        ),
                      ),
                    ],
                  ),
                )),
            if (result.nextRoundPredictedPrice != null) ...[
              const Divider(),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('다음 회차 예상', style: TextStyle(fontWeight: FontWeight.bold)),
                  Text(PredictionResult.formatNumber(result.nextRoundPredictedPrice!)),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  // 6. 유사 물건 비교 카드
  Widget _buildSimilarPropertiesCard() {
    final result = _result!;
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.indigo[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.compare_arrows, color: Colors.indigo[700]),
                ),
                const SizedBox(width: 12),
                const Text('유사 물건 비교', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 16),
            if (result.comparisonSummary != null) Text(result.comparisonSummary!),
            const SizedBox(height: 8),
            ...result.similarProperties!.take(3).map((p) => Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(p.address, style: const TextStyle(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 4),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('낙찰가: ${p.formattedWinningBid}'),
                          Text('유사도: ${p.similarityScore}%'),
                        ],
                      ),
                    ],
                  ),
                )),
          ],
        ),
      ),
    );
  }

  // 7. 입찰 시뮬레이터 카드
  Widget _buildBidSimulatorCard() {
    final result = _result!;
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.cyan[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.calculate, color: Colors.cyan[700]),
                ),
                const SizedBox(width: 12),
                const Text('입찰 시뮬레이터', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 16),
            if (result.simulatorGuidance != null) Text(result.simulatorGuidance!),
            const SizedBox(height: 8),
            ...result.bidSimulations!.map((sim) => Container(
                  margin: const EdgeInsets.only(bottom: 8),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(sim.formattedBidAmount, style: const TextStyle(fontWeight: FontWeight.bold)),
                          Text('낙찰확률: ${sim.winProbability}%',
                              style: TextStyle(
                                color: sim.winProbability >= 70
                                    ? Colors.green
                                    : sim.winProbability >= 40
                                        ? Colors.orange
                                        : Colors.red,
                                fontWeight: FontWeight.bold,
                              )),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(sim.recommendation, style: const TextStyle(fontSize: 12)),
                    ],
                  ),
                )),
          ],
        ),
      ),
    );
  }

  // 8. D-day 알림 카드
  Widget _buildDdayCard() {
    final result = _result!;
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.orange[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.event, color: Colors.orange[700]),
                ),
                const SizedBox(width: 12),
                const Text('경매일 D-day', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 16),
            if (result.auctionDateTime != null) Text('경매일시: ${result.auctionDateTime}'),
            if (result.daysUntilAuction != null)
              Text('D-${result.daysUntilAuction}', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.red)),
            if (result.urgencyMessage != null) ...[
              const SizedBox(height: 8),
              Text(result.urgencyMessage!, style: const TextStyle(color: Colors.orange)),
            ],
            if (result.preparationChecklist != null && result.preparationChecklist!.isNotEmpty) ...[
              const SizedBox(height: 12),
              const Text('준비사항 체크리스트:', style: TextStyle(fontWeight: FontWeight.bold)),
              ...result.preparationChecklist!.map((item) => Padding(
                    padding: const EdgeInsets.only(left: 8, top: 4),
                    child: Row(
                      children: [
                        const Icon(Icons.check_box_outline_blank, size: 18),
                        const SizedBox(width: 8),
                        Expanded(child: Text(item)),
                      ],
                    ),
                  )),
            ],
          ],
        ),
      ),
    );
  }

  // 10. 전문가 팁 카드
  Widget _buildExpertTipsCard() {
    final result = _result!;
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.amber[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.tips_and_updates, color: Colors.amber[700]),
                ),
                const SizedBox(width: 12),
                const Text('전문가 팁', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 16),
            ...result.expertTips!.map((tip) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.lightbulb, size: 18, color: Colors.amber),
                      const SizedBox(width: 8),
                      Expanded(child: Text(tip)),
                    ],
                  ),
                )),
            if (result.communityInsight != null) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.blue[50],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(result.communityInsight!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
