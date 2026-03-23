import requests
import json

# 동일한 조건에서 면적만 변화시켜 테스트
base_params = {
    'start_price': 200000000,  # 감정가 2억
    'property_type': '아파트',
    'region': '서울',
    'auction_round': 1,
    'bidders': 10
}

# 테스트할 면적들 (㎡)
test_areas = [40, 60, 85, 100, 120, 150, 200]

print("=" * 100)
print(f"AI 예측 - 면적별 낙찰가 변화 분석")
print(f"고정 조건: 감정가 {base_params['start_price']:,}원, {base_params['property_type']}, {base_params['region']}, {base_params['auction_round']}회차")
print("=" * 100)
print()

results = []

for area in test_areas:
    params = base_params.copy()
    params['area'] = area

    url = "https://auction-ai.kr/predict"
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        predicted = data.get('predicted_price', 0)

        # 평당가 계산 (1평 = 3.3㎡)
        pyeong = area / 3.3
        price_per_pyeong = predicted / pyeong if pyeong > 0 else 0

        results.append({
            'area_m2': area,
            'area_pyeong': pyeong,
            'predicted': predicted,
            'price_per_pyeong': price_per_pyeong,
            'price_per_m2': predicted / area if area > 0 else 0
        })

        print(f"면적 {area:3d}㎡ ({pyeong:5.1f}평) → 예측가: {predicted:,}원 | 평당가: {price_per_pyeong:,.0f}원 | ㎡당: {predicted/area:,.0f}원")
    else:
        print(f"면적 {area}㎡ - API 호출 실패: {response.status_code}")

print()
print("=" * 100)
print("분석 결과:")
print("=" * 100)

if len(results) >= 2:
    # 기준점 (85㎡) 대비 변화율 계산
    base_idx = next((i for i, r in enumerate(results) if r['area_m2'] == 85), 0)
    base_result = results[base_idx]

    print(f"\n기준: 85㎡ (25.8평) - 예측가 {base_result['predicted']:,}원")
    print()

    for r in results:
        area_diff_pct = ((r['area_m2'] - base_result['area_m2']) / base_result['area_m2'] * 100) if base_result['area_m2'] > 0 else 0
        price_diff_pct = ((r['predicted'] - base_result['predicted']) / base_result['predicted'] * 100) if base_result['predicted'] > 0 else 0

        # 면적 변화 대비 가격 변화 비율
        elasticity = price_diff_pct / area_diff_pct if area_diff_pct != 0 else 0

        if r['area_m2'] != base_result['area_m2']:
            print(f"면적 {r['area_m2']:3d}㎡: 면적 {area_diff_pct:+6.1f}% → 예측가 {price_diff_pct:+6.1f}% (탄력성: {elasticity:.3f})")

    print()
    print("💡 탄력성 해석:")
    print("  - 탄력성 1.0: 면적이 10% 증가하면 예측가도 10% 증가")
    print("  - 탄력성 0.5: 면적이 10% 증가하면 예측가는 5% 증가")
    print("  - 탄력성 0.1: 면적의 영향이 매우 작음")

    # 평균 탄력성 계산
    elasticities = []
    for r in results:
        if r['area_m2'] != base_result['area_m2']:
            area_diff_pct = ((r['area_m2'] - base_result['area_m2']) / base_result['area_m2'] * 100)
            price_diff_pct = ((r['predicted'] - base_result['predicted']) / base_result['predicted'] * 100)
            if area_diff_pct != 0:
                elasticities.append(price_diff_pct / area_diff_pct)

    if elasticities:
        avg_elasticity = sum(elasticities) / len(elasticities)
        print(f"\n평균 탄력성: {avg_elasticity:.3f}")
        print(f"→ 면적이 10% 변화하면 예측가는 약 {avg_elasticity * 10:.1f}% 변화")

print()
print("=" * 100)
print("Feature Importance vs 실제 영향:")
print("=" * 100)
print("- Feature Importance (모델 가중치): 면적 관련 특성 약 2.45%")
print("- 실제 영향 (탄력성): 위 계산 결과 참조")
print()
print("※ Feature importance는 모델 내부 가중치이고,")
print("  실제 탄력성은 사용자 입력값 변화에 따른 예측가 변화율입니다.")
