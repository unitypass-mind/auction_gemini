"""
valueauction_collected 데이터를 v4 모델로 재예측

- source='valueauction_collected' 인 1,113건
- 단순 공식(감정가×0.7) → v4 XGBoost 모델로 교체
- predicted_price / error_amount / error_rate / model_used 업데이트
"""
import sqlite3
import numpy as np
import joblib
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

DB_PATH       = Path("data/predictions.db")
MODEL_V4_PATH = Path("models/auction_model_v4.pkl")
PATTERN_PR    = Path("models/pattern_property_round.pkl")
PATTERN_REG   = Path("models/pattern_region.pkl")
PATTERN_CMP   = Path("models/pattern_complex.pkl")

# ── 모델 & 패턴 로드 ──────────────────────────────────────────────────────
logger.info("모델 및 패턴 테이블 로드 중...")
model = joblib.load(MODEL_V4_PATH)
pattern_pr  = joblib.load(PATTERN_PR)  if PATTERN_PR.exists()  else None
pattern_reg = joblib.load(PATTERN_REG) if PATTERN_REG.exists() else None
pattern_cmp = joblib.load(PATTERN_CMP) if PATTERN_CMP.exists() else None
logger.info("로드 완료")

# ── v4 피처 생성 ──────────────────────────────────────────────────────────
def calc_lowest(start_price, auction_round):
    return int(start_price * (0.8 ** auction_round))

def make_v4_features(row):
    start_price  = float(row['감정가'] or 0)
    prop_type    = str(row['물건종류'] or '기타')
    region       = str(row['지역'] or '기타')
    area         = float(row['면적'] or 85.0) or 85.0
    rnd          = int(row['경매회차'] or 1)
    bidders      = int(row['입찰자수'] or 0)
    bidders_act  = int(row['입찰자수_실제'] or bidders)
    share_floor  = float(row['공유지분_건물'] or 0)
    share_land   = float(row['공유지분_토지'] or 0)
    debt_ratio   = float(row['청구금액비율'] or 0)
    second_price = max(0, int(row['second_price'] or 0))

    lowest       = calc_lowest(start_price, rnd)
    lowest_ratio = lowest / start_price if start_price > 0 else 0.8

    f = []
    # 1. 기본 가격
    f += [start_price, np.log1p(start_price),
          lowest, np.log1p(lowest), lowest_ratio]
    # 2. 물건종류 원핫
    for pt in ['아파트','다세대','단독주택','오피스텔','토지','상가','기타']:
        f.append(1 if pt in prop_type else 0)
    # 3. 지역 원핫
    matched = False
    for r in ['서울','경기','인천','부산','대구','대전','광주','울산','세종']:
        if r in region:
            f.append(1); matched = True
        else:
            f.append(0)
    f.append(0 if matched else 1)
    # 4. 면적
    f += [area, np.log1p(area),
          start_price/area if area > 0 else 0,
          np.log1p(start_price/area) if area > 0 else 0]
    # 5. 경매 진행
    f += [rnd, np.log1p(rnd), bidders, bidders_act, np.log1p(bidders_act)]
    # 6. 공유지분 & 부채
    f += [share_floor, share_land, debt_ratio, np.log1p(debt_ratio)]
    # 7. 2순위 가격
    f += [second_price, np.log1p(second_price),
          second_price/start_price if start_price > 0 and second_price > 0 else 0]
    # 8. 최저입찰가 상호작용
    f += [lowest_ratio*rnd, lowest_ratio*bidders_act,
          lowest*bidders_act, np.log1p(lowest_ratio*rnd)]
    # 9. 고급 상호작용
    f += [start_price*rnd, start_price*bidders_act, area*rnd,
          (start_price/area if area > 0 else 0)*rnd,
          bidders_act/rnd if rnd > 0 else bidders_act,
          share_floor+share_land, debt_ratio*rnd]
    # 10. 다항
    f += [start_price**2, area**2, rnd**2, bidders_act**2]

    # 11. 패턴 (v4)
    prop_cat = '기타'
    for k, v in [('아파트','아파트'),('오피스텔','오피스텔'),
                 ('다세대','다세대'),('연립','다세대'),('단독','단독주택'),
                 ('상가','상가'),('점포','상가'),('토지','토지')]:
        if k in prop_type: prop_cat = v; break

    reg_grp = '기타'
    for r in ['서울','경기','인천','부산','대구','대전','광주','울산','세종',
              '강원','충북','충남','전북','전남','경북','경남','제주']:
        if r in region: reg_grp = r; break

    pr_key    = f"{prop_cat}_{rnd}"
    pr_ratio  = pattern_pr.get(pr_key,  {}).get('avg_ratio', 0.5) if pattern_pr  else 0.5
    reg_ratio = pattern_reg.get(reg_grp, {}).get('avg_ratio', 0.5) if pattern_reg else 0.5
    cmp_key   = f"{reg_grp}_{prop_cat}_{rnd}"
    cmp_ratio = pattern_cmp.get(cmp_key, {}).get('avg_ratio', 0.5) if pattern_cmp else 0.5

    f += [pr_ratio, reg_ratio, cmp_ratio,
          pr_ratio * reg_ratio,
          abs(pr_ratio - reg_ratio)]

    arr = np.array(f, dtype=np.float64)
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    return arr.reshape(1, -1)

