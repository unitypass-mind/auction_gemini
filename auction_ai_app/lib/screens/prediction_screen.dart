import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../models/models.dart';
import '../providers/selected_auction_provider.dart';

class PredictionScreen extends StatefulWidget {
  const PredictionScreen({super.key});

  @override
  State<PredictionScreen> createState() => _PredictionScreenState();
}

class _PredictionScreenState extends State<PredictionScreen> {
  final ApiService _apiService = ApiService();
  final _formKey = GlobalKey<FormState>();

  final _startPriceController = TextEditingController();
  final _areaController = TextEditingController();

  String? _selectedPropertyType;
  String? _selectedRegion;
  int _auctionRound = 1;

  bool _isLoading = false;
  PredictionResult? _result;
  String? _error;

  final List<String> _propertyTypes = [
    '아파트', '오피스텔', '빌라', '단독주택', '다가구', '상가', '토지'
  ];

  final List<String> _regions = [
    '서울', '경기', '인천', '부산', '대구', '대전', '광주',
    '울산', '세종', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주'
  ];

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();

    // Provider에서 선택된 물건 정보 가져오기
    final selectedAuctionProvider = Provider.of<SelectedAuctionProvider>(context);
    final selectedItem = selectedAuctionProvider.selectedItem;

    if (selectedItem != null) {
      // 선택된 물건 정보로 필드 자동 채우기
      _startPriceController.text = selectedItem.startPrice.toString();
      _selectedPropertyType = selectedItem.propertyType;
      _selectedRegion = selectedItem.region;
      _auctionRound = selectedItem.auctionRound;
      if (selectedItem.area != null) {
        _areaController.text = selectedItem.area!.toString();
      }

      // 사용 후 선택 해제
      selectedAuctionProvider.clearSelection();
    }
  }

  @override
  void dispose() {
    _startPriceController.dispose();
    _areaController.dispose();
    super.dispose();
  }

  Future<void> _predictPrice() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
      _error = null;
      _result = null;
    });

    try {
      final startPrice = int.parse(_startPriceController.text.replaceAll(',', ''));
      final area = _areaController.text.isNotEmpty
          ? double.parse(_areaController.text)
          : null;

      final response = await _apiService.predictPrice(
        startPrice: startPrice,
        propertyType: _selectedPropertyType,
        region: _selectedRegion,
        area: area,
        auctionRound: _auctionRound,
      );

      if (response['success'] == true) {
        setState(() {
          _result = PredictionResult.fromJson(response);
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = response['message'] ?? '예측에 실패했습니다';
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
        title: const Text('AI 낙찰가 예측'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // 안내 카드
              Card(
                color: Colors.blue[50],
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      Icon(Icons.info_outline, color: Colors.blue[700]),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'AI 모델이 감정가, 물건종류, 지역 등을 분석하여\n예상 낙찰가를 예측합니다',
                          style: TextStyle(
                            color: Colors.blue[900],
                            fontSize: 13,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // 감정가 입력
              TextFormField(
                controller: _startPriceController,
                keyboardType: TextInputType.number,
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                decoration: InputDecoration(
                  labelText: '감정가 (원)',
                  hintText: '예: 100000000',
                  prefixIcon: const Icon(Icons.attach_money),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  helperText: '숫자만 입력해주세요',
                ),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return '감정가를 입력해주세요';
                  }
                  final price = int.tryParse(value);
                  if (price == null || price <= 0) {
                    return '올바른 금액을 입력해주세요';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),

              // 물건종류
              DropdownButtonFormField<String>(
                value: _selectedPropertyType,
                decoration: InputDecoration(
                  labelText: '물건종류',
                  prefixIcon: const Icon(Icons.home),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                items: _propertyTypes.map((type) {
                  return DropdownMenuItem(
                    value: type,
                    child: Text(type),
                  );
                }).toList(),
                onChanged: (value) {
                  setState(() {
                    _selectedPropertyType = value;
                  });
                },
              ),
              const SizedBox(height: 16),

              // 지역
              DropdownButtonFormField<String>(
                value: _selectedRegion,
                decoration: InputDecoration(
                  labelText: '지역',
                  prefixIcon: const Icon(Icons.location_on),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                items: _regions.map((region) {
                  return DropdownMenuItem(
                    value: region,
                    child: Text(region),
                  );
                }).toList(),
                onChanged: (value) {
                  setState(() {
                    _selectedRegion = value;
                  });
                },
              ),
              const SizedBox(height: 16),

              // 면적 (선택사항)
              TextFormField(
                controller: _areaController,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(
                  labelText: '면적 (㎡) - 선택사항',
                  hintText: '예: 84.5',
                  prefixIcon: const Icon(Icons.square_foot),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // 경매 회차
              Row(
                children: [
                  const Icon(Icons.repeat),
                  const SizedBox(width: 12),
                  const Text('경매 회차:', style: TextStyle(fontSize: 16)),
                  const SizedBox(width: 16),
                  ChoiceChip(
                    label: const Text('1회차'),
                    selected: _auctionRound == 1,
                    onSelected: (selected) {
                      if (selected) setState(() => _auctionRound = 1);
                    },
                  ),
                  const SizedBox(width: 8),
                  ChoiceChip(
                    label: const Text('2회차'),
                    selected: _auctionRound == 2,
                    onSelected: (selected) {
                      if (selected) setState(() => _auctionRound = 2);
                    },
                  ),
                  const SizedBox(width: 8),
                  ChoiceChip(
                    label: const Text('3회차+'),
                    selected: _auctionRound >= 3,
                    onSelected: (selected) {
                      if (selected) setState(() => _auctionRound = 3);
                    },
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // 예측 버튼
              ElevatedButton(
                onPressed: _isLoading ? null : _predictPrice,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
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
                    : const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.psychology),
                          SizedBox(width: 8),
                          Text(
                            'AI 예측하기',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
              ),

              // 예측 결과
              if (_result != null) ...[
                const SizedBox(height: 32),
                _buildPredictionResult(),
              ],

              // 에러 메시지
              if (_error != null) ...[
                const SizedBox(height: 24),
                Card(
                  color: Colors.red[50],
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        Icon(Icons.error_outline, color: Colors.red[700]),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            _error!,
                            style: TextStyle(color: Colors.red[900]),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPredictionResult() {
    final result = _result!;

    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // 타이틀
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.blue[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.analytics, color: Colors.blue[700]),
                ),
                const SizedBox(width: 12),
                const Text(
                  'AI 예측 결과',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const Divider(height: 24),

            // 예측 낙찰가
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [Colors.blue[400]!, Colors.blue[600]!],
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
                    result.formattedPredictedPrice,
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

            // 입찰 전략 가이드
            if (result.safeBidPrice != null) ...[
              const SizedBox(height: 24),
              const Divider(),
              const SizedBox(height: 16),
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.purple[100],
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(Icons.lightbulb, color: Colors.purple[700]),
                  ),
                  const SizedBox(width: 12),
                  const Text(
                    '입찰 전략 가이드',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // 신뢰구간
              if (result.confidenceLowerBound != null && result.confidenceUpperBound != null)
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.show_chart, color: Colors.grey[700], size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '예측 신뢰구간 (±5%)',
                              style: TextStyle(
                                color: Colors.grey[800],
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              '${result.formattedConfidenceLowerBound} ~ ${result.formattedConfidenceUpperBound}',
                              style: TextStyle(
                                color: Colors.grey[700],
                                fontSize: 14,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              const SizedBox(height: 12),

              // 권장 입찰가
              if (result.recommendedBidPrice != null)
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [Colors.purple[400]!, Colors.purple[600]!],
                    ),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.stars, color: Colors.white, size: 28),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              '권장 입찰가',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 14,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              result.formattedRecommendedBidPrice ?? '',
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 24,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 4),
                            const Text(
                              '예측가 +5% (균형잡힌 전략)',
                              style: TextStyle(
                                color: Colors.white70,
                                fontSize: 11,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              const SizedBox(height: 12),

              // 안전 입찰 vs 공격 입찰
              Row(
                children: [
                  // 안전 입찰
                  if (result.safeBidPrice != null)
                    Expanded(
                      child: Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.green[50],
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.green[300]!),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(Icons.check_circle, color: Colors.green[700], size: 18),
                                const SizedBox(width: 6),
                                const Text(
                                  '안전 입찰',
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              result.formattedSafeBidPrice ?? '',
                              style: TextStyle(
                                color: Colors.green[900],
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              '낙찰 확률 ${result.safeBidProbability ?? 85}%',
                              style: TextStyle(
                                color: Colors.green[700],
                                fontSize: 11,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  const SizedBox(width: 12),
                  // 공격 입찰
                  if (result.aggressiveBidPrice != null)
                    Expanded(
                      child: Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.orange[50],
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.orange[300]!),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(Icons.flash_on, color: Colors.orange[700], size: 18),
                                const SizedBox(width: 6),
                                const Text(
                                  '공격 입찰',
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              result.formattedAggressiveBidPrice ?? '',
                              style: TextStyle(
                                color: Colors.orange[900],
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              '낙찰 확률 ${result.aggressiveBidProbability ?? 50}%',
                              style: TextStyle(
                                color: Colors.orange[700],
                                fontSize: 11,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 12),

              // 안내 메시지
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.blue[50],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.info_outline, color: Colors.blue[700], size: 18),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '입찰 전략은 AI 예측가를 기준으로 계산됩니다.\n실제 입찰 시 경쟁 상황과 물건 상태를 반드시 고려하세요.',
                        style: TextStyle(
                          color: Colors.blue[900],
                          fontSize: 11,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],

            // 모델 사용 여부
            if (result.modelUsed) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.green[50],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Icon(Icons.check_circle, color: Colors.green[700], size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        result.predictionMode ?? 'AI 모델 사용',
                        style: TextStyle(
                          color: Colors.green[900],
                          fontSize: 13,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],

            // 경고 메시지
            if (result.warning != null) ...[
              const SizedBox(height: 16),
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
                        result.warning!,
                        style: TextStyle(
                          color: Colors.orange[900],
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],

            // 수익 정보
            Row(
              children: [
                Expanded(
                  child: _buildInfoItem(
                    '예상 수익',
                    result.formattedExpectedProfit,
                    Icons.trending_up,
                    Colors.green,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildInfoItem(
                    '수익률',
                    result.formattedProfitRate,
                    Icons.percent,
                    Colors.orange,
                  ),
                ),
              ],
            ),

            // 경쟁 분석
            if (result.competitionLevel != null) ...[
              const SizedBox(height: 24),
              const Divider(),
              const SizedBox(height: 16),
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.orange[100],
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(Icons.people, color: Colors.orange[700]),
                  ),
                  const SizedBox(width: 12),
                  const Text(
                    '경쟁 분석',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.orange[50],
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.orange[200]!),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 예상 경쟁 강도
                    Row(
                      children: [
                        Icon(Icons.trending_up, color: Colors.orange[700], size: 20),
                        const SizedBox(width: 8),
                        const Text(
                          '예상 경쟁 강도:',
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                          decoration: BoxDecoration(
                            color: result.competitionLevel == '높음'
                                ? Colors.red[100]
                                : result.competitionLevel == '중간'
                                    ? Colors.orange[100]
                                    : Colors.green[100],
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            result.competitionLevel!,
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                              color: result.competitionLevel == '높음'
                                  ? Colors.red[900]
                                  : result.competitionLevel == '중간'
                                      ? Colors.orange[900]
                                      : Colors.green[900],
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // 통계 정보
                    Row(
                      children: [
                        // 조회수
                        if (result.viewCount != null)
                          Expanded(
                            child: Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Column(
                                children: [
                                  Icon(Icons.visibility, color: Colors.grey[600], size: 20),
                                  const SizedBox(height: 4),
                                  Text(
                                    '조회수',
                                    style: TextStyle(
                                      fontSize: 11,
                                      color: Colors.grey[600],
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    '${result.viewCount}회',
                                    style: TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.grey[800],
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        const SizedBox(width: 8),
                        // 평균 입찰자
                        if (result.avgBidderCount != null)
                          Expanded(
                            child: Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Column(
                                children: [
                                  Icon(Icons.group, color: Colors.grey[600], size: 20),
                                  const SizedBox(height: 4),
                                  Text(
                                    '평균 입찰자',
                                    style: TextStyle(
                                      fontSize: 11,
                                      color: Colors.grey[600],
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    '${result.avgBidderCount}명',
                                    style: TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.grey[800],
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                      ],
                    ),

                    // 최근 유사 물건 요약
                    if (result.recentCasesSummary != null) ...[
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(Icons.history, color: Colors.grey[700], size: 16),
                                const SizedBox(width: 6),
                                Text(
                                  '최근 유사 물건 낙찰 현황',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.grey[800],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              result.recentCasesSummary!,
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey[700],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],

                    // 평균 낙찰률
                    if (result.avgSuccessRate != null) ...[
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Row(
                              children: [
                                Icon(Icons.check_circle, color: Colors.green[700], size: 16),
                                const SizedBox(width: 6),
                                const Text(
                                  '평균 낙찰률',
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                            Text(
                              '${result.avgSuccessRate!.toStringAsFixed(1)}% (감정가 대비)',
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.bold,
                                color: Colors.green[900],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],

            // 실시간 유사 물건 비교
            if (result.similarProperties != null &&
                result.similarProperties!.isNotEmpty) ...[
              const SizedBox(height: 20),
              Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      Colors.teal.shade50,
                      Colors.cyan.shade50,
                    ],
                  ),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: Colors.teal.shade300,
                    width: 2,
                  ),
                ),
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          Icons.compare_arrows,
                          color: Colors.teal.shade700,
                          size: 24,
                        ),
                        const SizedBox(width: 8),
                        const Text(
                          '실시간 유사 물건 비교',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // 가격 통계
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.grey.shade300),
                      ),
                      child: Row(
                        children: [
                          if (result.avgSimilarPrice != null)
                            Expanded(
                              child: Column(
                                children: [
                                  Icon(
                                    Icons.show_chart,
                                    color: Colors.teal.shade600,
                                    size: 24,
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    '평균',
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: Colors.grey.shade600,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    PredictionResult.formatNumber(
                                        result.avgSimilarPrice!),
                                    style: TextStyle(
                                      fontSize: 14,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.teal.shade900,
                                    ),
                                    textAlign: TextAlign.center,
                                  ),
                                ],
                              ),
                            ),
                          if (result.minSimilarPrice != null)
                            Expanded(
                              child: Column(
                                children: [
                                  Icon(
                                    Icons.arrow_downward,
                                    color: Colors.blue.shade600,
                                    size: 24,
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    '최저',
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: Colors.grey.shade600,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    PredictionResult.formatNumber(
                                        result.minSimilarPrice!),
                                    style: TextStyle(
                                      fontSize: 14,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.blue.shade900,
                                    ),
                                    textAlign: TextAlign.center,
                                  ),
                                ],
                              ),
                            ),
                          if (result.maxSimilarPrice != null)
                            Expanded(
                              child: Column(
                                children: [
                                  Icon(
                                    Icons.arrow_upward,
                                    color: Colors.red.shade600,
                                    size: 24,
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    '최고',
                                    style: TextStyle(
                                      fontSize: 12,
                                      color: Colors.grey.shade600,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    PredictionResult.formatNumber(
                                        result.maxSimilarPrice!),
                                    style: TextStyle(
                                      fontSize: 14,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.red.shade900,
                                    ),
                                    textAlign: TextAlign.center,
                                  ),
                                ],
                              ),
                            ),
                        ],
                      ),
                    ),

                    // 비교 요약
                    if (result.comparisonSummary != null &&
                        result.comparisonSummary!.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.teal.shade50,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.teal.shade200),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              Icons.info_outline,
                              size: 20,
                              color: Colors.teal.shade700,
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                result.comparisonSummary!,
                                style: TextStyle(
                                  fontSize: 13,
                                  color: Colors.teal.shade900,
                                  height: 1.4,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],

                    // 유사 물건 목록
                    const SizedBox(height: 16),
                    ...result.similarProperties!
                        .take(5)
                        .map((property) => Container(
                              margin: const EdgeInsets.only(bottom: 12),
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(12),
                                border:
                                    Border.all(color: Colors.grey.shade300),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Expanded(
                                        child: Text(
                                          property.address,
                                          style: const TextStyle(
                                            fontSize: 14,
                                            fontWeight: FontWeight.bold,
                                          ),
                                          maxLines: 2,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                      ),
                                      const SizedBox(width: 8),
                                      Container(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 8,
                                          vertical: 4,
                                        ),
                                        decoration: BoxDecoration(
                                          color: property.similarityScore >= 80
                                              ? Colors.green.shade100
                                              : property.similarityScore >= 60
                                                  ? Colors.orange.shade100
                                                  : Colors.grey.shade100,
                                          borderRadius:
                                              BorderRadius.circular(8),
                                        ),
                                        child: Text(
                                          '${property.similarityScore}%',
                                          style: TextStyle(
                                            fontSize: 12,
                                            fontWeight: FontWeight.bold,
                                            color: property.similarityScore >= 80
                                                ? Colors.green.shade900
                                                : property.similarityScore >= 60
                                                    ? Colors.orange.shade900
                                                    : Colors.grey.shade900,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Row(
                                    children: [
                                      if (property.propertyType != null) ...[
                                        Icon(
                                          Icons.home,
                                          size: 14,
                                          color: Colors.grey.shade600,
                                        ),
                                        const SizedBox(width: 4),
                                        Text(
                                          property.propertyType!,
                                          style: TextStyle(
                                            fontSize: 12,
                                            color: Colors.grey.shade700,
                                          ),
                                        ),
                                        const SizedBox(width: 12),
                                      ],
                                      if (property.area != null) ...[
                                        Icon(
                                          Icons.square_foot,
                                          size: 14,
                                          color: Colors.grey.shade600,
                                        ),
                                        const SizedBox(width: 4),
                                        Text(
                                          '${property.area!.toStringAsFixed(1)}㎡',
                                          style: TextStyle(
                                            fontSize: 12,
                                            color: Colors.grey.shade700,
                                          ),
                                        ),
                                      ],
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Row(
                                    mainAxisAlignment:
                                        MainAxisAlignment.spaceBetween,
                                    children: [
                                      Text(
                                        '낙찰가',
                                        style: TextStyle(
                                          fontSize: 12,
                                          color: Colors.grey.shade600,
                                        ),
                                      ),
                                      Text(
                                        property.formattedWinningBid,
                                        style: TextStyle(
                                          fontSize: 15,
                                          fontWeight: FontWeight.bold,
                                          color: Colors.teal.shade900,
                                        ),
                                      ),
                                    ],
                                  ),
                                  if (property.auctionDate != null) ...[
                                    const SizedBox(height: 4),
                                    Text(
                                      '경매일: ${property.auctionDate}',
                                      style: TextStyle(
                                        fontSize: 11,
                                        color: Colors.grey.shade500,
                                      ),
                                    ),
                                  ],
                                ],
                              ),
                            )),
                    if (result.similarProperties!.length > 5)
                      Padding(
                        padding: const EdgeInsets.only(top: 8),
                        child: Center(
                          child: Text(
                            '외 ${result.similarProperties!.length - 5}건 더 있음',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey.shade600,
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ],

            // 리스크 분석
            if (result.riskScore != null) ...[
              const SizedBox(height: 20),
              Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      Colors.red.shade50,
                      Colors.orange.shade50,
                    ],
                  ),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: result.riskLevel == '높음'
                        ? Colors.red.shade300
                        : result.riskLevel == '중간'
                            ? Colors.orange.shade300
                            : Colors.green.shade300,
                    width: 2,
                  ),
                ),
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          Icons.warning_amber_rounded,
                          color: result.riskLevel == '높음'
                              ? Colors.red.shade700
                              : result.riskLevel == '중간'
                                  ? Colors.orange.shade700
                                  : Colors.green.shade700,
                          size: 24,
                        ),
                        const SizedBox(width: 8),
                        const Text(
                          '리스크 분석',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const Spacer(),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 6,
                          ),
                          decoration: BoxDecoration(
                            color: result.riskLevel == '높음'
                                ? Colors.red.shade100
                                : result.riskLevel == '중간'
                                    ? Colors.orange.shade100
                                    : Colors.green.shade100,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            '${result.riskLevel} 리스크',
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.bold,
                              color: result.riskLevel == '높음'
                                  ? Colors.red.shade900
                                  : result.riskLevel == '중간'
                                      ? Colors.orange.shade900
                                      : Colors.green.shade900,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),

                    // 리스크 점수 게이지
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.grey.shade300),
                      ),
                      child: Column(
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Text(
                                '종합 리스크 점수',
                                style: TextStyle(
                                  fontSize: 14,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              Text(
                                '${result.riskScore}/10',
                                style: TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.bold,
                                  color: result.riskScore! <= 3
                                      ? Colors.green.shade700
                                      : result.riskScore! <= 6
                                          ? Colors.orange.shade700
                                          : Colors.red.shade700,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Stack(
                            children: [
                              Container(
                                height: 12,
                                decoration: BoxDecoration(
                                  color: Colors.grey.shade200,
                                  borderRadius: BorderRadius.circular(6),
                                ),
                              ),
                              FractionallySizedBox(
                                widthFactor: result.riskScore! / 10,
                                child: Container(
                                  height: 12,
                                  decoration: BoxDecoration(
                                    gradient: LinearGradient(
                                      colors: [
                                        Colors.green,
                                        Colors.yellow,
                                        Colors.orange,
                                        Colors.red,
                                      ],
                                      stops: const [0.0, 0.3, 0.6, 1.0],
                                    ),
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                '안전',
                                style: TextStyle(
                                  fontSize: 11,
                                  color: Colors.grey.shade600,
                                ),
                              ),
                              Text(
                                '위험',
                                style: TextStyle(
                                  fontSize: 11,
                                  color: Colors.grey.shade600,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),

                    // 주요 리스크 요인
                    if (result.riskFactors != null &&
                        result.riskFactors!.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.red.shade50,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: Colors.red.shade200),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(
                                  Icons.error_outline,
                                  size: 18,
                                  color: Colors.red.shade700,
                                ),
                                const SizedBox(width: 6),
                                Text(
                                  '주요 리스크 요인',
                                  style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.red.shade900,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            ...result.riskFactors!.map((factor) => Padding(
                                  padding: const EdgeInsets.only(bottom: 8),
                                  child: Row(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Icon(
                                        Icons.warning,
                                        size: 16,
                                        color: Colors.red.shade600,
                                      ),
                                      const SizedBox(width: 8),
                                      Expanded(
                                        child: Text(
                                          factor,
                                          style: TextStyle(
                                            fontSize: 13,
                                            color: Colors.red.shade800,
                                            height: 1.4,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                )),
                          ],
                        ),
                      ),
                    ],

                    // 안전 요소
                    if (result.safetyFactors != null &&
                        result.safetyFactors!.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.green.shade50,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: Colors.green.shade200),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(
                                  Icons.check_circle_outline,
                                  size: 18,
                                  color: Colors.green.shade700,
                                ),
                                const SizedBox(width: 6),
                                Text(
                                  '안전 요소',
                                  style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.green.shade900,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            ...result.safetyFactors!.map((factor) => Padding(
                                  padding: const EdgeInsets.only(bottom: 8),
                                  child: Row(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Icon(
                                        Icons.check_circle,
                                        size: 16,
                                        color: Colors.green.shade600,
                                      ),
                                      const SizedBox(width: 8),
                                      Expanded(
                                        child: Text(
                                          factor,
                                          style: TextStyle(
                                            fontSize: 13,
                                            color: Colors.green.shade800,
                                            height: 1.4,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                )),
                          ],
                        ),
                      ),
                    ],

                    // 법률 자문 권장사항
                    if (result.legalAdvice != null &&
                        result.legalAdvice!.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.blue.shade50,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: Colors.blue.shade200),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Icon(
                              Icons.gavel,
                              size: 20,
                              color: Colors.blue.shade700,
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    '법률 자문 권장',
                                    style: TextStyle(
                                      fontSize: 14,
                                      fontWeight: FontWeight.bold,
                                      color: Colors.blue.shade900,
                                    ),
                                  ),
                                  const SizedBox(height: 6),
                                  Text(
                                    result.legalAdvice!,
                                    style: TextStyle(
                                      fontSize: 13,
                                      color: Colors.blue.shade800,
                                      height: 1.4,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],

            // 입찰 시뮬레이터
            if (result.bidSimulations != null &&
                result.bidSimulations!.isNotEmpty) ...[
              const SizedBox(height: 20),
              Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      Colors.amber.shade50,
                      Colors.orange.shade50,
                    ],
                  ),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: Colors.amber.shade400,
                    width: 2,
                  ),
                ),
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          Icons.calculate_outlined,
                          color: Colors.amber.shade800,
                          size: 24,
                        ),
                        const SizedBox(width: 8),
                        const Text(
                          '입찰 시뮬레이터',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    if (result.simulatorGuidance != null &&
                        result.simulatorGuidance!.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.amber.shade100,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.amber.shade300),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              Icons.info_outline,
                              size: 20,
                              color: Colors.amber.shade900,
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                result.simulatorGuidance!,
                                style: TextStyle(
                                  fontSize: 13,
                                  color: Colors.amber.shade900,
                                  height: 1.4,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                    const SizedBox(height: 16),

                    // 시뮬레이션 시나리오들
                    ...result.bidSimulations!.map((simulation) => Container(
                          margin: const EdgeInsets.only(bottom: 12),
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: simulation.winProbability >= 70
                                  ? Colors.green.shade300
                                  : simulation.winProbability >= 40
                                      ? Colors.orange.shade300
                                      : Colors.red.shade300,
                              width: 2,
                            ),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment:
                                    MainAxisAlignment.spaceBetween,
                                children: [
                                  Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        '만약 ${simulation.formattedBidAmount}에 입찰하면',
                                        style: const TextStyle(
                                          fontSize: 14,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        '예상 입찰자: ${simulation.estimatedBidders}명',
                                        style: TextStyle(
                                          fontSize: 12,
                                          color: Colors.grey.shade600,
                                        ),
                                      ),
                                    ],
                                  ),
                                  Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 12,
                                      vertical: 6,
                                    ),
                                    decoration: BoxDecoration(
                                      color: simulation.winProbability >= 70
                                          ? Colors.green.shade100
                                          : simulation.winProbability >= 40
                                              ? Colors.orange.shade100
                                              : Colors.red.shade100,
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    child: Column(
                                      children: [
                                        Text(
                                          '낙찰 확률',
                                          style: TextStyle(
                                            fontSize: 10,
                                            color: Colors.grey.shade700,
                                          ),
                                        ),
                                        Text(
                                          '${simulation.winProbability}%',
                                          style: TextStyle(
                                            fontSize: 18,
                                            fontWeight: FontWeight.bold,
                                            color:
                                                simulation.winProbability >= 70
                                                    ? Colors.green.shade900
                                                    : simulation
                                                                .winProbability >=
                                                            40
                                                        ? Colors
                                                            .orange.shade900
                                                        : Colors.red.shade900,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 12),
                              Container(
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: Colors.grey.shade50,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Row(
                                  mainAxisAlignment:
                                      MainAxisAlignment.spaceBetween,
                                  children: [
                                    Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          '예상 수익',
                                          style: TextStyle(
                                            fontSize: 12,
                                            color: Colors.grey.shade600,
                                          ),
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          simulation.formattedExpectedProfit,
                                          style: TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.bold,
                                            color:
                                                simulation.expectedProfit >= 0
                                                    ? Colors.blue.shade900
                                                    : Colors.red.shade900,
                                          ),
                                        ),
                                      ],
                                    ),
                                    Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.end,
                                      children: [
                                        Text(
                                          '수익률',
                                          style: TextStyle(
                                            fontSize: 12,
                                            color: Colors.grey.shade600,
                                          ),
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          '${simulation.profitRate > 0 ? '+' : ''}${simulation.profitRate.toStringAsFixed(1)}%',
                                          style: TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.bold,
                                            color: simulation.profitRate >= 0
                                                ? Colors.blue.shade900
                                                : Colors.red.shade900,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(height: 12),
                              Container(
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: simulation.winProbability >= 70
                                      ? Colors.green.shade50
                                      : simulation.winProbability >= 40
                                          ? Colors.orange.shade50
                                          : Colors.red.shade50,
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(
                                    color: simulation.winProbability >= 70
                                        ? Colors.green.shade200
                                        : simulation.winProbability >= 40
                                            ? Colors.orange.shade200
                                            : Colors.red.shade200,
                                  ),
                                ),
                                child: Row(
                                  children: [
                                    Icon(
                                      simulation.winProbability >= 70
                                          ? Icons.check_circle
                                          : simulation.winProbability >= 40
                                              ? Icons.warning_amber_rounded
                                              : Icons.cancel,
                                      size: 18,
                                      color: simulation.winProbability >= 70
                                          ? Colors.green.shade700
                                          : simulation.winProbability >= 40
                                              ? Colors.orange.shade700
                                              : Colors.red.shade700,
                                    ),
                                    const SizedBox(width: 8),
                                    Expanded(
                                      child: Text(
                                        simulation.recommendation,
                                        style: TextStyle(
                                          fontSize: 13,
                                          fontWeight: FontWeight.w500,
                                          color: simulation.winProbability >= 70
                                              ? Colors.green.shade900
                                              : simulation.winProbability >= 40
                                                  ? Colors.orange.shade900
                                                  : Colors.red.shade900,
                                          height: 1.3,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        )),
                  ],
                ),
              ),
            ],

            // 전문가 의견 (커뮤니티)
            if ((result.expertTips != null && result.expertTips!.isNotEmpty) || result.communityInsight != null) ...[
              const SizedBox(height: 20),
              Container(
                decoration: BoxDecoration(
                  gradient: LinearGradient(colors: [Colors.deepPurple.shade50, Colors.purple.shade50]),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.deepPurple.shade300, width: 2),
                ),
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.people, color: Colors.deepPurple.shade700, size: 24),
                        const SizedBox(width: 8),
                        const Text('전문가 의견 및 커뮤니티', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      ],
                    ),
                    if (result.expertTips != null && result.expertTips!.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      const Text('전문가 조언', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 12),
                      ...result.expertTips!.map((tip) => Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(8), border: Border.all(color: Colors.deepPurple.shade200)),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Icon(Icons.lightbulb, size: 18, color: Colors.deepPurple.shade600),
                            const SizedBox(width: 8),
                            Expanded(child: Text(tip, style: const TextStyle(fontSize: 13, height: 1.4))),
                          ],
                        ),
                      )),
                    ],
                    if (result.communityInsight != null) ...[
                      const SizedBox(height: 16),
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(color: Colors.deepPurple.shade100, borderRadius: BorderRadius.circular(12)),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(Icons.forum, size: 20, color: Colors.deepPurple.shade700),
                                const SizedBox(width: 8),
                                const Text('커뮤니티 인사이트', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(result.communityInsight!, style: TextStyle(fontSize: 13, color: Colors.deepPurple.shade900, height: 1.4)),
                            if (result.similarCaseDiscussions != null) ...[
                              const SizedBox(height: 8),
                              Text('유사 사례 토론 ${result.similarCaseDiscussions}건', style: TextStyle(fontSize: 12, color: Colors.deepPurple.shade700)),
                            ],
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],

            // AI 예측 신뢰도
            if (result.confidenceScore != null) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.blue[50],
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.blue[200]!),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.verified, color: Colors.blue[700], size: 20),
                        const SizedBox(width: 8),
                        const Text(
                          'AI 예측 신뢰도',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const Spacer(),
                        // 별점 표시
                        if (result.confidenceStars != null) ...[
                          Row(
                            children: List.generate(5, (index) {
                              return Icon(
                                index < result.confidenceStars!
                                    ? Icons.star
                                    : Icons.star_border,
                                color: Colors.amber[700],
                                size: 18,
                              );
                            }),
                          ),
                        ],
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '${result.confidenceScore}%',
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.blue[900],
                      ),
                    ),

                    // 신뢰도 높은 이유
                    if (result.confidenceReasons != null && result.confidenceReasons!.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Text(
                        '높은 신뢰도 이유:',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                          color: Colors.grey[800],
                        ),
                      ),
                      const SizedBox(height: 6),
                      ...result.confidenceReasons!.map((reason) => Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Icon(Icons.check, color: Colors.green[700], size: 16),
                            const SizedBox(width: 6),
                            Expanded(
                              child: Text(
                                reason,
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Colors.grey[700],
                                ),
                              ),
                            ),
                          ],
                        ),
                      )),
                    ],

                    // 주의사항
                    if (result.confidenceWarnings != null && result.confidenceWarnings!.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: Colors.orange[50],
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(Icons.warning_amber, color: Colors.orange[700], size: 16),
                                const SizedBox(width: 6),
                                Text(
                                  '주의사항:',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.orange[900],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 6),
                            ...result.confidenceWarnings!.map((warning) => Padding(
                              padding: const EdgeInsets.only(bottom: 2),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('• ', style: TextStyle(color: Colors.orange[800])),
                                  Expanded(
                                    child: Text(
                                      warning,
                                      style: TextStyle(
                                        fontSize: 11,
                                        color: Colors.orange[800],
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            )),
                          ],
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildFeedbackButton(String label, IconData icon, Color color) {
    return Column(
      children: [
        IconButton(
          icon: Icon(icon, size: 32),
          color: color,
          onPressed: () {
            // TODO: Send feedback to server
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('피드백 감사합니다!')),
            );
          },
        ),
        Text(label, style: TextStyle(fontSize: 10, color: color), textAlign: TextAlign.center),
      ],
    );
  }

  Widget _buildInfoItem(String label, String value, IconData icon, Color color) {
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
}
