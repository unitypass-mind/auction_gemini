import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/models.dart';

class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final ApiService _apiService = ApiService();
  final _caseNumberController = TextEditingController();

  FullAnalysisResult? _result;
  bool _isLoading = false;
  String? _error;

  String _selectedYear = DateTime.now().year.toString();
  final String _caseType = '타경'; // 고정

  @override
  void dispose() {
    _caseNumberController.dispose();
    super.dispose();
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
      // 먼저 사건번호로 물건 목록 조회
      final listResponse = await _apiService.listAuctionsByCaseNumber(caseNumber);

      if (listResponse['success'] != true) {
        setState(() {
          _error = listResponse['message'] ?? '물건 조회에 실패했습니다';
          _isLoading = false;
        });
        return;
      }

      final int count = listResponse['count'] ?? 0;
      final List<dynamic> items = listResponse['items'] ?? [];

      if (count == 0) {
        setState(() {
          _error = '해당 사건번호의 경매 물건을 찾을 수 없습니다';
          _isLoading = false;
        });
        return;
      }

      // 물건이 1개인 경우 바로 분석
      if (count == 1) {
        await _performFullAnalysis(caseNumber);
        return;
      }

      // 물건이 여러 개인 경우 선택 다이얼로그 표시
      setState(() {
        _isLoading = false;
      });

      if (!mounted) return;

      final selectedItem = await _showItemSelectionDialog(items);

      if (selectedItem != null) {
        await _performFullAnalysis(caseNumber, court: selectedItem['court']);
      }

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
        setState(() {
          _result = FullAnalysisResult.fromJson(response);
          _isLoading = false;
        });
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
      ),
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

          // 가격 비교 분석
          _buildPriceComparisonCard(),
          const SizedBox(height: 16),

          // 투자 매력도
          _buildInvestmentScoreCard(),
          const SizedBox(height: 16),

          // 입찰 전략
          _buildBiddingStrategyCard(),
          const SizedBox(height: 16),

          // 권리분석
          if (_result!.auctionInfo['권리분석'] != null)
            _buildRightsAnalysisCard(),
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

        // 금액
        Text(
          amount,
          style: TextStyle(
            fontSize: 10,
            color: Colors.grey[700],
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
}