# ── 대상 데이터 로드 ──────────────────────────────────────────────────────
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
    SELECT id, case_no, 감정가, 물건종류, 지역, 면적, 경매회차, 입찰자수,
           입찰자수_실제, 공유지분_건물, 공유지분_토지, 청구금액비율,
           second_price, actual_price
    FROM predictions
    WHERE source = 'valueauction_collected'
      AND actual_price > 0
      AND 감정가 > 0
""")
rows = cursor.fetchall()
logger.info(f"재예측 대상: {len(rows)}건")

# ── 재예측 & 업데이트 ────────────────────────────────────────────────────
updated = 0
skipped = 0

for row in rows:
    try:
        actual = int(row['actual_price'])
        if actual <= 0:
            skipped += 1
            continue

        features = make_v4_features(row)
        predicted = int(model.predict(features)[0])

        error_amount = abs(actual - predicted)
        error_rate   = round(error_amount / actual * 100, 4)

        cursor.execute("""
            UPDATE predictions
            SET predicted_price = ?,
                error_amount    = ?,
                error_rate      = ?,
                model_used      = 1,
                updated_at      = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (predicted, error_amount, error_rate, row['id']))
        updated += 1

    except Exception as e:
        logger.warning(f"id={row['id']} 오류: {e}")
        skipped += 1

conn.commit()
logger.info(f"업데이트 완료: {updated}건 / 스킵: {skipped}건")

# ── 결과 확인 ────────────────────────────────────────────────────────────
cursor.execute("""
    SELECT
        source,
        COUNT(*) as cnt,
        ROUND(AVG(CASE WHEN error_rate<=100
                        AND actual_price*100.0/감정가 BETWEEN 40 AND 150
                        THEN error_rate END), 2) as avg_err,
        ROUND(AVG(error_rate), 2) as avg_err_all
    FROM predictions
    WHERE verified=1 AND actual_price>0 AND 감정가>0
    GROUP BY source
""")
print("\n=== source별 오차율 ===")
for r in cursor.fetchall():
    print(f"  {r[0]:<30} {r[1]:>5}건  필터avg:{r[2]}%  전체avg:{r[3]}%")

# 전체 통계 (현재 API 필터 기준)
cursor.execute("""
    SELECT error_rate FROM predictions
    WHERE verified=1
      AND actual_price>0 AND 감정가>0
      AND error_rate<=100
      AND actual_price*100.0/감정가 BETWEEN 40 AND 150
    ORDER BY error_rate
""")
rates = [r[0] for r in cursor.fetchall()]
print(f"\n=== 전체 (필터 적용) ===")
print(f"  건수     : {len(rates):,}건")
print(f"  평균 오차 : {np.mean(rates):.2f}%")
print(f"  중앙값   : {np.median(rates):.2f}%")
print(f"  10% 이내 : {sum(1 for e in rates if e<=10)/len(rates)*100:.1f}%")
print(f"  20% 이내 : {sum(1 for e in rates if e<=20)/len(rates)*100:.1f}%")

conn.close()
print("\n=== 완료 ===")
