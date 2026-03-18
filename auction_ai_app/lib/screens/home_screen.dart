import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import 'search_screen.dart';
import 'prediction_screen.dart';
import 'stats_screen.dart';
import 'profile_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();

  /// HomeScreen의 GlobalKey (다른 화면에서 탭 전환용)
  static final GlobalKey<_HomeScreenState> globalKey = GlobalKey<_HomeScreenState>();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  final List<Widget> _screens = [
    const SearchScreen(),
    const PredictionScreen(),
    const StatsScreen(),
    const ProfileScreen(),
  ];

  /// 외부에서 탭을 전환할 수 있는 메서드
  void switchTab(int index) {
    if (index >= 0 && index < _screens.length) {
      setState(() {
        _currentIndex = index;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.analytics),
            label: '전체 분석',
          ),
          NavigationDestination(
            icon: Icon(Icons.psychology),
            label: 'AI 예측',
          ),
          NavigationDestination(
            icon: Icon(Icons.bar_chart),
            label: '통계',
          ),
          NavigationDestination(
            icon: Icon(Icons.person),
            label: '내 정보',
          ),
        ],
      ),
    );
  }
}
