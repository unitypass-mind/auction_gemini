"""
패턴 테이블 생성 스크립트 - v4 모델 개선
과거 데이터를 분석하여 예측에 사용할 패턴 테이블 생성

1. 물건종류 × 경매회차 패턴
2. 지역별 통계
3. 복합 패턴 (지역 × 물건종류 × 회차)
"""
import sqlite3
import pandas as pd
import joblib
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "data/predictions.db"
MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)


def create_property_round_pattern():
    """
    패턴 1: 물건종류 × 경매회차별 평균 낙찰률
    예: 아파트 3회차 평균 낙찰률 = 0.65
    """
    logger.info("=" * 60)
    logger.info("패턴 1: 물건종류 × 경매회차 패턴 생성")
    logger.info("=" * 60)

    conn = sqlite3.connect(DB_PATH)

    # 물건종류 정규화 (주요 카테고리로 그룹핑)
    raw_data = pd.read_sql_query("""
        SELECT
            CASE
                WHEN 물건종류 LIKE '%아파트%' THEN '아파트'
                WHEN 물건종류 LIKE '%오피스텔%' THEN '오피스텔'
                WHEN 물건종류 LIKE '%다세대%' OR 물건종류 LIKE '%연립%' THEN '다세대'
                WHEN 물건종류 LIKE '%단독%' THEN '단독주택'
                WHEN 물건종류 LIKE '%상가%' OR 물건종류 LIKE '%점포%' THEN '상가'
                WHEN 물건종류 LIKE '%토지%' THEN '토지'
                ELSE '기타'
            END as property_category,
            경매회차,
            actual_price * 1.0 / 감정가 as ratio
        FROM predictions
        WHERE actual_price > 0
          AND 감정가 > 0
    """, conn)

    # pandas로 그룹별 평균, 표준편차 계산
    pattern = raw_data.groupby(['property_category', '경매회차'])['ratio'].agg([
        ('avg_ratio', 'mean'),
        ('std_ratio', 'std'),
        ('count', 'count')
    ]).reset_index()

    # 최소 건수 필터링
    pattern = pattern[pattern['count'] >= 5]
    pattern = pattern.sort_values(['property_category', '경매회차'])

    conn.close()

    # 딕셔너리로 변환
    pattern_dict = {}
    for _, row in pattern.iterrows():
        key = f"{row['property_category']}_{row['경매회차']}"
        pattern_dict[key] = {
            'avg_ratio': row['avg_ratio'],
            'std_ratio': row['std_ratio'] if pd.notna(row['std_ratio']) else 0,
            'count': row['count']
        }

    # 저장
    output_path = MODELS_DIR / "pattern_property_round.pkl"
    joblib.dump(pattern_dict, output_path)

    logger.info(f"✅ 패턴 개수: {len(pattern_dict)}")
    logger.info(f"✅ 저장 경로: {output_path}")

    # 샘플 출력
    logger.info("\n샘플 패턴:")
    for i, (key, value) in enumerate(list(pattern_dict.items())[:10]):
        logger.info(f"  {key}: 평균={value['avg_ratio']:.3f}, 건수={value['count']}")

    return pattern_dict


def create_region_stats():
    """
    패턴 2: 지역별 평균 낙찰률 및 입찰자수
    예: 서울 평균 낙찰률 = 0.72, 평균 입찰자수 = 3.5
    """
    logger.info("\n" + "=" * 60)
    logger.info("패턴 2: 지역별 통계 생성")
    logger.info("=" * 60)

    conn = sqlite3.connect(DB_PATH)

    # 지역을 광역시/도 단위로 그룹핑
    region_stats = pd.read_sql_query("""
        SELECT
            CASE
                WHEN 지역 LIKE '%서울%' THEN '서울'
                WHEN 지역 LIKE '%경기%' THEN '경기'
                WHEN 지역 LIKE '%인천%' THEN '인천'
                WHEN 지역 LIKE '%부산%' THEN '부산'
                WHEN 지역 LIKE '%대구%' THEN '대구'
                WHEN 지역 LIKE '%대전%' THEN '대전'
                WHEN 지역 LIKE '%광주%' THEN '광주'
                WHEN 지역 LIKE '%울산%' THEN '울산'
                WHEN 지역 LIKE '%세종%' THEN '세종'
                WHEN 지역 LIKE '%강원%' THEN '강원'
                WHEN 지역 LIKE '%충북%' OR 지역 LIKE '%충청북%' THEN '충북'
                WHEN 지역 LIKE '%충남%' OR 지역 LIKE '%충청남%' THEN '충남'
                WHEN 지역 LIKE '%전북%' OR 지역 LIKE '%전라북%' THEN '전북'
                WHEN 지역 LIKE '%전남%' OR 지역 LIKE '%전라남%' THEN '전남'
                WHEN 지역 LIKE '%경북%' OR 지역 LIKE '%경상북%' THEN '경북'
                WHEN 지역 LIKE '%경남%' OR 지역 LIKE '%경상남%' THEN '경남'
                WHEN 지역 LIKE '%제주%' THEN '제주'
                ELSE '기타'
            END as region_group,
            AVG(actual_price * 1.0 / 감정가) as avg_ratio,
            AVG(입찰자수_실제) as avg_bidders,
            AVG(입찰자수) as avg_bidders_announced,
            COUNT(*) as count
        FROM predictions
        WHERE actual_price > 0
          AND 감정가 > 0
        GROUP BY region_group
        HAVING count >= 10
        ORDER BY count DESC
    """, conn)

    conn.close()

    # 딕셔너리로 변환
    region_dict = {}
    for _, row in region_stats.iterrows():
        region_dict[row['region_group']] = {
            'avg_ratio': row['avg_ratio'],
            'avg_bidders': row['avg_bidders'] if pd.notna(row['avg_bidders']) else 0,
            'avg_bidders_announced': row['avg_bidders_announced'] if pd.notna(row['avg_bidders_announced']) else 0,
            'count': row['count']
        }

    # 저장
    output_path = MODELS_DIR / "pattern_region.pkl"
    joblib.dump(region_dict, output_path)

    logger.info(f"✅ 지역 개수: {len(region_dict)}")
    logger.info(f"✅ 저장 경로: {output_path}")

    # 샘플 출력
    logger.info("\n지역별 통계:")
    for region, stats in sorted(region_dict.items(), key=lambda x: x[1]['count'], reverse=True):
        logger.info(f"  {region}: 평균 낙찰률={stats['avg_ratio']:.3f}, 건수={stats['count']}")

    return region_dict


