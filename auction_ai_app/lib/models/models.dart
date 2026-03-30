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
// 입찰 시뮬레이션 모델
// ========================================

class BidSimulation {
  final int bidAmount;          // 입찰 금액
  final int winProbability;     // 낙찰 확률 (%)
  final int expectedProfit;     // 예상 수익
  final double profitRate;      // 수익률 (%)
  final String recommendation;  // 추천 문구
  final int estimatedBidders;   // 예상 입찰자 수

  BidSimulation({
    required this.bidAmount,
    required this.winProbability,
    required this.expectedProfit,
    required this.profitRate,
    required this.recommendation,
    required this.estimatedBidders,
  });

  factory BidSimulation.fromJson(Map<String, dynamic> json) {
    return BidSimulation(
      bidAmount: json['bid_amount'] ?? 0,
      winProbability: json['win_probability'] ?? 0,
      expectedProfit: json['expected_profit'] ?? 0,
      profitRate: (json['profit_rate'] ?? 0).toDouble(),
      recommendation: json['recommendation'] ?? '',
      estimatedBidders: json['estimated_bidders'] ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'bid_amount': bidAmount,
      'win_probability': winProbability,
      'expected_profit': expectedProfit,
      'profit_rate': profitRate,
      'recommendation': recommendation,
      'estimated_bidders': estimatedBidders,
    };
  }

  String get formattedBidAmount {
    if (bidAmount >= 100000000) {
      final eok = bidAmount ~/ 100000000;
      final man = (bidAmount % 100000000) ~/ 10000;
      if (man > 0) {
        return '$eok억 ${man}만원';
      }
      return '$eok억원';
    } else if (bidAmount >= 10000) {
      return '${bidAmount ~/ 10000}만원';
    }
    return '${bidAmount}원';
  }

  String get formattedExpectedProfit {
    final absProfit = expectedProfit.abs();
    final sign = expectedProfit < 0 ? '-' : '';
    if (absProfit >= 100000000) {
      final eok = absProfit ~/ 100000000;
      final man = (absProfit % 100000000) ~/ 10000;
      if (man > 0) {
        return '$sign$eok억 ${man}만원';
      }
      return '$sign$eok억원';
    } else if (absProfit >= 10000) {
      return '$sign${absProfit ~/ 10000}만원';
    }
    return '$sign${absProfit}원';
  }
}

// ========================================
// 유사 물건 모델
// ========================================

class SimilarProperty {
  final String address;           // 소재지
  final String? propertyType;     // 물건 종류
  final double? area;             // 면적 (㎡)
  final int winningBid;           // 낙찰가
  final String? auctionDate;      // 경매일
  final int similarityScore;      // 유사도 점수 (0-100)
  final String? court;            // 법원

  SimilarProperty({
    required this.address,
    this.propertyType,
    this.area,
    required this.winningBid,
    this.auctionDate,
    required this.similarityScore,
    this.court,
  });

  factory SimilarProperty.fromJson(Map<String, dynamic> json) {
    return SimilarProperty(
      address: json['address'] ?? '',
      propertyType: json['property_type'],
      area: (json['area'])?.toDouble(),
      winningBid: json['winning_bid'] ?? 0,
      auctionDate: json['auction_date'],
      similarityScore: json['similarity_score'] ?? 0,
      court: json['court'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'address': address,
      'property_type': propertyType,
      'area': area,
      'winning_bid': winningBid,
      'auction_date': auctionDate,
      'similarity_score': similarityScore,
      'court': court,
    };
  }

  String get formattedWinningBid {
    if (winningBid >= 100000000) {
      final eok = winningBid ~/ 100000000;
      final man = (winningBid % 100000000) ~/ 10000;
      if (man > 0) {
        return '$eok억 ${man}만원';
      }
      return '$eok억원';
    } else if (winningBid >= 10000) {
      return '${winningBid ~/ 10000}만원';
    }
    return '${winningBid}원';
  }
}

// ========================================
// 회차별 가격 이력 모델
// ========================================

class RoundHistory {
  final int round;           // 회차
  final int price;           // 가격
  final double changeRate;   // 변화율 (%)

  RoundHistory({
    required this.round,
    required this.price,
    required this.changeRate,
  });

  factory RoundHistory.fromJson(Map<String, dynamic> json) {
    return RoundHistory(
      round: json['round'] ?? 0,
      price: json['price'] ?? 0,
      changeRate: (json['change_rate'] ?? 0).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'round': round,
      'price': price,
      'change_rate': changeRate,
    };
  }

