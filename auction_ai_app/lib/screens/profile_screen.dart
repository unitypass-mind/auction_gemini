import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../services/api_service.dart';
import 'subscriptions_screen.dart';
import 'search_history_screen.dart';
import 'favorites_screen.dart';
import 'change_password_screen.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);
    final user = authProvider.user;

    return Scaffold(
      appBar: AppBar(
        title: const Text('내 정보'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // 프로필 카드
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    CircleAvatar(
                      radius: 50,
                      backgroundColor: Theme.of(context).colorScheme.primary,
                      child: Text(
                        user?.name.substring(0, 1).toUpperCase() ?? 'U',
                        style: const TextStyle(
                          fontSize: 36,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      user?.name ?? '사용자',
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      user?.email ?? '',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // 메뉴 리스트
            Card(
              child: Column(
                children: [
                  _buildMenuItem(
                    context,
                    icon: Icons.subscriptions,
                    title: '내 구독 목록',
                    subtitle: '경매 알림 구독 관리',
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const SubscriptionsScreen(),
                        ),
                      );
                    },
                  ),
                  const Divider(height: 1),
                  _buildMenuItem(
                    context,
                    icon: Icons.history,
                    title: '검색 기록',
                    subtitle: '최근 검색한 경매 물건',
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const SearchHistoryScreen(),
                        ),
                      );
                    },
                  ),
                  const Divider(height: 1),
                  _buildMenuItem(
                    context,
                    icon: Icons.favorite,
                    title: '관심 목록',
                    subtitle: '즐겨찾기한 경매 물건',
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const FavoritesScreen(),
                        ),
                      );
                    },
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // 설정 리스트
            Card(
              child: Column(
                children: [
                  _buildMenuItem(
                    context,
                    icon: Icons.lock_reset,
                    title: '비밀번호 변경',
                    subtitle: '보안을 위해 주기적으로 변경하세요',
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const ChangePasswordScreen(),
                        ),
                      );
                    },
                  ),
                  const Divider(height: 1),
                  _buildMenuItem(
                    context,
                    icon: Icons.notifications,
                    title: '알림 설정',
                    subtitle: '푸시 알림 설정',
                    onTap: () {
                      _showNotificationSettings(context);
                    },
                  ),
                  const Divider(height: 1),
                  _buildMenuItem(
                    context,
                    icon: Icons.help,
                    title: '도움말',
                    subtitle: '앱 사용 가이드',
                    onTap: () {
                      _showHelpDialog(context);
                    },
                  ),
                  const Divider(height: 1),
                  _buildMenuItem(
                    context,
                    icon: Icons.info,
                    title: '앱 정보',
                    subtitle: '버전 1.0.0',
                    onTap: () {
                      _showAboutDialog(context);
                    },
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // 로그아웃 버튼
            OutlinedButton(
              onPressed: () {
                _showLogoutDialog(context);
              },
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                foregroundColor: Colors.red,
                side: const BorderSide(color: Colors.red),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.logout),
                  SizedBox(width: 8),
                  Text(
                    '로그아웃',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMenuItem(
    BuildContext context, {
    required IconData icon,
    required String title,
    String? subtitle,
    required VoidCallback onTap,
  }) {
    return ListTile(
      leading: Icon(icon, color: Theme.of(context).colorScheme.primary),
      title: Text(title),
      subtitle: subtitle != null ? Text(subtitle) : null,
      trailing: const Icon(Icons.chevron_right),
      onTap: onTap,
    );
  }

  void _showLogoutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('로그아웃'),
        content: const Text('정말 로그아웃하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('취소'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              Provider.of<AuthProvider>(context, listen: false).logout();
            },
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('로그아웃'),
          ),
        ],
      ),
    );
  }

  void _showHelpDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('앱 사용 가이드'),
        content: const SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                '1. 경매 검색',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('사건번호, 지역, 물건종류로 경매 물건을 검색할 수 있습니다.'),
              SizedBox(height: 16),
              Text(
                '2. AI 예측',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('감정가, 물건종류, 지역 등을 입력하면 AI가 예상 낙찰가를 예측합니다.'),
              SizedBox(height: 16),
              Text(
                '3. 통계',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text('AI 모델의 정확도와 최근 검증 결과를 확인할 수 있습니다.'),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('확인'),
          ),
        ],
      ),
    );
  }

  void _showAboutDialog(BuildContext context) {
    showAboutDialog(
      context: context,
      applicationName: '경매 AI',
      applicationVersion: '1.0.0',
      applicationIcon: const Icon(Icons.gavel, size: 48),
      children: const [
        Text('AI 기반 부동산 경매 낙찰가 예측 앱'),
        SizedBox(height: 16),
        Text('© 2026 Auction AI'),
      ],
    );
  }

  void _showNotificationSettings(BuildContext context) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => const NotificationSettingsScreen(),
      ),
    );
  }
}

