/// 데이터 모델 클래스들
/// API 응답을 Dart 객체로 변환

// ========================================
// 경매 물건 모델
// ========================================

class AuctionItem {
  final String caseNumber;
  final String? itemNumber;
  final int startPrice;
  final String? propertyType;
  final String? region;
  final double? area;
  final int auctionRound;
  final int? bidderCount;
  final String? status;
  final DateTime? auctionDate;
  final String? court;
  final String? address;

  AuctionItem({
    required this.caseNumber,
    this.itemNumber,
    required this.startPrice,
    this.propertyType,
    this.region,
    this.area,
    required this.auctionRound,
    this.bidderCount,
    this.status,
    this.auctionDate,
    this.court,
    this.address,
  });

  factory AuctionItem.fromJson(Map<String, dynamic> json) {
    return AuctionItem(
      caseNumber: json['case_number'] ?? json['사건번호'] ?? '',
      itemNumber: json['item_number'] ?? json['물건번호'],
      startPrice: json['start_price'] ?? json['감정가'] ?? 0,
      propertyType: json['property_type'] ?? json['물건종류'],
      region: json['region'] ?? json['지역'],
      area: (json['area'] ?? json['면적'])?.toDouble(),
      auctionRound: json['auction_round'] ?? json['경매회차'] ?? 1,
      bidderCount: json['bidder_count'] ?? json['입찰자수'],
      status: json['status'] ?? json['상태'],
      auctionDate: json['auction_date'] != null
          ? DateTime.parse(json['auction_date'])
          : null,
      court: json['court'] ?? json['법원'],
      address: json['address'] ?? json['소재지'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'case_number': caseNumber,
      'item_number': itemNumber,
      'start_price': startPrice,
      'property_type': propertyType,
      'region': region,
      'area': area,
      'auction_round': auctionRound,
      'bidder_count': bidderCount,
      'status': status,
      'auction_date': auctionDate?.toIso8601String(),
      'court': court,
      'address': address,
    };
  }
}

// ========================================
// AI 예측 결과 모델
// ========================================

class PredictionResult {
  final int startPrice;
  final int predictedPrice;
  final int expectedProfit;
  final double profitRate;
  final String? propertyType;
  final String? region;
  final double? area;
  final int auctionRound;
  final bool modelUsed;
  final String? predictionMode;
  final int? featuresCount;
  final String? warning;

  PredictionResult({
    required this.startPrice,
    required this.predictedPrice,
    required this.expectedProfit,
    required this.profitRate,
    this.propertyType,
    this.region,
    this.area,
    required this.auctionRound,
    required this.modelUsed,
    this.predictionMode,
    this.featuresCount,
    this.warning,
  });

  factory PredictionResult.fromJson(Map<String, dynamic> json) {
    return PredictionResult(
      startPrice: json['start_price'] ?? json['감정가'] ?? 0,
      predictedPrice: json['predicted_price'] ?? json['예측가'] ?? 0,
      expectedProfit: json['expected_profit'] ?? json['예상수익'] ?? 0,
      profitRate: (json['profit_rate'] ?? json['수익률'] ?? 0).toDouble(),
      propertyType: json['property_type'] ?? json['물건종류'],
      region: json['region'] ?? json['지역'],
      area: (json['area'] ?? json['면적'])?.toDouble(),
      auctionRound: json['auction_round'] ?? json['경매회차'] ?? 1,
      modelUsed: json['model_used'] ?? false,
      predictionMode: json['prediction_mode'],
      featuresCount: json['features_count'],
      warning: json['warning'],
    );
  }

  String get formattedPredictedPrice =>
      '${_formatNumber(predictedPrice)}원';

  String get formattedExpectedProfit =>
      '${_formatNumber(expectedProfit)}원';

  String get formattedProfitRate =>
      '${profitRate.toStringAsFixed(1)}%';

