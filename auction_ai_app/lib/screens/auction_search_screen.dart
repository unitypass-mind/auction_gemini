import 'package:flutter/material.dart';
import '../services/api_service.dart';

/// 경매 물건 상세 검색 화면
///
/// 주소, 가격대, 면적 등 다양한 필터로 경매 물건을 검색할 수 있는 전용 화면
class AuctionSearchScreen extends StatefulWidget {
  const AuctionSearchScreen({super.key});

  @override
  State<AuctionSearchScreen> createState() => _AuctionSearchScreenState();
}

class _AuctionSearchScreenState extends State<AuctionSearchScreen> {
  final ApiService _apiService = ApiService();
  final _addressController = TextEditingController();

  // 검색 상태
  bool _isSearching = false;
  List<dynamic> _searchResults = [];
  String? _searchError;

  // 가격/면적 섹션 펼침 상태
  bool _isPriceAreaExpanded = false;

  // 경매 상태 필터
  String? _selectedStatus;

  // 가격 범위 (단위: 억원, 0 = 무제한)
  RangeValues _priceRange = const RangeValues(0, 40);

  // 면적 범위 (단위: 평, 0 = 무제한)
  RangeValues _areaRange = const RangeValues(0, 200);

  @override
  void dispose() {
    _addressController.dispose();
    super.dispose();
  }

  /// 검색 실행
  Future<void> _performSearch() async {
    setState(() {
      _isSearching = true;
      _searchError = null;
      _searchResults = [];
    });

    try {
      // 검색 파라미터 구성
      final query = _addressController.text.trim();

      // 가격 범위 변환 (억원 -> 원)
      int? minPrice;
      int? maxPrice;
      if (_priceRange.start > 0) {
        minPrice = (_priceRange.start * 100000000).toInt();
      }
      if (_priceRange.end < 40) {
        maxPrice = (_priceRange.end * 100000000).toInt();
      }

      // 면적 범위 변환 (평 -> ㎡)
      double? minArea;
      double? maxArea;
      if (_areaRange.start > 0) {
        minArea = _areaRange.start * 3.30579; // 1평 = 3.30579㎡
      }
      if (_areaRange.end < 200) {
        maxArea = _areaRange.end * 3.30579;
      }

      final response = await _apiService.searchAuctions(
        region: query.isNotEmpty ? query : null,
        minPrice: minPrice,
        maxPrice: maxPrice,
        minArea: minArea,
        maxArea: maxArea,
        status: _selectedStatus,
      );

      setState(() {
        if (response['success'] == true) {
          _searchResults = response['items'] ?? [];
          if (_searchResults.isEmpty) {
            _searchError = '검색 결과가 없습니다';
          }
        } else {
          _searchError = response['message'] ?? '검색에 실패했습니다';
        }
        _isSearching = false;
      });
    } catch (e) {
      setState(() {
        _searchError = e.toString();
        _isSearching = false;
      });
    }
  }

  /// 검색 조건 초기화
  void _resetFilters() {
    setState(() {
      _addressController.clear();
      _selectedStatus = null;
      _priceRange = const RangeValues(0, 40);
      _areaRange = const RangeValues(0, 200);
      _searchResults = [];
      _searchError = null;
    });
  }

  /// 가격 레이블 포맷 (억원 단위)
  String _formatPriceLabel(double value) {
    if (value == 0) {
      return '최저 입찰가';
    } else if (value >= 40) {
      return '무제한';
    } else {
      return '${value.toInt()}억';
    }
  }

