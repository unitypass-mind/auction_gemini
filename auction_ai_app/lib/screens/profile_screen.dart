import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';

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
                      // TODO: 구독 목록 화면으로 이동
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('구독 목록 기능 준비중입니다')),
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
                      // TODO: 검색 기록 화면으로 이동
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('검색 기록 기능 준비중입니다')),
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
                      // TODO: 관심 목록 화면으로 이동
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('관심 목록 기능 준비중입니다')),
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
                    icon: Icons.notifications,
                    title: '알림 설정',
                    subtitle: '푸시 알림 설정',
                    onTap: () {
                      // TODO: 알림 설정 화면으로 이동
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('알림 설정 기능 준비중입니다')),
                      );
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
}
