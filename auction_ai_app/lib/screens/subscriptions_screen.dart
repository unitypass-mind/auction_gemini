import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../providers/selected_auction_provider.dart';

class SubscriptionsScreen extends StatefulWidget {
  const SubscriptionsScreen({super.key});

  @override
  State<SubscriptionsScreen> createState() => _SubscriptionsScreenState();
}

class _SubscriptionsScreenState extends State<SubscriptionsScreen> {
  final ApiService _apiService = ApiService();
  List<dynamic> _subscriptions = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadSubscriptions();
  }

  Future<void> _loadSubscriptions() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      print('=== Loading subscriptions ===');

      final response = await _apiService.getMySubscriptions();

      print('=== Subscriptions Response ===');
      print('Response: $response');

      if (response['success'] == true) {
        setState(() {
          _subscriptions = response['subscriptions'] ?? [];
          _isLoading = false;
        });

        print('Loaded ${_subscriptions.length} subscriptions');
      } else {
        setState(() {
          _error = response['message'] ?? '구독 목록을 불러올 수 없습니다';
          _isLoading = false;
        });
      }
    } catch (e) {
      print('=== Subscriptions Error ===');
      print('Error: $e');
      print('Error type: ${e.runtimeType}');

      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _showEditSubscriptionDialog(Map<String, dynamic> subscription) async {
    final caseNumber = subscription['case_number'] ?? '알 수 없음';
    bool priceDropAlert = subscription['price_drop_alert'] ?? true;
    bool bidReminderAlert = subscription['bid_reminder_alert'] ?? true;

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: Row(
            children: [
              const Icon(Icons.edit_notifications, color: Colors.blue),
              const SizedBox(width: 8),
              const Expanded(child: Text('알림 설정')),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                caseNumber,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),
              CheckboxListTile(
                title: const Text('가격 하락 알림'),
                subtitle: const Text('유찰로 인한 가격 하락 시 알림'),
                value: priceDropAlert,
                onChanged: (value) {
                  setState(() {
                    priceDropAlert = value ?? true;
                  });
                },
                secondary: const Icon(Icons.trending_down, color: Colors.blue),
              ),
              CheckboxListTile(
                title: const Text('입찰 마감 알림'),
                subtitle: const Text('입찰 마감일 전일 알림'),
                value: bidReminderAlert,
                onChanged: (value) {
                  setState(() {
                    bidReminderAlert = value ?? true;
                  });
                },
                secondary: const Icon(Icons.alarm, color: Colors.orange),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('취소'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('저장'),
            ),
          ],
        ),
      ),
    );

    if (confirmed == true) {
      await _updateSubscription(
        caseNumber: caseNumber,
        priceDropAlert: priceDropAlert,
        bidReminderAlert: bidReminderAlert,
      );
    }
  }

  Future<void> _updateSubscription({
    required String caseNumber,
    required bool priceDropAlert,
    required bool bidReminderAlert,
  }) async {
    try {
      print('=== Updating subscription ===');
      print('Case Number: $caseNumber');
      print('Price Drop Alert: $priceDropAlert');
      print('Bid Reminder Alert: $bidReminderAlert');

      final response = await _apiService.subscribeAuction(
        caseNumber: caseNumber,
        priceDropAlert: priceDropAlert,
        bidReminderAlert: bidReminderAlert,
      );

      print('=== Update Response ===');
      print('Response: $response');

      if (response['success'] == true) {
        // Provider에 상태 저장 (구독 유지, 설정만 변경)
        if (mounted) {
          final provider = Provider.of<SelectedAuctionProvider>(context, listen: false);
          provider.setSubscriptionState(caseNumber, true);

          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('알림 설정이 변경되었습니다'),
              backgroundColor: Colors.green,
            ),
          );
          _loadSubscriptions(); // 목록 새로고침
        }
      } else {
        if (mounted) {
          final message = response['message'] ?? '설정 변경에 실패했습니다';
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(message)),
          );
        }
      }
    } catch (e) {
      print('=== Update Error ===');
      print('Error: $e');

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('설정 변경 실패: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _unsubscribe(int subscriptionId, String caseNumber) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('구독 해제'),
        content: Text('$caseNumber 경매의 알림 구독을 해제하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('해제'),
          ),
        ],
      ),
    );

    if (confirm == true) {
      try {
        print('=== Unsubscribing ===');
        print('Subscription ID: $subscriptionId');

        final response = await _apiService.unsubscribe(subscriptionId);

        print('=== Unsubscribe Response ===');
        print('Response: $response');

        if (response['success'] == true) {
          // Provider에 상태 저장 (즉시 반영)
          if (mounted) {
            final provider = Provider.of<SelectedAuctionProvider>(context, listen: false);
            provider.setSubscriptionState(caseNumber, false);

            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('구독이 해제되었습니다'),
                backgroundColor: Colors.green,
              ),
            );
            _loadSubscriptions(); // 목록 새로고침
          }
        } else {
          if (mounted) {
            final message = response['message'] ?? '구독 해제에 실패했습니다';
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(message)),
            );
          }
        }
      } catch (e) {
        print('=== Unsubscribe Error ===');
        print('Error: $e');
        print('Error type: ${e.runtimeType}');

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('구독 해제 실패: ${e.toString()}'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('내 구독 목록'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadSubscriptions,
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

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 64, color: Colors.red[300]),
            const SizedBox(height: 16),
            Text(_error!, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadSubscriptions,
              child: const Text('다시 시도'),
            ),
          ],
        ),
      );
    }

    if (_subscriptions.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.notifications_off, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(
              '구독 중인 경매가 없습니다',
              style: TextStyle(color: Colors.grey[600]),
            ),
            const SizedBox(height: 8),
            Text(
              '경매 상세 페이지에서 알림을 구독할 수 있습니다',
              style: TextStyle(color: Colors.grey[500], fontSize: 12),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadSubscriptions,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _subscriptions.length,
        itemBuilder: (context, index) {
          final subscription = _subscriptions[index];
          return _buildSubscriptionCard(subscription);
        },
      ),
    );
  }

  Widget _buildSubscriptionCard(Map<String, dynamic> subscription) {
    final caseNumber = subscription['case_number'] ?? '알 수 없음';
    final priceDropAlert = subscription['price_drop_alert'] ?? false;
    final bidReminderAlert = subscription['bid_reminder_alert'] ?? false;
    final createdAt = subscription['created_at'] ?? '';
    final subscriptionId = subscription['id'];

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: () => _showEditSubscriptionDialog(subscription),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(
                    Icons.gavel,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  const SizedBox(width: 12),
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
                        if (createdAt.isNotEmpty)
                          Text(
                            '구독일: ${_formatDate(createdAt)}',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey[600],
                            ),
                          ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.delete_outline, color: Colors.red),
                    onPressed: () => _unsubscribe(subscriptionId, caseNumber),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              const Divider(),
              const SizedBox(height: 8),
              Row(
                children: [
                  if (priceDropAlert) ...[
                    Chip(
                      avatar: const Icon(Icons.trending_down, size: 16),
                      label: const Text('가격 하락 알림', style: TextStyle(fontSize: 12)),
                      backgroundColor: Colors.blue[50],
                    ),
                    const SizedBox(width: 8),
                  ],
                  if (bidReminderAlert) ...[
                    Chip(
                      avatar: const Icon(Icons.alarm, size: 16),
                      label: const Text('입찰 마감 알림', style: TextStyle(fontSize: 12)),
                      backgroundColor: Colors.orange[50],
                    ),
                  ],
                  const Spacer(),
                  Icon(Icons.edit, size: 16, color: Colors.grey[400]),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
    } catch (e) {
      return dateStr;
    }
  }
}