  static String _formatNumber(int number) {
    if (number >= 100000000) {
      final eok = number ~/ 100000000;
      final man = (number % 100000000) ~/ 10000;
      if (man > 0) {
        return '$eok억 ${man}만';
      }
      return '$eok억';
    } else if (number >= 10000) {
      return '${number ~/ 10000}만';
    }
    return number.toString();
  }
}

// ========================================
// 사용자 모델
// ========================================

class User {
  final int id;
  final String email;
  final String name;
  final DateTime createdAt;

  User({
    required this.id,
    required this.email,
    required this.name,
    required this.createdAt,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] ?? 0,
      email: json['email'] ?? '',
      name: json['name'] ?? '',  // null일 경우 빈 문자열 사용
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'])
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'name': name,
      'created_at': createdAt.toIso8601String(),
    };
  }
}

// ========================================
// 경매 구독 모델
// ========================================

class AuctionSubscription {
  final int id;
  final String caseNumber;
  final bool priceDropAlert;
  final bool bidReminderAlert;
  final DateTime createdAt;
  final AuctionItem? auctionItem;

  AuctionSubscription({
    required this.id,
    required this.caseNumber,
    required this.priceDropAlert,
    required this.bidReminderAlert,
    required this.createdAt,
    this.auctionItem,
  });

  factory AuctionSubscription.fromJson(Map<String, dynamic> json) {
    return AuctionSubscription(
      id: json['id'],
      caseNumber: json['case_number'],
      priceDropAlert: json['price_drop_alert'] ?? false,
      bidReminderAlert: json['bid_reminder_alert'] ?? false,
      createdAt: DateTime.parse(json['created_at']),
      auctionItem: json['auction_item'] != null
          ? AuctionItem.fromJson(json['auction_item'])
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'case_number': caseNumber,
      'price_drop_alert': priceDropAlert,
      'bid_reminder_alert': bidReminderAlert,
      'created_at': createdAt.toIso8601String(),
    };
  }
}

// ========================================
// 통계 모델
// ========================================

class AccuracyStats {
  final int totalPredictions;
  final int verifiedPredictions;
  final double avgErrorRate;
  final List<VerifiedPrediction> recentVerified;

  AccuracyStats({
    required this.totalPredictions,
    required this.verifiedPredictions,
    required this.avgErrorRate,
    required this.recentVerified,
  });

  factory AccuracyStats.fromJson(Map<String, dynamic> json) {
    return AccuracyStats(
      totalPredictions: json['stats']['total_predictions'] ?? 0,
      verifiedPredictions: json['stats']['verified_predictions'] ?? 0,
      avgErrorRate: (json['stats']['avg_error_rate'] ?? 0).toDouble(),
      recentVerified: (json['recent_verified'] as List?)
              ?.map((item) => VerifiedPrediction.fromJson(item))
              .toList() ??
          [],
    );
  }
}

class VerifiedPrediction {
  final String caseNumber;
  final int predictedPrice;
  final int actualPrice;
  final double errorRate;
  final DateTime actualDate;

  VerifiedPrediction({
    required this.caseNumber,
    required this.predictedPrice,
    required this.actualPrice,
    required this.errorRate,
    required this.actualDate,
  });

  factory VerifiedPrediction.fromJson(Map<String, dynamic> json) {
    return VerifiedPrediction(
      caseNumber: json['case_number'] ?? json['사건번호'] ?? '',
      predictedPrice: json['predicted_price'] ?? json['예측가'] ?? 0,
      actualPrice: json['actual_price'] ?? json['실제낙찰가'] ?? 0,
      errorRate: (json['error_rate'] ?? json['오차율'] ?? 0).toDouble(),
      actualDate: DateTime.parse(
        json['actual_date'] ?? json['낙찰일자'] ?? DateTime.now().toIso8601String(),
      ),
    );
  }
}

// ========================================
// 가격대별 통계 모델
// ========================================

class PriceRangeStats {
  final String priceRange;
  final int count;
  final double avgErrorRate;

  PriceRangeStats({
    required this.priceRange,
    required this.count,
    required this.avgErrorRate,
  });