// 알림 설정 화면
class NotificationSettingsScreen extends StatefulWidget {
  const NotificationSettingsScreen({super.key});

  @override
  State<NotificationSettingsScreen> createState() => _NotificationSettingsScreenState();
}

class _NotificationSettingsScreenState extends State<NotificationSettingsScreen> {
  final ApiService _apiService = ApiService();
  bool _notificationEnabled = true;
  bool _isLoading = true;
  int _subscriptionCount = 0;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    setState(() => _isLoading = true);

    try {
      // 마스터 스위치 상태 조회
      final settingsResponse = await _apiService.getNotificationSettings();

      // 구독 개수 조회
      final subscriptionsResponse = await _apiService.getMySubscriptions();

      if (mounted) {
        setState(() {
          _notificationEnabled = settingsResponse['notification_enabled'] ?? true;
          _subscriptionCount = subscriptionsResponse['count'] ?? 0;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('설정 로드 실패: ${e.toString()}')),
        );
      }
    }
  }

  Future<void> _toggleNotification(bool value) async {
    try {
      final response = await _apiService.updateNotificationSettings(value);

      if (response['success'] == true) {
        setState(() {
          _notificationEnabled = value;
        });

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(response['message'] ?? '설정이 변경되었습니다'),
              backgroundColor: Colors.green,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('설정 변경 실패: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
        // 실패 시 이전 상태로 복원
        setState(() {
          _notificationEnabled = !value;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('알림 설정'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 마스터 스위치
                  Card(
                    child: SwitchListTile(
                      title: const Text(
                        '푸시 알림 받기',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      subtitle: Text(
                        _notificationEnabled
                            ? '모든 알림을 받습니다'
                            : '모든 알림이 꺼져 있습니다',
                        style: TextStyle(
                          color: _notificationEnabled ? Colors.green : Colors.grey,
                        ),
                      ),
                      value: _notificationEnabled,
                      onChanged: _toggleNotification,
                      secondary: Icon(
                        _notificationEnabled
                            ? Icons.notifications_active
                            : Icons.notifications_off,
                        color: _notificationEnabled ? Colors.blue : Colors.grey,
                      ),
                    ),
                  ),

                  const SizedBox(height: 16),

                  // 구독 정보
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.subscriptions, color: Colors.blue),
                              const SizedBox(width: 8),
                              const Text(
                                '구독 정보',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Text(
                            '현재 $_subscriptionCount개 경매를 구독 중입니다',
                            style: const TextStyle(fontSize: 14),
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 16),

                  // 안내 문구
                  Card(
                    color: Colors.blue[50],
                    child: const Padding(
                      padding: EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(Icons.info_outline, color: Colors.blue),
                              SizedBox(width: 8),
                              Text(
                                '알림 설정 안내',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: Colors.blue,
                                ),
                              ),
                            ],
                          ),
                          SizedBox(height: 12),
                          Text('• 알림을 끄면 모든 푸시 알림이 차단됩니다'),
                          SizedBox(height: 4),
                          Text('• 구독 설정은 그대로 유지됩니다'),
                          SizedBox(height: 4),
                          Text('• 다시 켜면 기존 구독 그대로 알림이 재개됩니다'),
                          SizedBox(height: 12),
                          Divider(),
                          SizedBox(height: 8),
                          Text(
                            '알림 종류:',
                            style: TextStyle(fontWeight: FontWeight.bold),
                          ),
                          SizedBox(height: 4),
                          Text('• 가격 하락 알림: 경매 유찰 시 가격 하락'),
                          SizedBox(height: 4),
                          Text('• 입찰 마감 알림: 입찰 마감일 전일'),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}