  /// 면적 레이블 포맷 (평 단위)
  String _formatAreaLabel(double value) {
    if (value == 0) {
      return '0평';
    } else if (value >= 200) {
      return '무제한';
    } else {
      return '${value.toInt()}평';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text(
          '경매 물건 검색',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w600,
          ),
        ),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black87),
      ),
      body: Column(
        children: [
          // 검색 필터 섹션
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 주소로 찾기 섹션
                  Container(
                    width: double.infinity,
                    color: Colors.white,
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          '주소로 찾기',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            color: Colors.black87,
                          ),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _addressController,
                          decoration: InputDecoration(
                            hintText: '주소를 선택해주세요',
                            hintStyle: TextStyle(
                              color: Colors.grey[400],
                              fontSize: 14,
                            ),
                            filled: true,
                            fillColor: Colors.grey[50],
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(8),
                              borderSide: BorderSide(color: Colors.grey[300]!),
                            ),
                            enabledBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(8),
                              borderSide: BorderSide(color: Colors.grey[300]!),
                            ),
                            focusedBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(8),
                              borderSide: const BorderSide(
                                color: Color(0xFF4CAF50),
                                width: 2,
                              ),
                            ),
                            contentPadding: const EdgeInsets.symmetric(
                              horizontal: 16,
                              vertical: 14,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 8),

                  // 경매 상태 섹션
                  Container(
                    width: double.infinity,
                    color: Colors.white,
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          '경매 상태',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            color: Colors.black87,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Expanded(
                              child: _buildStatusButton('전체'),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: _buildStatusButton('경매중'),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: _buildStatusButton('입찰완료'),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 8),

                  // 가격/면적 섹션 (펼치기/접기 가능)
                  Container(
                    width: double.infinity,
                    color: Colors.white,
                    child: Column(
                      children: [
                        InkWell(
                          onTap: () {
                            setState(() {
                              _isPriceAreaExpanded = !_isPriceAreaExpanded;
                            });
                          },
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text(
                                  '가격/면적',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w600,
                                    color: Colors.black87,
                                  ),
                                ),
                                Icon(
                                  _isPriceAreaExpanded
                                      ? Icons.keyboard_arrow_up
                                      : Icons.keyboard_arrow_down,
                                  color: Colors.grey[600],
                                ),
                              ],
                            ),
                          ),
                        ),
                        if (_isPriceAreaExpanded) ...[
                          const Divider(height: 1),
                          Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                // 가격 슬라이더
                                const Text(
                                  '가격',
                                  style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.w500,
                                    color: Colors.black87,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      _formatPriceLabel(_priceRange.start),
                                      style: TextStyle(
                                        fontSize: 13,
                                        color: Colors.grey[700],
                                      ),
                                    ),
                                    Text(
                                      '~',
                                      style: TextStyle(
                                        fontSize: 13,
                                        color: Colors.grey[500],
                                      ),
                                    ),
                                    Text(
                                      _formatPriceLabel(_priceRange.end),
                                      style: TextStyle(
                                        fontSize: 13,
                                        color: Colors.grey[700],
                                      ),
                                    ),
                                  ],
                                ),
                                RangeSlider(
                                  values: _priceRange,
                                  min: 0,
                                  max: 40,
                                  divisions: 40,
                                  activeColor: const Color(0xFF4CAF50),
                                  inactiveColor: Colors.grey[300],
                                  onChanged: (RangeValues values) {
                                    setState(() {
                                      _priceRange = values;
                                    });
                                  },
                                ),
                                const SizedBox(height: 16),

                                // 면적 슬라이더
                                const Text(
                                  '면적',
                                  style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.w500,
                                    color: Colors.black87,
                                  ),
                                ),
                                const SizedBox(height: 8),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      _formatAreaLabel(_areaRange.start),
                                      style: TextStyle(
                                        fontSize: 13,
                                        color: Colors.grey[700],
                                      ),
                                    ),
                                    Text(
                                      '~',
                                      style: TextStyle(
                                        fontSize: 13,
                                        color: Colors.grey[500],
                                      ),
                                    ),
                                    Text(
                                      _formatAreaLabel(_areaRange.end),
                                      style: TextStyle(
                                        fontSize: 13,
                                        color: Colors.grey[700],
                                      ),
                                    ),
                                  ],
                                ),
                                RangeSlider(
                                  values: _areaRange,
                                  min: 0,
                                  max: 200,
                                  divisions: 40,
                                  activeColor: const Color(0xFF4CAF50),
                                  inactiveColor: Colors.grey[300],
                                  onChanged: (RangeValues values) {
                                    setState(() {
                                      _areaRange = values;
                                    });
                                  },
                                ),
                              ],
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),

                  const SizedBox(height: 8),

                  // 검색 결과 섹션
                  if (_isSearching)
                    Container(
                      padding: const EdgeInsets.all(32),
                      child: const Center(
                        child: CircularProgressIndicator(
                          color: Color(0xFF4CAF50),
                        ),
                      ),
                    )
                  else if (_searchError != null)
                    Container(
                      padding: const EdgeInsets.all(16),
                      child: Center(
                        child: Text(
                          _searchError!,
                          style: TextStyle(
                            color: Colors.grey[600],
                            fontSize: 14,
                          ),
                        ),
                      ),
                    )
                  else if (_searchResults.isNotEmpty)
                    Container(
                      color: Colors.white,
                      child: ListView.separated(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: _searchResults.length,
                        separatorBuilder: (context, index) => const Divider(
                          height: 1,
                          indent: 16,
                          endIndent: 16,
                        ),
                        itemBuilder: (context, index) {
                          final item = _searchResults[index];
                          return InkWell(
                            onTap: () {
                              // 결과 선택 시 사건번호를 반환하고 화면 닫기
                              final caseNo = item['case_no'] as String?;
                              if (caseNo != null) {
                                Navigator.of(context).pop(caseNo);
                              }
                            },
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    item['case_no'] ?? '사건번호 없음',
                                    style: const TextStyle(
                                      fontSize: 15,
                                      fontWeight: FontWeight.w600,
                                      color: Colors.black87,
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  Row(
                                    children: [
                                      if (item['물건종류'] != null) ...[
                                        _buildInfoChip(
                                          item['물건종류'],
                                          Colors.blue[50]!,
                                          Colors.blue[700]!,
                                        ),
                                        const SizedBox(width: 6),
                                      ],
                                      if (item['지역'] != null)
                                        _buildInfoChip(
                                          item['지역'],
                                          Colors.green[50]!,
                                          Colors.green[700]!,
                                        ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      if (item['감정가_formatted'] != null)
                                        Text(
                                          '감정가: ${item['감정가_formatted']}',
                                          style: TextStyle(
                                            fontSize: 13,
                                            color: Colors.grey[700],
                                          ),
                                        ),
                                      if (item['면적'] != null)
                                        Text(
                                          _formatAreaDisplay(item['면적']),
                                          style: TextStyle(
                                            fontSize: 13,
                                            color: Colors.grey[700],
                                          ),
                                        ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                ],
              ),
            ),
          ),

          // 하단 버튼 영역
          Container(
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 4,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            padding: const EdgeInsets.all(16),
            child: SafeArea(
              child: Row(
                children: [
                  // 초기화 버튼
                  Expanded(
                    child: OutlinedButton(
                      onPressed: _resetFilters,
                      style: OutlinedButton.styleFrom(
                        side: BorderSide(color: Colors.grey[300]!),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                      child: const Text(
                        '초기화',
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                          color: Colors.black87,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  // 검색하기 버튼
                  Expanded(
                    flex: 2,
                    child: ElevatedButton(
                      onPressed: _isSearching ? null : _performSearch,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF4CAF50),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                        elevation: 0,
                      ),
                      child: const Text(
                        '검색하기',
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  /// 정보 칩 위젯 빌더
  Widget _buildInfoChip(String label, Color bgColor, Color textColor) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w500,
          color: textColor,
        ),
      ),
    );
  }

  /// 면적 표시 포맷 (㎡를 평으로 변환하여 함께 표시)
  String _formatAreaDisplay(dynamic area) {
    if (area == null) return '';

    // 문자열로 변환
    final areaStr = area.toString();

    // "61.32㎡" 형식에서 숫자 추출
    final match = RegExp(r'([\d.]+)').firstMatch(areaStr);
    if (match == null) return areaStr;

    final sqm = double.tryParse(match.group(1) ?? '0');
    if (sqm == null || sqm == 0) return areaStr;

    // 제곱미터를 평으로 변환 (1평 = 3.30579㎡)
    final pyeong = sqm / 3.30579;

    return '$areaStr (${pyeong.toStringAsFixed(0)}평)';
  }

  /// 경매 상태 버튼 빌더
  Widget _buildStatusButton(String status) {
    final isSelected = _selectedStatus == status;

    return OutlinedButton(
      onPressed: () {
        setState(() {
          // 같은 버튼을 다시 누르면 선택 해제
          if (_selectedStatus == status) {
            _selectedStatus = null;
          } else {
            _selectedStatus = status;
          }
        });
      },
      style: OutlinedButton.styleFrom(
        backgroundColor: isSelected ? const Color(0xFF4CAF50) : Colors.white,
        foregroundColor: isSelected ? Colors.white : Colors.black87,
        side: BorderSide(
          color: isSelected ? const Color(0xFF4CAF50) : Colors.grey[300]!,
          width: isSelected ? 2 : 1,
        ),
        padding: const EdgeInsets.symmetric(vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
        ),
      ),
      child: Text(
        status,
        style: TextStyle(
          fontSize: 14,
          fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
        ),
      ),
    );
  }
}
