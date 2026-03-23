# -*- coding: utf-8 -*-
import requests
import json
import urllib3
urllib3.disable_warnings()

url = 'https://49.50.131.190/predict/simple'

def test_prediction(name, data):
    """예측 테스트"""
    response = requests.post(url, json=data, verify=False, timeout=30)
    result = response.json()

    if result.get('success'):
        pred = result['data']['predicted_price']
        ratio = result['data']['bid_ratio']
        return pred, ratio
    else:
        return None, None

# 기준값
base_data = {
    'start_price': 300000000,
    'property_type': '아파트',
    'region': '서울',
    'area': 84.0,
    'auction_round': 1
}

print("=" * 80)
print("AI 예측 모델 변수별 민감도 테스트")
print("=" * 80)

# 1. 지역별 테스트
print("\n[1] 지역별 차이 테스트 (감정가 3억, 아파트 84㎡, 1회차)")
print("-" * 80)
regions = ['서울', '인천', '경기', '부산', '대구']
region_results = {}

for region in regions:
    data = base_data.copy()
    data['region'] = region
    pred, ratio = test_prediction(region, data)
    region_results[region] = pred
    print(f"{region:6s}: 예측 {pred:,}원 (낙찰률 {ratio:.1f}%)")

# 지역별 차이 분석
print("\n지역별 차이 분석:")
seoul_price = region_results['서울']
for region, price in region_results.items():
    if region != '서울':
        diff = price - seoul_price
        diff_pct = (diff / seoul_price * 100) if seoul_price else 0
        print(f"  {region} vs 서울: {diff:+,}원 ({diff_pct:+.2f}%)")

# 2. 물건종류별 테스트
print("\n[2] 물건종류별 차이 테스트 (감정가 3억, 서울 84㎡, 1회차)")
print("-" * 80)
property_types = ['아파트', '오피스텔', '다세대', '단독주택']
property_results = {}

for ptype in property_types:
    data = base_data.copy()
    data['property_type'] = ptype
    pred, ratio = test_prediction(ptype, data)
    property_results[ptype] = pred
    print(f"{ptype:8s}: 예측 {pred:,}원 (낙찰률 {ratio:.1f}%)")

# 3. 면적별 테스트
print("\n[3] 면적별 차이 테스트 (감정가 3억, 서울 아파트, 1회차)")
print("-" * 80)
areas = [59.0, 84.0, 110.0, 150.0]
area_results = {}

for area in areas:
    data = base_data.copy()
    data['area'] = area
    pred, ratio = test_prediction(f"{area}㎡", data)
    area_results[area] = pred
    평 = area / 3.3
    print(f"{area:5.0f}㎡ ({평:4.0f}평): 예측 {pred:,}원 (낙찰률 {ratio:.1f}%)")

# 4. 경매회차별 테스트
print("\n[4] 경매회차별 차이 테스트 (감정가 3억, 서울 아파트 84㎡)")
print("-" * 80)
rounds = [1, 2, 3]
round_results = {}

for round_num in rounds:
    data = base_data.copy()
    data['auction_round'] = round_num
    pred, ratio = test_prediction(f"{round_num}회차", data)
    round_results[round_num] = pred
    print(f"{round_num}회차: 예측 {pred:,}원 (낙찰률 {ratio:.1f}%)")

# 5. 감정가별 테스트
print("\n[5] 감정가별 차이 테스트 (서울 아파트 84㎡, 1회차)")
print("-" * 80)
prices = [100000000, 300000000, 500000000, 1000000000]
price_results = {}

for price in prices:
    data = base_data.copy()
    data['start_price'] = price
    pred, ratio = test_prediction(f"{price//100000000}억", data)
    price_results[price] = pred
    억 = price // 100000000
    print(f"감정가 {억:2d}억: 예측 {pred:,}원 (낙찰률 {ratio:.1f}%)")

# 종합 분석
print("\n" + "=" * 80)
print("종합 분석")
print("=" * 80)

# 각 변수별 변동 폭 계산
def calc_variation(results):
    values = list(results.values())
    if len(values) < 2:
        return 0
    return (max(values) - min(values)) / min(values) * 100

print(f"\n변수별 예측가 변동 폭:")
print(f"  지역:      {calc_variation(region_results):.2f}%")
print(f"  물건종류:  {calc_variation(property_results):.2f}%")
print(f"  면적:      {calc_variation(area_results):.2f}%")
print(f"  경매회차:  {calc_variation(round_results):.2f}%")
print(f"  감정가:    변동률은 금액에 비례하므로 생략")

print("\n결론:")
if calc_variation(region_results) < 0.1:
    print("  ⚠️  지역 변수가 예측에 거의 영향을 주지 않고 있습니다!")
else:
    print("  ✓ 지역 변수가 예측에 정상적으로 반영되고 있습니다.")

if calc_variation(property_results) < 0.1:
    print("  ⚠️  물건종류 변수가 예측에 거의 영향을 주지 않고 있습니다!")
else:
    print("  ✓ 물건종류 변수가 예측에 정상적으로 반영되고 있습니다.")