  factory PriceRangeStats.fromJson(Map<String, dynamic> json) {
    return PriceRangeStats(
      priceRange: json['price_range'],
      count: json['count'],
      avgErrorRate: (json['avg_error_rate'] ?? 0).toDouble(),
    );
  }
}

// ========================================
// 지역별 통계 모델
// ========================================

class RegionalStats {
  final String region;
  final int count;
  final int avgStartPrice;
  final int avgPredictedPrice;

  RegionalStats({
    required this.region,
    required this.count,
    required this.avgStartPrice,
    required this.avgPredictedPrice,
  });

  factory RegionalStats.fromJson(Map<String, dynamic> json) {
    return RegionalStats(
      region: json['region'],
      count: json['count'],
      avgStartPrice: json['avg_start_price'] ?? 0,
      avgPredictedPrice: json['avg_predicted_price'] ?? 0,
    );
  }
}

// ========================================
// 전체 분석 결과 모델 (Full Analysis)
// ========================================

/// 투자 매력도 점수 세부 항목
class ScoreDetail {
  final String category;
  final int score;
  final int maxScore;
  final String level;
  final String description;

  ScoreDetail({
    required this.category,
    required this.score,
    required this.maxScore,
    required this.level,
    required this.description,
  });

  factory ScoreDetail.fromJson(Map<String, dynamic> json) {
    return ScoreDetail(
      category: json['category'] ?? '',
      score: json['score'] ?? 0,
      maxScore: json['max_score'] ?? 0,
      level: json['level'] ?? '',
      description: json['description'] ?? '',
    );
  }
}

/// 투자 매력도 점수
class InvestmentScore {
  final int totalScore;
  final String level;
  final String color;
  final List<ScoreDetail> details;

  InvestmentScore({
    required this.totalScore,
    required this.level,
    required this.color,
    required this.details,
  });

  factory InvestmentScore.fromJson(Map<String, dynamic> json) {
    return InvestmentScore(
      totalScore: json['total_score'] ?? 0,
      level: json['level'] ?? '',
      color: json['color'] ?? '',
      details: (json['details'] as List?)
              ?.map((item) => ScoreDetail.fromJson(item))
              .toList() ??
          [],
    );
  }

  String get formattedScore => '$totalScore점';
}

/// AI 신뢰도
class AiConfidence {
  final int score;
  final int stars;
  final int trainingSamples;
  final double avgErrorRate;
  final String modelVersion;

  AiConfidence({
    required this.score,
    required this.stars,
    required this.trainingSamples,
    required this.avgErrorRate,
    required this.modelVersion,
  });

  factory AiConfidence.fromJson(Map<String, dynamic> json) {
    return AiConfidence(
      score: json['score'] ?? 0,
      stars: json['stars'] ?? 0,
      trainingSamples: json['training_samples'] ?? 0,
      avgErrorRate: (json['avg_error_rate'] ?? 0).toDouble(),
      modelVersion: json['model_version'] ?? '',
    );
  }

  String get formattedErrorRate => '${avgErrorRate.toStringAsFixed(2)}%';
}

/// 입찰 전략 추천
class BiddingStrategy {
  final int currentRound;
  final int currentMinimum;
  final int predictedPrice;
  final String recommendation;
  final int? waitUntilRound;
  final int potentialSavings;
  final String message;

  BiddingStrategy({
    required this.currentRound,
    required this.currentMinimum,
    required this.predictedPrice,
    required this.recommendation,
    this.waitUntilRound,
    required this.potentialSavings,
    required this.message,
  });

  factory BiddingStrategy.fromJson(Map<String, dynamic> json) {
    return BiddingStrategy(
      currentRound: json['current_round'] ?? 1,
      currentMinimum: json['current_minimum'] ?? 0,
      predictedPrice: json['predicted_price'] ?? 0,
      recommendation: json['recommendation'] ?? '',
      waitUntilRound: json['wait_until_round'],
      potentialSavings: json['potential_savings'] ?? 0,
      message: json['message'] ?? '',
    );
  }