  String get formattedPrice {
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
    return '${price}원';
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

  // 입찰 전략 정보
  final int? confidenceLowerBound;  // 신뢰구간 하한
  final int? confidenceUpperBound;  // 신뢰구간 상한
  final int? safeBidPrice;          // 안전 입찰가
  final int? aggressiveBidPrice;    // 공격 입찰가
  final int? recommendedBidPrice;   // 권장 입찰가
  final int? safeBidProbability;    // 안전 입찰 확률
  final int? aggressiveBidProbability;  // 공격 입찰 확률

  // 예측 신뢰도 정보
  final int? confidenceScore;       // 신뢰도 점수 (0-100)
  final int? confidenceStars;       // 별점 (1-5)
  final int? similarCasesCount;     // 유사 사례 개수
  final int? regionalDataCount;     // 지역 데이터 개수
  final List<String>? confidenceReasons;   // 높은 신뢰도 이유
  final List<String>? confidenceWarnings;  // 주의사항

  // 경쟁 분석 정보
  final String? competitionLevel;    // 경쟁 강도 (낮음/중간/높음)
  final int? viewCount;              // 조회수
  final int? avgBidderCount;         // 평균 입찰자 수
  final double? avgSuccessRate;      // 평균 낙찰률 (%)
  final String? recentCasesSummary;  // 최근 사례 요약

  // 리스크 분석 정보
  final int? riskScore;              // 종합 리스크 점수 (0-10, 낮을수록 안전)
  final String? riskLevel;           // 리스크 수준 (낮음/중간/높음)
  final List<String>? riskFactors;   // 주요 리스크 요인
  final List<String>? safetyFactors; // 안전 요소
  final String? legalAdvice;         // 법률 자문 권장사항

  // 회차별 가격 추이 정보
  final List<RoundHistory>? roundHistory;  // 회차별 가격 이력
  final String? priceTrend;                // 가격 추세 (상승/하락/안정)
  final int? nextRoundPredictedPrice;      // 다음 회차 예상가
  final double? trendChangeRate;           // 추세 변화율 (%)

  // 유사 물건 비교 정보
  final List<SimilarProperty>? similarProperties;  // 유사 물건 목록
  final int? avgSimilarPrice;                      // 유사 물건 평균 낙찰가
  final int? minSimilarPrice;                      // 유사 물건 최저 낙찰가
  final int? maxSimilarPrice;                      // 유사 물건 최고 낙찰가
  final String? comparisonSummary;                 // 비교 요약

  // 입찰 시뮬레이터 정보
  final List<BidSimulation>? bidSimulations;       // 입찰 시뮬레이션 시나리오들
  final String? simulatorGuidance;                 // 시뮬레이터 안내 메시지

  // D-day 알림 + 체크리스트 정보
  final int? daysUntilAuction;                     // 경매일까지 남은 일수
  final String? auctionDateTime;                   // 경매 일시
  final List<String>? preparationChecklist;        // 준비사항 체크리스트
  final String? urgencyMessage;                    // 긴급도 메시지

  // AI 학습 피드백 정보
  final String? feedbackPrompt;                    // 피드백 요청 메시지
  final bool? feedbackEnabled;                     // 피드백 활성화 여부

  // 전문가 의견 (커뮤니티) 정보
  final List<String>? expertTips;                  // 전문가 팁
  final String? communityInsight;                  // 커뮤니티 인사이트
  final int? similarCaseDiscussions;               // 유사 사례 토론 수

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
    this.confidenceLowerBound,
    this.confidenceUpperBound,
    this.safeBidPrice,
    this.aggressiveBidPrice,
    this.recommendedBidPrice,
    this.safeBidProbability,
    this.aggressiveBidProbability,
    this.confidenceScore,
    this.confidenceStars,
    this.similarCasesCount,
    this.regionalDataCount,
    this.confidenceReasons,
    this.confidenceWarnings,
    this.competitionLevel,
    this.viewCount,
    this.avgBidderCount,
    this.avgSuccessRate,
    this.recentCasesSummary,
    this.riskScore,
    this.riskLevel,
    this.riskFactors,
    this.safetyFactors,
    this.legalAdvice,
    this.roundHistory,
    this.priceTrend,
    this.nextRoundPredictedPrice,
    this.trendChangeRate,
    this.similarProperties,
    this.avgSimilarPrice,
    this.minSimilarPrice,
    this.maxSimilarPrice,
    this.comparisonSummary,
    this.bidSimulations,
    this.simulatorGuidance,
    this.daysUntilAuction,
    this.auctionDateTime,
    this.preparationChecklist,
    this.urgencyMessage,
    this.feedbackPrompt,
    this.feedbackEnabled,
    this.expertTips,
    this.communityInsight,
    this.similarCaseDiscussions,
  });

