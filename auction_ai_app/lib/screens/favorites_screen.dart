import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import '../providers/selected_auction_provider.dart';
import 'home_screen.dart';

class FavoritesScreen extends StatefulWidget {
  const FavoritesScreen({super.key});

  @override
  State<FavoritesScreen> createState() => _FavoritesScreenState();
}

class _FavoritesScreenState extends State<FavoritesScreen> {
  List<Map<String, dynamic>> _favorites = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadFavorites();
  }

  Future<void> _loadFavorites() async {
    setState(() => _isLoading = true);

    try {
      final prefs = await SharedPreferences.getInstance();
      final favoritesJson = prefs.getStringList('favorites') ?? [];

      setState(() {
        _favorites = favoritesJson
            .map((item) => jsonDecode(item) as Map<String, dynamic>)
            .toList()
            .reversed // 최신순으로 표시
            .toList();
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _removeFavorite(int index) async {
    final item = _favorites[index];
    final caseNumber = item['case_number'] ?? '알 수 없음';

    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('즐겨찾기 삭제'),
        content: Text('$caseNumber을(를) 즐겨찾기에서 삭제하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('삭제'),
          ),
        ],
      ),
    );

    if (confirm == true) {
      try {
        final prefs = await SharedPreferences.getInstance();
        final favoritesJson = prefs.getStringList('favorites') ?? [];

        // reversed 했으므로 실제 인덱스는 반대
        final actualIndex = favoritesJson.length - 1 - index;
        favoritesJson.removeAt(actualIndex);

        await prefs.setStringList('favorites', favoritesJson);

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('즐겨찾기에서 삭제되었습니다')),
          );
          _loadFavorites();
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('삭제 실패: ${e.toString()}')),
          );
        }
      }
    }
  }

  Future<void> _clearAllFavorites() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('전체 삭제'),
        content: const Text('모든 즐겨찾기를 삭제하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('전체 삭제'),
          ),
        ],
      ),
    );

    if (confirm == true) {
      try {
        final prefs = await SharedPreferences.getInstance();
        await prefs.remove('favorites');

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('모든 즐겨찾기가 삭제되었습니다')),
          );
          _loadFavorites();
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('삭제 실패: ${e.toString()}')),
          );
        }
      }
    }
  }

  void _viewDetails(String caseNumber) {
    print('=== FavoritesScreen: _viewDetails called ===');
    print('Case number: $caseNumber');

    // 홈 화면으로 돌아가면서 검색 탭으로 전환하고 자동 검색 실행
    Navigator.of(context).popUntil((route) => route.isFirst);
    print('Navigated back to home screen');

    // autoSearchCaseNumber 파라미터를 전달하여 자동 검색 실행
    HomeScreen.globalKey.currentState?.switchTab(0, autoSearchCaseNumber: caseNumber);
    print('Switched to tab 0 with auto-search for: $caseNumber');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('관심 목록'),
        actions: [
          if (_favorites.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_sweep),
              onPressed: _clearAllFavorites,
              tooltip: '전체 삭제',
            ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_favorites.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.favorite_border, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(
              '즐겨찾기한 경매가 없습니다',
              style: TextStyle(color: Colors.grey[600]),
            ),
            const SizedBox(height: 8),
            Text(
              '경매 상세 페이지에서 하트 아이콘을 눌러\n즐겨찾기에 추가할 수 있습니다',
              style: TextStyle(color: Colors.grey[500], fontSize: 12),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _favorites.length,
      itemBuilder: (context, index) {
        final item = _favorites[index];
        return _buildFavoriteCard(item, index);
      },
    );
  }

  Widget _buildFavoriteCard(Map<String, dynamic> item, int index) {
    final caseNumber = item['case_number'] ?? '알 수 없음';
    final propertyType = item['property_type'] ?? '-';
    final address = item['address'] ?? '-';
    final startPrice = item['start_price'];
    final predictedPrice = item['predicted_price'];
    final addedAt = item['timestamp'] ?? '';

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: () => _viewDetails(caseNumber),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          caseNumber,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          propertyType,
                          style: TextStyle(
                            fontSize: 13,
                            color: Colors.grey[700],
                          ),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.favorite, color: Colors.red),
                    onPressed: () => _removeFavorite(index),
                    tooltip: '즐겨찾기 삭제',
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                address,
                style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 12),
              if (startPrice != null || predictedPrice != null) ...[
                Row(
                  children: [
                    if (startPrice != null) ...[
                      Expanded(
                        child: _buildPriceInfo(
                          '감정가',
                          _formatPrice(startPrice),
                          Colors.blue,
                        ),
                      ),
                    ],
                    if (predictedPrice != null) ...[
                      const SizedBox(width: 12),
                      Expanded(
                        child: _buildPriceInfo(
                          'AI 예측가',
                          _formatPrice(predictedPrice),
                          Colors.purple,
                        ),
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 8),
              ],
              const Divider(),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    _formatDateTime(addedAt),
                    style: TextStyle(fontSize: 11, color: Colors.grey[500]),
                  ),
                  Text(
                    '자세히 보기',
                    style: TextStyle(
                      fontSize: 12,
                      color: Theme.of(context).colorScheme.primary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPriceInfo(String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              color: Colors.grey[700],
            ),
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  String _formatPrice(dynamic price) {
    try {
      final priceInt = price is int ? price : int.parse(price.toString());
      if (priceInt >= 100000000) {
        final eok = priceInt / 100000000;
        return '${eok.toStringAsFixed(1)}억';
      } else {
        final man = priceInt / 10000;
        return '${man.toStringAsFixed(0)}만원';
      }
    } catch (e) {
      return price.toString();
    }
  }

  String _formatDateTime(String dateTimeStr) {
    try {
      final dateTime = DateTime.parse(dateTimeStr);
      final now = DateTime.now();
      final difference = now.difference(dateTime);

      if (difference.inMinutes < 1) {
        return '방금 추가';
      } else if (difference.inHours < 1) {
        return '${difference.inMinutes}분 전 추가';
      } else if (difference.inDays < 1) {
        return '${difference.inHours}시간 전 추가';
      } else if (difference.inDays < 7) {
        return '${difference.inDays}일 전 추가';
      } else {
        return '${dateTime.year}-${dateTime.month.toString().padLeft(2, '0')}-${dateTime.day.toString().padLeft(2, '0')} 추가';
      }
    } catch (e) {
      return '';
    }
  }
}