  String get formattedCurrentMinimum => _formatPrice(currentMinimum);
  String get formattedPredictedPrice => _formatPrice(predictedPrice);
  String get formattedPotentialSavings => _formatPrice(potentialSavings);

  String _formatPrice(int price) {
    // 숫자를 천 단위로 쉼표를 추가하여 포맷팅
    final str = price.toString();
    final buffer = StringBuffer();
    int count = 0;

    for (int i = str.length - 1; i >= 0; i--) {
      if (count > 0 && count % 3 == 0) {
        buffer.write(',');
      }
      buffer.write(str[i]);
      count++;
    }

    return '${buffer.toString().split('').reversed.join()}원';
  }
}

/// 수익 분석
class ProfitAnalysis {
  final int expectedProfit;
  final double profitRate;
  final int marketPrice;
  final String marketPriceSource;

  ProfitAnalysis({
    required this.expectedProfit,
    required this.profitRate,
    required this.marketPrice,
    required this.marketPriceSource,
  });

  factory ProfitAnalysis.fromJson(Map<String, dynamic> json) {
    return ProfitAnalysis(
      expectedProfit: json['예상수익'] ?? json['expected_profit'] ?? 0,
      profitRate: (json['예상수익률'] ?? json['profit_rate'] ?? 0).toDouble(),
      marketPrice: json['시세'] ?? json['market_price'] ?? 0,
      marketPriceSource: json['시세출처'] ?? json['market_price_source'] ?? '',
    );
  }

  String get formattedExpectedProfit {
    if (expectedProfit >= 100000000) {
      final eok = expectedProfit ~/ 100000000;
      final man = (expectedProfit % 100000000) ~/ 10000;
      if (man > 0) {
        return '$eok억 ${man}만원';
      }
      return '$eok억원';
    } else if (expectedProfit >= 10000) {
      return '${expectedProfit ~/ 10000}만원';
    }
    return '$expectedProfit원';
  }

  String get formattedProfitRate => '${profitRate.toStringAsFixed(1)}%';
}

/// 고급 분석 데이터
class AdvancedAnalysis {
  final int lowestBidPrice;
  final double lowestBidRatio;
  final double predictedRatio;
  final InvestmentScore investmentScore;
  final AiConfidence aiConfidence;
  final BiddingStrategy biddingStrategy;

  AdvancedAnalysis({
    required this.lowestBidPrice,
    required this.lowestBidRatio,
    required this.predictedRatio,
    required this.investmentScore,
    required this.aiConfidence,
    required this.biddingStrategy,
  });

  factory AdvancedAnalysis.fromJson(Map<String, dynamic> json) {
    return AdvancedAnalysis(
      lowestBidPrice: json['lowest_bid_price'] ?? 0,
      lowestBidRatio: (json['lowest_bid_ratio'] ?? 0).toDouble(),
      predictedRatio: (json['predicted_ratio'] ?? 0).toDouble(),
      investmentScore: InvestmentScore.fromJson(json['investment_score'] ?? {}),
      aiConfidence: AiConfidence.fromJson(json['ai_confidence'] ?? {}),
      biddingStrategy: BiddingStrategy.fromJson(json['bidding_strategy'] ?? {}),
    );
  }

  String get formattedLowestBidPrice {
    if (lowestBidPrice >= 100000000) {
      final eok = lowestBidPrice ~/ 100000000;
      final man = (lowestBidPrice % 100000000) ~/ 10000;
      if (man > 0) {
        return '$eok억 ${man}만원';
      }
      return '$eok억원';
    } else if (lowestBidPrice >= 10000) {
      return '${lowestBidPrice ~/ 10000}만원';
    }
    return '$lowestBidPrice원';
  }
}

/// 전체 분석 결과 (Full Analysis Result)
class FullAnalysisResult {
  final Map<String, dynamic> auctionInfo;
  final int predictedPrice;
  final String predictedPriceFormatted;
  final int marketPrice;
  final String marketPriceFormatted;
  final ProfitAnalysis profitAnalysis;
  final int transactionsCount;
  final String realTransactionNote;
  final String realTransactionWarning;
  final bool modelUsed;
  final AdvancedAnalysis advancedAnalysis;