  factory PredictionResult.fromJson(Map<String, dynamic> json) {
    // API 응답이 { "success": true, "data": {...}, "input": {...} } 형식인 경우 처리
    final data = json['data'] ?? json;
    final input = json['input'] ?? {};

    return PredictionResult(
      startPrice: data['start_price'] ?? data['감정가'] ?? 0,
      predictedPrice: data['predicted_price'] ?? data['예측가'] ?? 0,
      expectedProfit: data['expected_profit'] ?? data['예상수익'] ?? 0,
      profitRate: (data['profit_rate'] ?? data['수익률'] ?? 0).toDouble(),
      propertyType: input['property_type'] ?? data['property_type'] ?? data['물건종류'],
      region: input['region'] ?? data['region'] ?? data['지역'],
      area: (input['area'] ?? data['area'] ?? data['면적'])?.toDouble(),
      auctionRound: input['auction_round'] ?? data['auction_round'] ?? data['경매회차'] ?? 1,
      modelUsed: data['model_used'] ?? false,
      predictionMode: data['prediction_mode'],
      featuresCount: data['features_count'],
      warning: data['warning'],
      confidenceLowerBound: data['confidence_lower_bound'],
      confidenceUpperBound: data['confidence_upper_bound'],
      safeBidPrice: data['safe_bid_price'],
      aggressiveBidPrice: data['aggressive_bid_price'],
      recommendedBidPrice: data['recommended_bid_price'],
      safeBidProbability: data['safe_bid_probability'],
      aggressiveBidProbability: data['aggressive_bid_probability'],
      confidenceScore: data['confidence_score'],
      confidenceStars: data['confidence_stars'],
      similarCasesCount: data['similar_cases_count'],
      regionalDataCount: data['regional_data_count'],
      confidenceReasons: (data['confidence_reasons'] as List?)?.map((e) => e.toString()).toList(),
      confidenceWarnings: (data['confidence_warnings'] as List?)?.map((e) => e.toString()).toList(),
      competitionLevel: data['competition_level'],
      viewCount: data['view_count'],
      avgBidderCount: data['avg_bidder_count'],
      avgSuccessRate: (data['avg_success_rate'])?.toDouble(),
      recentCasesSummary: data['recent_cases_summary'],
      riskScore: data['risk_score'],
      riskLevel: data['risk_level'],
      riskFactors: (data['risk_factors'] as List?)?.map((e) => e.toString()).toList(),
      safetyFactors: (data['safety_factors'] as List?)?.map((e) => e.toString()).toList(),
      legalAdvice: data['legal_advice'],
      roundHistory: (data['round_history'] as List?)?.map((e) => RoundHistory.fromJson(e as Map<String, dynamic>)).toList(),
      priceTrend: data['price_trend'],
      nextRoundPredictedPrice: data['next_round_predicted_price'],
      trendChangeRate: (data['trend_change_rate'])?.toDouble(),
      similarProperties: (data['similar_properties'] as List?)?.map((e) => SimilarProperty.fromJson(e as Map<String, dynamic>)).toList(),
      avgSimilarPrice: data['avg_similar_price'],
      minSimilarPrice: data['min_similar_price'],
      maxSimilarPrice: data['max_similar_price'],
      comparisonSummary: data['comparison_summary'],
      bidSimulations: (data['bid_simulations'] as List?)?.map((e) => BidSimulation.fromJson(e as Map<String, dynamic>)).toList(),
      simulatorGuidance: data['simulator_guidance'],
      daysUntilAuction: data['days_until_auction'],
      auctionDateTime: data['auction_date_time'],
      preparationChecklist: (data['preparation_checklist'] as List?)?.map((e) => e.toString()).toList(),
      urgencyMessage: data['urgency_message'],
      feedbackPrompt: data['feedback_prompt'],
      feedbackEnabled: data['feedback_enabled'],
      expertTips: (data['expert_tips'] as List?)?.map((e) => e.toString()).toList(),
      communityInsight: data['community_insight'],
      similarCaseDiscussions: data['similar_case_discussions'],
    );
  }

