import joblib

# 모델 로드
model_data = joblib.load('models/auction_model_v4.pkl')

model = model_data['model']
feature_names = model_data.get('feature_names', [])

print(f"=== XGBoost v4 모델 특성 정보 ===")
print(f"총 특성 개수: {len(feature_names)}")
print()

# Feature importance 가져오기
importance = model.feature_importances_

# 리스트로 정리
features_with_importance = []
for name, imp in zip(feature_names, importance):
    features_with_importance.append({
        '특성명': name,
        '중요도': imp,
        '중요도(%)': imp * 100
    })

# 중요도 순으로 정렬
features_with_importance.sort(key=lambda x: x['중요도'], reverse=True)

print("=== 변수별 중요도 (상위 20개) ===")
print()
for item in features_with_importance[:20]:
    print(f"{item['특성명']:30s} : {item['중요도(%)']:6.2f}%")

print()
print("=== 전체 변수별 중요도 ===")
print()
for item in features_with_importance:
    bar = '█' * int(item['중요도(%)'] * 2)
    print(f"{item['특성명']:30s} : {item['중요도(%)']:6.2f}% {bar}")

print()
print("=== 중요도 합계 확인 ===")
total = sum(item['중요도(%)'] for item in features_with_importance)
print(f"총 합계: {total:.2f}%")
