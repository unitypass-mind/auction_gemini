"""
v4 vs v5 모델 성능 비교 스크립트

동일한 검증 데이터(실제 낙찰가 있는 레코드)로 두 모델의 예측 정확도를 비교합니다.
"""
import sqlite3
import numpy as np
import joblib
import pandas as pd
from pathlib import Path

DB_PATH       = Path("data/predictions.db")
MODEL_V4_PATH = Path("models/auction_model_v4.pkl")
MODEL_V5_PATH = Path("models/auction_model_v5.pkl")
ENCODERS_V5   = Path("encoders_v5.pkl")
PATTERN_PR    = Path("models/pattern_property_round.pkl")
PATTERN_REG   = Path("models/pattern_region.pkl")
PATTERN_CMP   = Path("models/pattern_complex.pkl")

print("=" * 70)
print("v4 vs v5 모델 성능 비교")
print("=" * 70)

# ── 모델 로드 ──────────────────────────────────────────────────────────────
print("\n[1/4] 모델 로드...")
model_v4 = joblib.load(MODEL_V4_PATH)
model_v5 = joblib.load(MODEL_V5_PATH)
enc      = joblib.load(ENCODERS_V5)
le_prop  = enc['property_encoder']
le_reg   = enc['region_encoder']

pattern_pr  = joblib.load(PATTERN_PR)  if PATTERN_PR.exists()  else None
pattern_reg = joblib.load(PATTERN_REG) if PATTERN_REG.exists() else None
pattern_cmp = joblib.load(PATTERN_CMP) if PATTERN_CMP.exists() else None

print(f"  v4 피처 수: 58개 (예상)")
print(f"  v5 피처 수: 6개")
print(f"  패턴테이블: {'로드됨' if pattern_pr else '없음'}")

# ── 검증 데이터 로드 ────────────────────────────────────────────────────────
print("\n[2/4] 검증 데이터 로드...")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

df = pd.read_sql_query("""
    SELECT id, case_no,
           감정가, 물건종류, 지역, 면적, 경매회차, 입찰자수,
           입찰자수_실제, 공유지분_건물, 공유지분_토지, 청구금액비율,
           second_price, actual_price,
           ROUND(actual_price * 100.0 / 감정가, 2) as 낙찰률
    FROM predictions
    WHERE verified = 1
      AND actual_price > 0
      AND 감정가 > 0
""", conn)
conn.close()

total = len(df)
print(f"  전체 검증 데이터: {total}건")

# 필터링된 데이터 (v5 훈련 분포 내)
df_filtered = df[
    (df['낙찰률'] >= 40) &
    (df['낙찰률'] <= 150) &
    (df['경매회차'] < 5) &
    (df['감정가'] >= 5000000)
].copy()
print(f"  v5 분포 내 데이터: {len(df_filtered)}건 (낙찰률 40~150%, 경매회차 1~4회)")
print(f"  분포 외 데이터   : {total - len(df_filtered)}건")

# ── v4 피처 생성 함수 ──────────────────────────────────────────────────────
def calc_lowest_price(start_price, auction_round):
    ratio = 0.8 ** auction_round
    return int(start_price * ratio)

def make_features_v4(row):
    start_price  = float(row['감정가'])
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
    lowest       = calc_lowest_price(start_price, rnd)
    lowest_ratio = lowest / start_price if start_price > 0 else 0.8

    f = []
    # 1. 기본 가격
    f += [start_price, np.log1p(start_price), lowest, np.log1p(lowest), lowest_ratio]
    # 2. 물건종류 원핫
    for pt in ['아파트','다세대','단독주택','오피스텔','토지','상가','기타']:
        f.append(1 if pt in prop_type else 0)
    # 3. 지역 원핫
    regions = ['서울','경기','인천','부산','대구','대전','광주','울산','세종','기타']
    matched = False
    for r in regions[:-1]:
        if r in region:
            f.append(1); matched = True
        else:
            f.append(0)
    f.append(0 if matched else 1)
    # 4. 면적
    f += [area, np.log1p(area),
          start_price/area if area>0 else 0,
          np.log1p(start_price/area) if area>0 else 0]
    # 5. 경매 진행
    f += [rnd, np.log1p(rnd), bidders, bidders_act, np.log1p(bidders_act)]
    # 6. 공유지분 & 부채
    f += [share_floor, share_land, debt_ratio, np.log1p(debt_ratio)]
    # 7. 2순위 가격
    f += [second_price, np.log1p(second_price),
          second_price/start_price if start_price>0 and second_price>0 else 0]
    # 8. 최저입찰가 상호작용
    f += [lowest_ratio * rnd, lowest_ratio * bidders_act,
          lowest * bidders_act, np.log1p(lowest_ratio * rnd)]
    # 9. 고급 상호작용
    f += [start_price * rnd, start_price * bidders_act, area * rnd,
          (start_price/area if area>0 else 0) * rnd,
          bidders_act/rnd if rnd>0 else bidders_act,
          share_floor + share_land, debt_ratio * rnd]
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

    pr_key   = f"{prop_cat}_{rnd}"
    pr_ratio = pattern_pr.get(pr_key, {}).get('avg_ratio', 0.5)  if pattern_pr  else 0.5
    reg_ratio= pattern_reg.get(reg_grp, {}).get('avg_ratio', 0.5) if pattern_reg else 0.5

    pr_pred  = start_price * pr_ratio
    reg_pred = start_price * reg_ratio
    combined = start_price * (pr_ratio * 0.5 + reg_ratio * 0.5)

    f += [pr_ratio, reg_ratio, pr_pred, reg_pred, combined]

    return np.array(f, dtype=np.float64)