  String get formattedPredictedPrice =>
      '${formatNumber(predictedPrice)}원';

  String get formattedExpectedProfit {
    final absProfit = expectedProfit.abs();
    final sign = expectedProfit < 0 ? '-' : '';
    return '$sign${formatNumber(absProfit)}원';
  }

  String get formattedProfitRate =>
      '${profitRate.toStringAsFixed(1)}%';

  // 입찰 전략 관련 포맷팅 메서드
  String? get formattedConfidenceLowerBound =>
      confidenceLowerBound != null ? '${formatNumber(confidenceLowerBound!)}원' : null;

  String? get formattedConfidenceUpperBound =>
      confidenceUpperBound != null ? '${formatNumber(confidenceUpperBound!)}원' : null;

  String? get formattedSafeBidPrice =>
      safeBidPrice != null ? '${formatNumber(safeBidPrice!)}원' : null;

  String? get formattedAggressiveBidPrice =>
      aggressiveBidPrice != null ? '${formatNumber(aggressiveBidPrice!)}원' : null;

  String? get formattedRecommendedBidPrice =>
      recommendedBidPrice != null ? '${formatNumber(recommendedBidPrice!)}원' : null;

  static String formatNumber(int number) {
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
  final int? actualSellingPrice;
  final String? formattedActualSellingPrice;

  BiddingStrategy({
    required this.currentRound,
    required this.currentMinimum,
    required this.predictedPrice,
    required this.recommendation,
    this.waitUntilRound,
    required this.potentialSavings,
    required this.message,
    this.actualSellingPrice,
    this.formattedActualSellingPrice,
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
      actualSellingPrice: json['actual_selling_price'],
      formattedActualSellingPrice: json['actual_selling_price_formatted'],
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
    final absProfit = expectedProfit.abs();
    final sign = expectedProfit < 0 ? '-' : '';

    // 숫자를 천 단위로 쉼표를 추가하여 포맷팅
    final str = absProfit.toString();
    final buffer = StringBuffer();
    int count = 0;

    for (int i = str.length - 1; i >= 0; i--) {
      if (count > 0 && count % 3 == 0) {
        buffer.write(',');
      }
      buffer.write(str[i]);
      count++;
    }

    final formatted = buffer.toString().split('').reversed.join();
    return '$sign$formatted원';
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

  // 10가지 고급 기능 필드
  // 1. 입찰 전략 정보
  final int? confidenceLowerBound;
  final int? confidenceUpperBound;
  final int? safeBidPrice;
  final int? aggressiveBidPrice;
  final int? recommendedBidPrice;
  final int? safeBidProbability;
  final int? aggressiveBidProbability;

  // 2. 예측 신뢰도 정보
  final int? confidenceScore;
  final int? confidenceStars;
  final int? similarCasesCount;
  final int? regionalDataCount;
  final List<String>? confidenceReasons;
  final List<String>? confidenceWarnings;

  // 3. 경쟁 분석 정보
  final String? competitionLevel;
  final int? viewCount;
  final int? avgBidderCount;
  final double? avgSuccessRate;
  final String? recentCasesSummary;

  // 4. 리스크 분석 정보
  final int? riskScore;
  final String? riskLevel;
  final List<String>? riskFactors;
  final List<String>? safetyFactors;
  final String? legalAdvice;

  // 5. 회차별 가격 추이 정보
  final List<RoundHistory>? roundHistory;
  final String? priceTrend;
  final int? nextRoundPredictedPrice;
  final double? trendChangeRate;

  // 6. 유사 물건 비교 정보
  final List<SimilarProperty>? similarProperties;
  final int? avgSimilarPrice;
  final int? minSimilarPrice;
  final int? maxSimilarPrice;
  final String? comparisonSummary;

  // 7. 입찰 시뮬레이터 정보
  final List<BidSimulation>? bidSimulations;
  final String? simulatorGuidance;

  // 8. D-day 알림 + 체크리스트 정보
  final int? daysUntilAuction;
  final String? auctionDateTime;
  final List<String>? preparationChecklist;
  final String? urgencyMessage;

  // 9. AI 학습 피드백 정보
  final String? feedbackPrompt;
  final bool? feedbackEnabled;

  // 10. 전문가 의견 정보
  final List<String>? expertTips;
  final String? communityInsight;
  final int? similarCaseDiscussions;

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
    // 10가지 고급 기능 필드
    this.confidenceLowerBound,
    this.confidenceUpperBound,
    this.safeBidPrice,
    this.aggressiveBidPrice,
    this.recommendedBidPrice,
    this.safeBidProbability,
    this.aggressiveBidProbability,
    this.confidenceScore,
    this.confidenceStars,
    this.similarCasesCount,
    this.regionalDataCount,
    this.confidenceReasons,
    this.confidenceWarnings,
    this.competitionLevel,
    this.viewCount,
    this.avgBidderCount,
    this.avgSuccessRate,
    this.recentCasesSummary,
    this.riskScore,
    this.riskLevel,
    this.riskFactors,
    this.safetyFactors,
    this.legalAdvice,
    this.roundHistory,
    this.priceTrend,
    this.nextRoundPredictedPrice,
    this.trendChangeRate,
    this.similarProperties,
    this.avgSimilarPrice,
    this.minSimilarPrice,
    this.maxSimilarPrice,
    this.comparisonSummary,
    this.bidSimulations,
    this.simulatorGuidance,
    this.daysUntilAuction,
    this.auctionDateTime,
    this.preparationChecklist,
    this.urgencyMessage,
    this.feedbackPrompt,
    this.feedbackEnabled,
    this.expertTips,
    this.communityInsight,
    this.similarCaseDiscussions,
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
      // 10가지 고급 기능 필드 파싱
      confidenceLowerBound: data['confidence_lower_bound'],
      confidenceUpperBound: data['confidence_upper_bound'],
      safeBidPrice: data['safe_bid_price'],
      aggressiveBidPrice: data['aggressive_bid_price'],
      recommendedBidPrice: data['recommended_bid_price'],
      safeBidProbability: data['safe_bid_probability'],
      aggressiveBidProbability: data['aggressive_bid_probability'],
      confidenceScore: data['confidence_score'],
      confidenceStars: data['confidence_stars'],
      similarCasesCount: data['similar_cases_count'],
      regionalDataCount: data['regional_data_count'],
      confidenceReasons: (data['confidence_reasons'] as List?)?.map((e) => e.toString()).toList(),
      confidenceWarnings: (data['confidence_warnings'] as List?)?.map((e) => e.toString()).toList(),
      competitionLevel: data['competition_level'],
      viewCount: data['view_count'],
      avgBidderCount: data['avg_bidder_count'],
      avgSuccessRate: (data['avg_success_rate'])?.toDouble(),
      recentCasesSummary: data['recent_cases_summary'],
      riskScore: data['risk_score'],
      riskLevel: data['risk_level'],
      riskFactors: (data['risk_factors'] as List?)?.map((e) => e.toString()).toList(),
      safetyFactors: (data['safety_factors'] as List?)?.map((e) => e.toString()).toList(),
      legalAdvice: data['legal_advice'],
      roundHistory: (data['round_history'] as List?)?.map((e) => RoundHistory.fromJson(e as Map<String, dynamic>)).toList(),
      priceTrend: data['price_trend'],
      nextRoundPredictedPrice: data['next_round_predicted_price'],
      trendChangeRate: (data['trend_change_rate'])?.toDouble(),
      similarProperties: (data['similar_properties'] as List?)?.map((e) => SimilarProperty.fromJson(e as Map<String, dynamic>)).toList(),
      avgSimilarPrice: data['avg_similar_price'],
      minSimilarPrice: data['min_similar_price'],
      maxSimilarPrice: data['max_similar_price'],
      comparisonSummary: data['comparison_summary'],
      bidSimulations: (data['bid_simulations'] as List?)?.map((e) => BidSimulation.fromJson(e as Map<String, dynamic>)).toList(),
      simulatorGuidance: data['simulator_guidance'],
      daysUntilAuction: data['days_until_auction'],
      auctionDateTime: data['auction_date_time'],
      preparationChecklist: (data['preparation_checklist'] as List?)?.map((e) => e.toString()).toList(),
      urgencyMessage: data['urgency_message'],
      feedbackPrompt: data['feedback_prompt'],
      feedbackEnabled: data['feedback_enabled'],
      expertTips: (data['expert_tips'] as List?)?.map((e) => e.toString()).toList(),
      communityInsight: data['community_insight'],
      similarCaseDiscussions: data['similar_case_discussions'],
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
