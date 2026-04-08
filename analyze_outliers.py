"""
통계용 이상치 분석 스크립트

현재 DB의 검증 데이터를 분석해서 이상치 기준별 효과를 미리 확인합니다.
"""
import sqlite3
import numpy as np
from pathlib import Path

DB_PATH = Path("data/predictions.db")
conn = sqlite3.connect(DB_PATH)

print("=" * 70)
print("DB 이상치 분석")
print("=" * 70)

# ── 전체 현황 ────────────────────────────────────────────────────────────
cur = conn.cursor()
cur.execute("""
    SELECT
        COUNT(*) as total,
        COUNT(CASE WHEN verified=1 THEN 1 END) as verified,
        COUNT(CASE WHEN verified=1 AND actual_price > 0 THEN 1 END) as has_actual
    FROM predictions
""")
r = cur.fetchone()
print(f"\n[전체 현황]")
print(f"  전체 레코드   : {r[0]:,}건")
print(f"  검증 완료     : {r[1]:,}건")
print(f"  실제 낙찰가 有 : {r[2]:,}건")

# ── 오차율 분포 ───────────────────────────────────────────────────────────
cur.execute("""
    SELECT error_rate
    FROM predictions
    WHERE verified=1 AND actual_price > 0 AND error_rate IS NOT NULL
    ORDER BY error_rate
""")
rates = [row[0] for row in cur.fetchall()]
print(f"\n[오차율 분포] ({len(rates)}건)")
percentiles = [25, 50, 75, 90, 95, 99]
for p in percentiles:
    print(f"  {p}th 백분위: {np.percentile(rates, p):.2f}%")
print(f"  평균          : {np.mean(rates):.2f}%")
print(f"  최대          : {np.max(rates):.2f}%")

q1, q3 = np.percentile(rates, 25), np.percentile(rates, 75)
iqr = q3 - q1
iqr_upper = q3 + 1.5 * iqr
print(f"  IQR 상한 (Q3+1.5×IQR): {iqr_upper:.2f}%")

# ── 낙찰률 분포 ───────────────────────────────────────────────────────────
cur.execute("""
    SELECT
        ROUND(actual_price * 100.0 / 감정가, 2) as 낙찰률,
        error_rate,
        감정가,
        물건종류,
        경매회차
    FROM predictions
    WHERE verified=1 AND actual_price > 0 AND 감정가 > 0
""")
rows = cur.fetchall()
win_rates = [r[0] for r in rows]
print(f"\n[낙찰률 분포] ({len(win_rates)}건)")
for p in [5, 10, 25, 50, 75, 90, 95]:
    print(f"  {p}th 백분위: {np.percentile(win_rates, p):.1f}%")

# ── 필터 기준별 효과 비교 ─────────────────────────────────────────────────
print(f"\n[필터 기준별 효과 비교]")
print(f"  {'기준':<35} {'남는 건수':>8} {'avg 오차':>9} {'median 오차':>12}")
print(f"  {'-'*68}")

criteria = [
    ("필터 없음",
     "error_rate IS NOT NULL"),
    ("오차율 ≤ 100%",
     "error_rate <= 100"),
    ("오차율 ≤ 50%",
     "error_rate <= 50"),
    ("낙찰률 40~150%",
     "actual_price*100.0/감정가 BETWEEN 40 AND 150"),
    ("낙찰률 40~150% + 오차 ≤ 100%",
     "actual_price*100.0/감정가 BETWEEN 40 AND 150 AND error_rate <= 100"),
    ("낙찰률 50~130% + 오차 ≤ 50%",
     "actual_price*100.0/감정가 BETWEEN 50 AND 130 AND error_rate <= 50"),
    (f"IQR 기반 (오차 ≤ {iqr_upper:.0f}%)",
     f"error_rate <= {iqr_upper:.2f}"),
    ("경매회차 ≤ 4 + 낙찰률 40~150%",
     "경매회차 <= 4 AND actual_price*100.0/감정가 BETWEEN 40 AND 150"),
]

for label, where in criteria:
    cur.execute(f"""
        SELECT COUNT(*), AVG(error_rate), error_rate
        FROM predictions
        WHERE verified=1 AND actual_price > 0 AND 감정가 > 0 AND {where}
        ORDER BY error_rate
    """)
    # 중앙값은 별도 계산
    cur2 = conn.cursor()
    cur2.execute(f"""
        SELECT error_rate FROM predictions
        WHERE verified=1 AND actual_price > 0 AND 감정가 > 0 AND {where}
        ORDER BY error_rate
    """)
    subset = [r[0] for r in cur2.fetchall()]
    if not subset:
        continue
    avg_e = np.mean(subset)
    med_e = np.median(subset)
    print(f"  {label:<35} {len(subset):>8,}건 {avg_e:>8.2f}% {med_e:>11.2f}%")

# ── 이상치 샘플 확인 ──────────────────────────────────────────────────────
print(f"\n[이상치 샘플 - 낙찰률 < 40% 또는 > 150%]")
cur.execute("""
    SELECT case_no, 감정가, actual_price, error_rate,
           ROUND(actual_price * 100.0 / 감정가, 1) as 낙찰률,
           물건종류, 경매회차
    FROM predictions
    WHERE verified=1 AND actual_price > 0 AND 감정가 > 0
      AND (actual_price * 100.0 / 감정가 < 40
           OR actual_price * 100.0 / 감정가 > 150)
    ORDER BY error_rate DESC
    LIMIT 10
""")
rows = cur.fetchall()
print(f"  {'사건번호':<22} {'감정가':>10} {'낙찰가':>10} {'낙찰률':>7} {'오차율':>7} {'종류'}")
for r in rows:
    print(f"  {r[0]:<22} {r[1]//10000:>8,}만 {r[2]//10000:>8,}만 {r[4]:>6.1f}% {r[3]:>6.1f}%  {r[5]}")

# ── 최종 추천 ─────────────────────────────────────────────────────────────
print(f"\n[추천 필터 적용 시 예상 결과]")
recommend = "actual_price*100.0/감정가 BETWEEN 40 AND 150 AND error_rate <= 100"
cur.execute(f"""
    SELECT error_rate FROM predictions
    WHERE verified=1 AND actual_price > 0 AND 감정가 > 0 AND {recommend}
    ORDER BY error_rate
""")
rec = [r[0] for r in cur.fetchall()]
print(f"  남는 데이터 : {len(rec):,}건 (현재 대비 제거: {len(rates)-len(rec)}건)")
print(f"  평균 오차율 : {np.mean(rec):.2f}%")
print(f"  중앙값 오차율: {np.median(rec):.2f}%")
print(f"  10% 이내   : {sum(1 for e in rec if e<=10)/len(rec)*100:.1f}%")
print(f"  20% 이내   : {sum(1 for e in rec if e<=20)/len(rec)*100:.1f}%")

conn.close()
print("\n=== 분석 완료 ===")
