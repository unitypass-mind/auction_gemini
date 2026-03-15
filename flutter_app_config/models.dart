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
      id: json['id'],
      email: json['email'],
      name: json['name'],
      createdAt: DateTime.parse(json['created_at']),
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
