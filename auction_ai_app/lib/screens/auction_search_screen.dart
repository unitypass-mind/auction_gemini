import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/api_service.dart';
import 'home_screen.dart';

/// 경매 물건 상세 검색 화면
class AuctionSearchScreen extends StatefulWidget {
  const AuctionSearchScreen({super.key});

  @override
  State<AuctionSearchScreen> createState() => _AuctionSearchScreenState();
}

class _AuctionSearchScreenState extends State<AuctionSearchScreen> {
  final ApiService _apiService = ApiService();
  final _addressController = TextEditingController();
  final _scrollController = ScrollController();

  // 검색 상태
  bool _isSearching = false;
  List<dynamic> _searchResults = [];
  String? _searchError;

  // 페이지네이션
  int _currentPage = 0;
  final int _itemsPerPage = 10;
  int _totalCount = 0;

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
    _scrollController.dispose();
    super.dispose();
  }

  /// 검색 실행
  Future<void> _performSearch({int page = 0}) async {
    setState(() {
      _isSearching = true;
      _searchError = null;
      if (page == 0) {
        _searchResults = [];
      }
    });

    try {
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
        minArea = _areaRange.start * 3.30579;
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
          final allResults = response['items'] ?? [];
          _totalCount = allResults.length;

          // 페이지네이션 적용
          final startIndex = page * _itemsPerPage;
          final endIndex = (startIndex + _itemsPerPage).clamp(0, _totalCount);
          _searchResults = allResults.sublist(startIndex, endIndex);
          _currentPage = page;

          if (_totalCount == 0) {
            _searchError = '검색 결과가 없습니다';
          }
        } else {
          _searchError = response['message'] ?? '검색에 실패했습니다';
        }
        _isSearching = false;
      });

      // 페이지 변경 시 스크롤을 맨 위로
      if (page > 0 && _scrollController.hasClients) {
        _scrollController.animateTo(
          0,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    } catch (e) {
      setState(() {
        _searchError = '검색 중 오류가 발생했습니다: ${e.toString()}';
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
      _currentPage = 0;
      _totalCount = 0;
    });
  }

  /// 물건 상세 보기
  void _viewAuctionDetail(String? caseNo) {
    if (caseNo == null) return;
    Navigator.of(context).popUntil((route) => route.isFirst);
    HomeScreen.globalKey.currentState?.switchTab(0, autoSearchCaseNumber: caseNo);
  }

  /// 가격 포맷팅 (억/만 단위)
  String _formatPrice(dynamic price) {
    if (price == null || price == 0) return '-';
    try {
      final intPrice = price is int ? price : int.parse(price.toString());
      final 억 = (intPrice / 100000000).floor();
      final 만 = ((intPrice % 100000000) / 10000).floor();

      if (억 > 0 && 만 > 0) {
        return '$억억 ${만}만원';
      } else if (억 > 0) {
        return '$억억원';
      } else if (만 > 0) {
        return '${만}만원';
      } else {
        final formatter = NumberFormat('#,###');
        return '${formatter.format(intPrice)}원';
      }
    } catch (e) {
      return price.toString();
    }
  }

  /// 날짜 포맷팅 (YYYYMMDD -> YYYY-MM-DD)
  String _formatDate(String? dateStr) {
    if (dateStr == null || dateStr.length != 8) return '-';
    try {
      return '${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}';
    } catch (e) {
      return dateStr;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: const Text(
          '경매 물건 검색',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
        ),
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.black87),
      ),
      body: Column(
        children: [
          _buildFilters(),
          Expanded(child: _buildResultsTable()),
          _buildBottomButtons(),
        ],
      ),
    );
  }

  /// 검색 필터 UI
  Widget _buildFilters() {
    return SingleChildScrollView(
      child: Column(
        children: [
          // 주소로 찾기
          Container(
            color: Colors.white,
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('주소로 찾기',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                const SizedBox(height: 12),
                TextField(
                  controller: _addressController,
                  decoration: InputDecoration(
                    hintText: '예: 인천, 서울 강남구, 부평동',
                    hintStyle: TextStyle(color: Colors.grey[400], fontSize: 14),
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
                      borderSide: const BorderSide(color: Color(0xFF4CAF50), width: 2),
                    ),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                  ),
                  onSubmitted: (_) => _performSearch(),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),

          // 경매 상태
          Container(
            color: Colors.white,
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('경매 상태',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(child: _buildStatusButton('전체')),
                    const SizedBox(width: 8),
                    Expanded(child: _buildStatusButton('경매중')),
                    const SizedBox(width: 8),
                    Expanded(child: _buildStatusButton('입찰완료')),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),

          // 가격/면적 (접기/펼치기)
          Container(
            color: Colors.white,
            child: Column(
              children: [
                InkWell(
                  onTap: () => setState(() => _isPriceAreaExpanded = !_isPriceAreaExpanded),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('가격/면적',
                            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                        Icon(_isPriceAreaExpanded
                            ? Icons.keyboard_arrow_up
                            : Icons.keyboard_arrow_down,
                            color: Colors.grey[600]),
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
                        const Text('가격', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500)),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(_formatPriceLabel(_priceRange.start),
                                style: TextStyle(fontSize: 13, color: Colors.grey[700])),
                            Text('~', style: TextStyle(fontSize: 13, color: Colors.grey[500])),
                            Text(_formatPriceLabel(_priceRange.end),
                                style: TextStyle(fontSize: 13, color: Colors.grey[700])),
                          ],
                        ),
                        RangeSlider(
                          values: _priceRange,
                          min: 0,
                          max: 40,
                          divisions: 40,
                          activeColor: const Color(0xFF4CAF50),
                          onChanged: (values) => setState(() => _priceRange = values),
                        ),
                        const SizedBox(height: 16),
                        const Text('면적', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500)),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(_formatAreaLabel(_areaRange.start),
                                style: TextStyle(fontSize: 13, color: Colors.grey[700])),
                            Text('~', style: TextStyle(fontSize: 13, color: Colors.grey[500])),
                            Text(_formatAreaLabel(_areaRange.end),
                                style: TextStyle(fontSize: 13, color: Colors.grey[700])),
                          ],
                        ),
                        RangeSlider(
                          values: _areaRange,
                          min: 0,
                          max: 200,
                          divisions: 40,
                          activeColor: const Color(0xFF4CAF50),
                          onChanged: (values) => setState(() => _areaRange = values),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _formatPriceLabel(double value) {
    if (value == 0) return '최저 입찰가';
    if (value >= 40) return '무제한';
    return '${value.toInt()}억';
  }

  String _formatAreaLabel(double value) {
    if (value == 0) return '0평';
    if (value >= 200) return '무제한';
    return '${value.toInt()}평';
  }

  /// 검색 결과 테이블
  Widget _buildResultsTable() {
    if (_isSearching) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF4CAF50)));
    }

    if (_searchError != null) {
      return Center(
          child: Text(_searchError!,
              style: TextStyle(color: Colors.grey[600], fontSize: 14)));
    }

    if (_searchResults.isEmpty) {
      return Center(
          child: Text('검색 버튼을 눌러 경매 물건을 검색하세요',
              style: TextStyle(color: Colors.grey[600], fontSize: 14)));
    }

    final totalPages = (_totalCount / _itemsPerPage).ceil();

    return Container(
      color: Colors.white,
      child: Column(
        children: [
          // 결과 개수
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: Colors.grey[100],
              border: Border(bottom: BorderSide(color: Colors.grey[300]!)),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('검색 결과: $_totalCount건',
                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                if (totalPages > 1)
                  Text('${_currentPage + 1} / $totalPages 페이지',
                      style: TextStyle(fontSize: 13, color: Colors.grey[700])),
              ],
            ),
          ),

          // 테이블 헤더
          Container(
            decoration: BoxDecoration(
              color: Colors.grey[200],
              border: Border(bottom: BorderSide(color: Colors.grey[400]!, width: 2)),
            ),
            child: Row(
              children: [
                _buildHeaderCell('용도/사건번호', flex: 3),
                _buildHeaderCell('소재지', flex: 4),
                _buildHeaderCell('가격', flex: 2),
                _buildHeaderCell('진행상태', flex: 2),
                _buildHeaderCell('매각기일', flex: 2),
              ],
            ),
          ),

          // 테이블 본문
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              itemCount: _searchResults.length,
              itemBuilder: (context, index) {
                final item = _searchResults[index];
                return _buildTableRow(item);
              },
            ),
          ),

          // 페이지네이션
          if (totalPages > 1) _buildPagination(totalPages),
        ],
      ),
    );
  }

  Widget _buildHeaderCell(String text, {int flex = 1}) {
    return Expanded(
      flex: flex,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 12),
        child: Text(text,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
            textAlign: TextAlign.center),
      ),
    );
  }

  Widget _buildTableRow(Map<String, dynamic> item) {
    return InkWell(
      onTap: () => _viewAuctionDetail(item['case_no']),
      child: Container(
        decoration: BoxDecoration(
          border: Border(bottom: BorderSide(color: Colors.grey[300]!)),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 12),
        child: Row(
          children: [
            // 용도/사건번호
            Expanded(
              flex: 3,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item['물건종류'] ?? '-',
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w500, color: Colors.blue),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    item['사건번호'] ?? item['case_no'] ?? '-',
                    style: const TextStyle(fontSize: 10, color: Colors.black87),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),

            // 소재지
            Expanded(
              flex: 4,
              child: Text(
                item['소재지'] ?? '-',
                style: const TextStyle(fontSize: 11),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ),

            // 가격
            Expanded(
              flex: 2,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('감정가', style: TextStyle(fontSize: 9, color: Colors.grey[600])),
                  Text(_formatPrice(item['감정가']),
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w500),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis),
                  if (item['최저입찰가'] != null) ...[
                    const SizedBox(height: 2),
                    Text('최저가', style: TextStyle(fontSize: 9, color: Colors.grey[600])),
                    Text(_formatPrice(item['최저입찰가']),
                        style: const TextStyle(fontSize: 11, color: Color(0xFF4CAF50)),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis),
                  ],
                ],
              ),
            ),

            // 진행상태
            Expanded(
              flex: 2,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                decoration: BoxDecoration(
                  color: item['auction_status'] == '경매중' ? Colors.green[50] : Colors.grey[200],
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  item['auction_status'] == '입찰완료'
                      ? '유찰 ${item['경매회차'] ?? 0}회'
                      : '경매중',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: item['auction_status'] == '경매중' ? Colors.green[700] : Colors.grey[700],
                  ),
                  textAlign: TextAlign.center,
                  maxLines: 1,
                ),
              ),
            ),

            // 매각기일
            Expanded(
              flex: 2,
              child: Text(
                _formatDate(item['bidding_date']),
                style: const TextStyle(fontSize: 11),
                textAlign: TextAlign.center,
              ),
            ),
          ],
        ),
      ),
    );
  }

  /// 페이지네이션
  Widget _buildPagination(int totalPages) {
    return Container(
      decoration: BoxDecoration(
        border: Border(top: BorderSide(color: Colors.grey[300]!)),
      ),
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          IconButton(
            onPressed: _currentPage > 0 ? () => _performSearch(page: _currentPage - 1) : null,
            icon: const Icon(Icons.chevron_left),
            color: const Color(0xFF4CAF50),
            disabledColor: Colors.grey[400],
          ),
          ...List.generate(totalPages, (index) {
            if ((index - _currentPage).abs() > 2 && index != 0 && index != totalPages - 1) {
              if (index == 1 || index == totalPages - 2) {
                return const Padding(padding: EdgeInsets.symmetric(horizontal: 4), child: Text('...'));
              }
              return const SizedBox.shrink();
            }
            final isCurrentPage = index == _currentPage;
            return Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4),
              child: InkWell(
                onTap: isCurrentPage ? null : () => _performSearch(page: index),
                child: Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: isCurrentPage ? const Color(0xFF4CAF50) : Colors.white,
                    border: Border.all(
                        color: isCurrentPage ? const Color(0xFF4CAF50) : Colors.grey[300]!),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  alignment: Alignment.center,
                  child: Text('${index + 1}',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: isCurrentPage ? FontWeight.w600 : FontWeight.normal,
                        color: isCurrentPage ? Colors.white : Colors.black87,
                      )),
                ),
              ),
            );
          }),
          IconButton(
            onPressed: _currentPage < totalPages - 1
                ? () => _performSearch(page: _currentPage + 1)
                : null,
            icon: const Icon(Icons.chevron_right),
            color: const Color(0xFF4CAF50),
            disabledColor: Colors.grey[400],
          ),
        ],
      ),
    );
  }

  /// 하단 버튼
  Widget _buildBottomButtons() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 4, offset: const Offset(0, -2)),
        ],
      ),
      padding: const EdgeInsets.all(16),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: _resetFilters,
                style: OutlinedButton.styleFrom(
                  side: BorderSide(color: Colors.grey[300]!),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
                child: const Text('초기화',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: Colors.black87)),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              flex: 2,
              child: ElevatedButton(
                onPressed: _isSearching ? null : () => _performSearch(page: 0),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF4CAF50),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  elevation: 0,
                ),
                child: const Text('검색하기',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: Colors.white)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusButton(String status) {
    final isSelected = _selectedStatus == status;
    return OutlinedButton(
      onPressed: () {
        setState(() {
          _selectedStatus = _selectedStatus == status ? null : status;
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
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
      child: Text(status,
          style: TextStyle(fontSize: 14, fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500)),
    );
  }
}