  FullAnalysisResult({
    required this.auctionInfo,
    required this.predictedPrice,
    required this.predictedPriceFormatted,
    required this.marketPrice,
    required this.marketPriceFormatted,
    required this.profitAnalysis,
    required this.transactionsCount,
    required this.realTransactionNote,
    required this.realTransactionWarning,
    required this.modelUsed,
    required this.advancedAnalysis,
  });

  factory FullAnalysisResult.fromJson(Map<String, dynamic> json) {
    final data = json['data'] ?? json;
    return FullAnalysisResult(
      auctionInfo: data['auction_info'] ?? {},
      predictedPrice: data['predicted_price'] ?? 0,
      predictedPriceFormatted: data['predicted_price_formatted'] ?? '0원',
      marketPrice: data['market_price'] ?? 0,
      marketPriceFormatted: data['market_price_formatted'] ?? '0원',
      profitAnalysis: ProfitAnalysis.fromJson(data['profit_analysis'] ?? {}),
      transactionsCount: data['transactions_count'] ?? 0,
      realTransactionNote: data['real_transaction_note'] ?? '',
      realTransactionWarning: data['real_transaction_warning'] ?? '',
      modelUsed: data['model_used'] ?? false,
      advancedAnalysis: AdvancedAnalysis.fromJson(data['advanced_analysis'] ?? {}),
    );
  }

  // 경매 정보 편의 메서드
  String get caseNumber => auctionInfo['사건번호'] ?? '';
  String get propertyType => auctionInfo['물건종류'] ?? '';
  String get address => auctionInfo['소재지'] ?? '';
  String get region => auctionInfo['지역'] ?? '';
  String get area => auctionInfo['면적'] ?? '';
  int get auctionRound => auctionInfo['경매회차'] ?? 1;
  int get startPrice => auctionInfo['감정가_숫자'] ?? 0;
  String get formattedStartPrice => auctionInfo['감정가'] ?? '0원';
  String get auctionDate => auctionInfo['경매일자'] ?? '';
  String get biddingDate => auctionInfo['bidding_date'] ?? '';
  String get court => auctionInfo['법원'] ?? '';
  String get courtDepartment => auctionInfo['경매계'] ?? '';

  /// 매각기일 포맷팅 ("20260316" -> "2026년 3월 16일")
  String get formattedBiddingDate {
    if (biddingDate.isEmpty || biddingDate.length != 8) return '';

    try {
      final year = biddingDate.substring(0, 4);
      final month = biddingDate.substring(4, 6);
      final day = biddingDate.substring(6, 8);

      return '$year년 ${int.parse(month)}월 ${int.parse(day)}일';
    } catch (e) {
      return biddingDate;
    }
  }

  /// 면적을 제곱미터와 평 단위로 함께 표시 (예: "61.32㎡ (18.5평)")
  String get formattedArea {
    final areaStr = area;
    if (areaStr.isEmpty) return '';

    // "61.32㎡" 형식에서 숫자 추출
    final match = RegExp(r'([\d.]+)').firstMatch(areaStr);
    if (match == null) return areaStr;

    final sqm = double.tryParse(match.group(1) ?? '0');
    if (sqm == null || sqm == 0) return areaStr;

    // 제곱미터를 평으로 변환 (1평 = 3.30579㎡)
    final pyeong = sqm / 3.30579;

    return '$areaStr (${pyeong.toStringAsFixed(0)}평)';
  }

  /// 법원 정보를 포맷팅하여 반환 (예: "서울동부지방법원 경매6계")
  String get formattedCourt {
    final courtName = court;
    final dept = courtDepartment;
    if (courtName.isEmpty) return '';
    if (dept.isNotEmpty) {
      return '$courtName $dept';
    }
    return courtName;
  }
}
