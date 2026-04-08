"""ValueAuction API 수집 가능량 확인"""
import requests, json, sqlite3

api_url = "https://valueauction.co.kr/api/search"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Referer": "https://valueauction.co.kr/search",
    "Origin": "https://valueauction.co.kr"
}

base_payload = {
    "limit": 50, "offset": 0,
    "order": "bidding_date", "direction": "desc",
    "category": {"residential": ["전체"], "commercial": [], "land": []},
    "priceRange": {
        "min_ask_price": {"min": 0, "max": None},
        "appraisal_price": {"min": 0, "max": None}
    },
    "areaRange": {
        "land_area": {"min": 0, "max": None},
        "building_area": {"min": 0, "max": None}
    },
    "addresses": {
        "pnu1": [], "pnu2": [], "pnu3": [],
        "address1": [], "address2": [], "address3": []
    },
    "all": False, "courts": [], "tags": {"mode": "exclude"}
}

# ── 현재 DB 상태 ──────────────────────────────────────────────────────────
conn = sqlite3.connect("data/predictions.db")
cur = conn.cursor()
cur.execute("SELECT COUNT(DISTINCT case_no) FROM predictions WHERE source='valueauction'")
va_in_db = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM predictions WHERE verified=1 AND actual_price>0")
verified_total = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM predictions WHERE source='valueauction' AND verified=1")
va_verified = cur.fetchone()[0]
cur.execute("SELECT DISTINCT case_no FROM predictions")
existing_cases = set(r[0] for r in cur.fetchall())
conn.close()

print("=" * 60)
print("현재 DB 상태")
print("=" * 60)
print(f"  VA 수집 데이터  : {va_in_db:,}건")
print(f"  VA 검증 완료    : {va_verified:,}건")
print(f"  전체 검증 완료  : {verified_total:,}건")

# ── API 총 건수 확인 ──────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("ValueAuction API 수집 가능량")
print("=" * 60)

price_ranges = [
    ("전체",      0),
    ("1억 이상",  100_000_000),
    ("3억 이상",  300_000_000),
    ("10억 이상", 1_000_000_000),
]

for label, min_p in price_ranges:
    p = json.loads(json.dumps(base_payload))
    p["limit"] = 1
    p["priceRange"]["appraisal_price"]["min"] = min_p
    try:
        res = requests.post(api_url, json=p, headers=headers, timeout=15)
        total = res.json().get("total", 0)
        print(f"  감정가 {label:<8}: {total:,}건")
    except Exception as e:
        print(f"  감정가 {label:<8}: 오류 - {e}")

# ── 낙찰 완료 비율 및 신규 건수 확인 ─────────────────────────────────────
print("\n" + "=" * 60)
print("낙찰 완료 비율 분석 (최신 50건 샘플)")
print("=" * 60)

try:
    res = requests.post(api_url, json=base_payload, headers=headers, timeout=15)
    rdata = res.json()
    results = rdata.get("results", [])
    total_api = rdata.get("total", 0)

    sold_items = []
    not_sold = 0
    new_sold = 0

    for r in results:
        histories = r.get("histories", [])
        winning_info = None
        for h in reversed(histories):
            if h.get("winning_info"):
                winning_info = h["winning_info"]
                break

        selling_price = int(r.get("price", {}).get("selling_price", 0))
        is_sold = winning_info is not None or selling_price > 0

        if is_sold:
            sold_items.append(r)
            case_name = r["case"].get("name", "")
            va_key = "VA-" + str(r["case"]["id"])
            if case_name not in existing_cases and va_key not in existing_cases:
                new_sold += 1
        else:
            not_sold += 1

    sold_ratio = len(sold_items) / len(results) * 100 if results else 0
    est_total_sold = int(total_api * sold_ratio / 100)

    print(f"  샘플 {len(results)}건 중:")
    print(f"    낙찰 완료   : {len(sold_items)}건 ({sold_ratio:.0f}%)")
    print(f"    낙찰 미완료 : {not_sold}건")
    print(f"    신규 낙찰   : {new_sold}건 (DB 미등록)")
    print(f"\n  전체 {total_api:,}건 기준 추정:")
    print(f"    낙찰 완료 추정   : {est_total_sold:,}건")
    print(f"    현재 DB 등록     : {va_in_db:,}건")
    print(f"    추가 수집 가능   : ~{max(0, est_total_sold - va_in_db):,}건")

    # 최신 낙찰 건 샘플 출력
    print("\n  [최신 낙찰 건 샘플]")
    for item in sold_items[:5]:
        case_name = item["case"].get("name", "-")
        ap = int(item.get("price", {}).get("appraised_price", 0))
        hist = item.get("histories", [])
        win = None
        for h in reversed(hist):
            if h.get("winning_info"):
                win = h["winning_info"]
                break
        sp = int(win.get("winning_price", 0)) if win else int(item.get("price", {}).get("selling_price", 0))
        bidders = win.get("bidders_count", 0) if win else 0
        ratio = sp / ap * 100 if ap > 0 else 0
        print(f"    {case_name:<22} 감정가:{ap//10000:,}만 낙찰가:{sp//10000:,}만 ({ratio:.1f}%) 입찰자:{bidders}명")

except Exception as e:
    print(f"  오류: {e}")

print("\n=== 확인 완료 ===")
