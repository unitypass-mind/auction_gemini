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
          ],
        ),
      ),
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