# ── v5 피처 생성 함수 ──────────────────────────────────────────────────────
known_props = set(le_prop.classes_)
known_regs  = set(le_reg.classes_)

def make_features_v5(row):
    appraised = float(row['감정가'])
    area      = float(row['면적'] or 85.0) or 85.0
    rnd       = int(row['경매회차'] or 1)
    bidders   = int(row['입찰자수'] or 0)
    prop_type = str(row['물건종류'] or '기타')
    region    = str(row['지역'] or '기타')

    prop_enc = le_prop.transform([prop_type if prop_type in known_props else '기타'])[0]
    reg_enc  = le_reg.transform([region if region in known_regs else '기타'])[0]

    return np.array([[appraised, area, rnd, bidders, prop_enc, reg_enc]])


# ── 예측 및 오차 계산 ──────────────────────────────────────────────────────
def evaluate(df_eval, label):
    v4_errors, v5_errors = [], []
    v4_wins, v5_wins, ties = 0, 0, 0

    for _, row in df_eval.iterrows():
        actual = float(row['actual_price'])
        try:
            fv4   = make_features_v4(row).reshape(1, -1)
            pred4 = float(model_v4.predict(fv4)[0])
            err4  = abs(actual - pred4) / actual * 100
        except:
            err4 = None

        try:
            fv5   = make_features_v5(row)
            pred5 = float(model_v5.predict(fv5)[0])
            err5  = abs(actual - pred5) / actual * 100
        except:
            err5 = None

        if err4 is not None and err4 <= 100: v4_errors.append(err4)
        if err5 is not None and err5 <= 100: v5_errors.append(err5)

        if err4 is not None and err5 is not None and err4 <= 100 and err5 <= 100:
            if err4 < err5 - 1: v4_wins += 1
            elif err5 < err4 - 1: v5_wins += 1
            else: ties += 1

    print(f"\n  [{label}] {len(df_eval)}건")
    print(f"  {'항목':<20} {'v4':>10} {'v5':>10}")
    print(f"  {'-'*42}")
    print(f"  {'유효 예측 건수':<20} {len(v4_errors):>10} {len(v5_errors):>10}")
    if v4_errors:
        print(f"  {'평균 오차율':<20} {np.mean(v4_errors):>9.2f}% {np.mean(v5_errors) if v5_errors else 'N/A':>9}{'%' if v5_errors else ''}")
        print(f"  {'중앙값 오차율':<20} {np.median(v4_errors):>9.2f}% {np.median(v5_errors) if v5_errors else 'N/A':>9}{'%' if v5_errors else ''}")
        print(f"  {'10% 이내 비율':<20} {sum(1 for e in v4_errors if e<=10)/len(v4_errors)*100:>9.1f}% {sum(1 for e in v5_errors if e<=10)/len(v5_errors)*100 if v5_errors else 'N/A':>9}{'%' if v5_errors else ''}")
        print(f"  {'20% 이내 비율':<20} {sum(1 for e in v4_errors if e<=20)/len(v4_errors)*100:>9.1f}% {sum(1 for e in v5_errors if e<=20)/len(v5_errors)*100 if v5_errors else 'N/A':>9}{'%' if v5_errors else ''}")
        print(f"  {'v4 우세 케이스':<20} {v4_wins:>10}")
        print(f"  {'v5 우세 케이스':<20} {v5_wins:>10}")
        print(f"  {'비슷한 케이스':<20} {ties:>10}")
        winner = 'v4' if v4_wins > v5_wins else ('v5' if v5_wins > v4_wins else '동일')
        print(f"  >>> 승자: {winner}")
    return v4_errors, v5_errors


# ── 전체 데이터 비교 ──────────────────────────────────────────────────────
print("\n[3/4] 예측 비교 중...")
print("\n" + "=" * 70)
e4_all, e5_all = evaluate(df, "전체 검증 데이터")

print("\n" + "=" * 70)
e4_fil, e5_fil = evaluate(df_filtered, "v5 훈련 분포 내 데이터")

# ── 구간별 비교 ──────────────────────────────────────────────────────────
print("\n\n[4/4] 감정가 구간별 비교")
print("=" * 70)
ranges = [
    ('1억 이하',   0,         100_000_000),
    ('1억~3억',    100_000_000, 300_000_000),
    ('3억~5억',    300_000_000, 500_000_000),
    ('5억~10억',   500_000_000, 1_000_000_000),
    ('10억 초과',  1_000_000_000, 9_999_999_999),
]
for label, lo, hi in ranges:
    sub = df[(df['감정가'] >= lo) & (df['감정가'] < hi)]
    if len(sub) < 5:
        continue
    v4e, v5e = [], []
    for _, row in sub.iterrows():
        actual = float(row['actual_price'])
        try:
            pred4 = float(model_v4.predict(make_features_v4(row).reshape(1,-1))[0])
            e = abs(actual-pred4)/actual*100
            if e <= 100: v4e.append(e)
        except: pass
        try:
            pred5 = float(model_v5.predict(make_features_v5(row))[0])
            e = abs(actual-pred5)/actual*100
            if e <= 100: v5e.append(e)
        except: pass

    v4med = f"{np.median(v4e):.1f}%" if v4e else "N/A"
    v5med = f"{np.median(v5e):.1f}%" if v5e else "N/A"
    winner = ""
    if v4e and v5e:
        winner = " ← v4 우세" if np.median(v4e) < np.median(v5e) else " ← v5 우세"
    print(f"  {label:<10} ({len(sub):>4}건)  v4 중앙값:{v4med:>7}  v5 중앙값:{v5med:>7}{winner}")

print("\n=== 비교 완료 ===")
