"""
v4 모델 로딩 테스트
"""
import joblib
from pathlib import Path

model_v4_path = Path("models/auction_model_v4.pkl")
pattern_property_round_path = Path("models/pattern_property_round.pkl")
pattern_region_path = Path("models/pattern_region.pkl")
pattern_complex_path = Path("models/pattern_complex.pkl")

print("=== v4 Model Loading Test ===\n")

# 1. v4 모델 로드
if model_v4_path.exists():
    try:
        model = joblib.load(model_v4_path)
        print(f"[OK] v4 model loaded successfully")
        print(f"  - Path: {model_v4_path}")
        print(f"  - Type: {type(model)}")

        # 모델 특성 확인
        if hasattr(model, 'n_features_in_'):
            print(f"  - Features: {model.n_features_in_}")

        if hasattr(model, 'feature_importances_'):
            print(f"  - Top 5 feature importances:")
            top_indices = model.feature_importances_.argsort()[-5:][::-1]
            for i, idx in enumerate(top_indices, 1):
                print(f"    {i}. Feature {idx}: {model.feature_importances_[idx]:.4f}")

    except Exception as e:
        print(f"[ERROR] v4 model load failed: {e}")
else:
    print(f"[ERROR] v4 model file not found: {model_v4_path}")

print()

# 2. 패턴 테이블 로드
patterns = {
    "property_round": pattern_property_round_path,
    "region": pattern_region_path,
    "complex": pattern_complex_path
}

for name, path in patterns.items():
    if path.exists():
        try:
            data = joblib.load(path)
            print(f"[OK] {name} pattern loaded: {len(data)} items")
        except Exception as e:
            print(f"[ERROR] {name} pattern load failed: {e}")
    else:
        print(f"[ERROR] {name} pattern file not found: {path}")

print("\n=== 테스트 완료 ===")
