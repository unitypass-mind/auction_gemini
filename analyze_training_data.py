# -*- coding: utf-8 -*-
import sqlite3
import pandas as pd

DB_PATH = "data/predictions.db"

conn = sqlite3.connect(DB_PATH)

# 전체 데이터 확인
df_all = pd.read_sql_query("SELECT * FROM predictions LIMIT 5", conn)
print("=" * 80)
print("데이터베이스 스키마 (샘플 5개)")
print("=" * 80)
print(df_all.head())

# 낙찰 데이터만 (actual_price > 0)
df = pd.read_sql_query("""
    SELECT
        감정가, 물건종류, 지역, 면적, 경매회차, 입찰자수, actual_price
    FROM predictions
    WHERE actual_price IS NOT NULL AND actual_price > 0
""", conn)

print("\n" + "=" * 80)
print(f"학습 데이터 통계 (전체 {len(df)}건)")
print("=" * 80)

print(f"\n총 데이터 수: {len(df)}건")

# 지역별 분포
print("\n[지역별 분포]")
region_dist = df['지역'].value_counts()
print(region_dist.head(15))
print(f"고유 지역 수: {df['지역'].nunique()}개")

# 물건종류별 분포
print("\n[물건종류별 분포]")
property_dist = df['물건종류'].value_counts()
print(property_dist.head(15))
print(f"고유 물건종류 수: {df['물건종류'].nunique()}개")

# 면적 분포
print("\n[면적 분포]")
print(df['면적'].describe())

# 감정가 분포
print("\n[감정가 분포]")
print(df['감정가'].describe())

# 낙찰률 계산
df['낙찰률'] = (df['actual_price'] / df['감정가'] * 100).round(1)

print("\n[낙찰률 분포]")
print(df['낙찰률'].describe())

# 지역별 평균 낙찰률
print("\n[지역별 평균 낙찰률 TOP 10]")
region_rate = df.groupby('지역').agg({
    'actual_price': 'count',
    '낙찰률': 'mean'
}).round(1)
region_rate.columns = ['건수', '평균낙찰률(%)']
region_rate = region_rate[region_rate['건수'] >= 5]  # 5건 이상만
region_rate = region_rate.sort_values('평균낙찰률(%)', ascending=False)
print(region_rate.head(10))

# 물건종류별 평균 낙찰률
print("\n[물건종류별 평균 낙찰률]")
property_rate = df.groupby('물건종류').agg({
    'actual_price': 'count',
    '낙찰률': 'mean'
}).round(1)
property_rate.columns = ['건수', '평균낙찰률(%)']
property_rate = property_rate[property_rate['건수'] >= 3]
property_rate = property_rate.sort_values('평균낙찰률(%)', ascending=False)
print(property_rate.head(15))

# 데이터 편향성 확인
print("\n" + "=" * 80)
print("데이터 편향성 분석")
print("=" * 80)

total = len(df)
top_region = region_dist.iloc[0]
top_region_name = region_dist.index[0]
top_region_pct = (top_region / total * 100)

print(f"\n최다 지역: {top_region_name} ({top_region}건, {top_region_pct:.1f}%)")

top_property = property_dist.iloc[0]
top_property_name = property_dist.index[0]
top_property_pct = (top_property / total * 100)

print(f"최다 물건종류: {top_property_name} ({top_property}건, {top_property_pct:.1f}%)")

if top_region_pct > 80:
    print(f"\n⚠️  경고: 지역 데이터가 {top_region_name}에 {top_region_pct:.1f}% 집중되어 있습니다!")
    print("   다른 지역의 패턴을 학습하기 어려울 수 있습니다.")

if top_property_pct > 80:
    print(f"\n⚠️  경고: 물건종류가 {top_property_name}에 {top_property_pct:.1f}% 집중되어 있습니다!")
    print("   다른 물건종류의 패턴을 학습하기 어려울 수 있습니다.")

conn.close()
