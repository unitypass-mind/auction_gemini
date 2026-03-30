"""패턴 테이블 구조 확인"""
import joblib
from pathlib import Path

pattern_files = {
    "property_round": "models/pattern_property_round.pkl",
    "region": "models/pattern_region.pkl",
    "complex": "models/pattern_complex.pkl"
}

for name, path in pattern_files.items():
    data = joblib.load(Path(path))
    print(f"\n{name}:")
    print(f"  Type: {type(data)}")
    print(f"  Length: {len(data)}")

    # 처음 3개 항목 출력
    items = list(data.items())[:3] if isinstance(data, dict) else data[:3]
    print(f"  First 3 items:")
    for item in items:
        print(f"    {item}")
