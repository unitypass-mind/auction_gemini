import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/models.dart';

class StatsScreen extends StatefulWidget {
  const StatsScreen({super.key});

  @override
  State<StatsScreen> createState() => _StatsScreenState();
}

class _StatsScreenState extends State<StatsScreen> {
  final ApiService _apiService = ApiService();

  AccuracyStats? _accuracyStats;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final response = await _apiService.getAccuracy();

      if (response['success'] == true) {
        setState(() {
          _accuracyStats = AccuracyStats.fromJson(response);
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = response['message'] ?? '데이터 로드 실패';
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('통계 및 정확도'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadStats,
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
            Text(
              _error!,
              style: TextStyle(color: Colors.grey[600]),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _loadStats,
              child: const Text('다시 시도'),
            ),
          ],
        ),
      );
    }

    if (_accuracyStats == null) {
      return const Center(child: Text('데이터가 없습니다'));
    }

    return RefreshIndicator(
      onRefresh: _loadStats,
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // 자동 갱신 안내 카드
            Card(
              color: Colors.blue[50],
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Icon(Icons.info_outline, color: Colors.blue[700], size: 20),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '자동 데이터 갱신',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                              color: Colors.blue[900],
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            '• 낙찰 데이터: 매일 오전 6시\n• 통계 갱신: 매일 오전 6시 30분\n• 모델 재학습: 매주 일요일 새벽 3시',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey[700],
                              height: 1.4,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // 전체 통계 카드
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    const Text(
                      'AI 모델 성능',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 20),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        _buildStatItem(
                          '전체 예측',
                          '${_accuracyStats!.totalPredictions}건',
                          Icons.analytics,
                          Colors.blue,
                        ),
                        _buildStatItem(
                          '검증 완료',
                          '${_accuracyStats!.verifiedPredictions}건',
                          Icons.check_circle,
                          Colors.green,
                        ),
                        _buildStatItem(
                          '평균 오차',
                          '${_accuracyStats!.avgErrorRate.toStringAsFixed(1)}%',
                          Icons.percent,
                          Colors.orange,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // 최근 검증 결과
            const Text(
              '최근 검증 결과',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),

            if (_accuracyStats!.recentVerified.isEmpty)
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(32),
                  child: Center(
                    child: Text('검증된 예측이 없습니다'),
                  ),
                ),
              )
            else
              ..._accuracyStats!.recentVerified.map((verified) {
                final isAccurate = verified.errorRate < 10.0;

                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: isAccurate ? Colors.green[100] : Colors.orange[100],
                      child: Icon(
                        isAccurate ? Icons.check : Icons.warning,
                        color: isAccurate ? Colors.green[700] : Colors.orange[700],
                      ),
                    ),
                    title: Text(verified.caseNumber),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 4),
                        Text('예측: ${_formatPrice(verified.predictedPrice)}'),
                        Text('실제: ${_formatPrice(verified.actualPrice)}'),
                      ],
                    ),
                    trailing: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          '${verified.errorRate.toStringAsFixed(1)}%',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: isAccurate ? Colors.green[700] : Colors.orange[700],
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          isAccurate ? '정확' : '보통',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }).toList(),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(String label, String value, IconData icon, Color color) {
    return Column(
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: color, size: 28),
        ),
        const SizedBox(height: 8),
        Text(
          value,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
        ),
      ],
    );
  }

  String _formatPrice(int price) {
    if (price >= 100000000) {
      final eok = price ~/ 100000000;
      final man = (price % 100000000) ~/ 10000;
      if (man > 0) {
        return '$eok억 ${man}만원';
      }
      return '$eok억원';
    } else if (price >= 10000) {
      return '${price ~/ 10000}만원';
    }
    return '$price원';
  }
}