def create_complex_pattern():
    """
    패턴 3: 지역 × 물건종류 × 경매회차 복합 패턴
    예: 서울 아파트 3회차 평균 낙찰률 = 0.68
    """
    logger.info("\n" + "=" * 60)
    logger.info("패턴 3: 복합 패턴 (지역 × 물건종류 × 회차) 생성")
    logger.info("=" * 60)

    conn = sqlite3.connect(DB_PATH)

    complex_pattern = pd.read_sql_query("""
        SELECT
            CASE
                WHEN 지역 LIKE '%서울%' THEN '서울'
                WHEN 지역 LIKE '%경기%' THEN '경기'
                WHEN 지역 LIKE '%인천%' THEN '인천'
                WHEN 지역 LIKE '%부산%' THEN '부산'
                WHEN 지역 LIKE '%대구%' THEN '대구'
                WHEN 지역 LIKE '%대전%' THEN '대전'
                ELSE '기타'
            END as region_group,
            CASE
                WHEN 물건종류 LIKE '%아파트%' THEN '아파트'
                WHEN 물건종류 LIKE '%오피스텔%' THEN '오피스텔'
                WHEN 물건종류 LIKE '%다세대%' OR 물건종류 LIKE '%연립%' THEN '다세대'
                WHEN 물건종류 LIKE '%단독%' THEN '단독주택'
                WHEN 물건종류 LIKE '%상가%' OR 물건종류 LIKE '%점포%' THEN '상가'
                ELSE '기타'
            END as property_category,
            경매회차,
            AVG(actual_price * 1.0 / 감정가) as avg_ratio,
            COUNT(*) as count
        FROM predictions
        WHERE actual_price > 0
          AND 감정가 > 0
        GROUP BY region_group, property_category, 경매회차
        HAVING count >= 3
        ORDER BY count DESC
    """, conn)

    conn.close()

    # 딕셔너리로 변환
    pattern_3d = {}
    for _, row in complex_pattern.iterrows():
        key = f"{row['region_group']}_{row['property_category']}_{row['경매회차']}"
        pattern_3d[key] = {
            'avg_ratio': row['avg_ratio'],
            'count': row['count']
        }

    # 저장
    output_path = MODELS_DIR / "pattern_complex.pkl"
    joblib.dump(pattern_3d, output_path)

    logger.info(f"✅ 복합 패턴 개수: {len(pattern_3d)}")
    logger.info(f"✅ 저장 경로: {output_path}")

    # 샘플 출력
    logger.info("\n샘플 복합 패턴 (상위 20개):")
    sorted_patterns = sorted(pattern_3d.items(), key=lambda x: x[1]['count'], reverse=True)
    for i, (key, value) in enumerate(sorted_patterns[:20]):
        logger.info(f"  {key}: 평균={value['avg_ratio']:.3f}, 건수={value['count']}")

    return pattern_3d


def main():
    """모든 패턴 테이블 생성"""
    logger.info("=" * 60)
    logger.info("패턴 테이블 생성 시작")
    logger.info("=" * 60)

    # 1. 물건종류 × 경매회차
    pattern_property_round = create_property_round_pattern()

    # 2. 지역별 통계
    region_stats = create_region_stats()

    # 3. 복합 패턴
    complex_pattern = create_complex_pattern()

    logger.info("\n" + "=" * 60)
    logger.info("✅ 모든 패턴 테이블 생성 완료!")
    logger.info("=" * 60)
    logger.info(f"\n생성된 파일:")
    logger.info(f"  - models/pattern_property_round.pkl ({len(pattern_property_round)} 패턴)")
    logger.info(f"  - models/pattern_region.pkl ({len(region_stats)} 지역)")
    logger.info(f"  - models/pattern_complex.pkl ({len(complex_pattern)} 복합 패턴)")

    logger.info(f"\n다음 단계:")
    logger.info(f"  1. train_model_v4.py 실행")
    logger.info(f"  2. 모델 재훈련")
    logger.info(f"  3. 정확도 비교 (v3 vs v4)")


if __name__ == "__main__":
    main()
