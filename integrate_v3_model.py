"""
main.py에 v3 모델을 완전 통합하는 스크립트
"""
import re
from pathlib import Path

def integrate_v3():
    print("=" * 60)
    print("v3 모델 완전 통합 시작")
    print("=" * 60)

    # 1. 백업 생성
    with open("main.py", "r", encoding="utf-8") as f:
        main_content = f.read()

    with open("main.py.backup", "w", encoding="utf-8") as f:
        f.write(main_content)
    print("[OK] main.py 백업 완료: main.py.backup")

    # 2. v3 함수들 가져오기
    with open("train_model_v3_simple.py", "r", encoding="utf-8") as f:
        v3_content = f.read()

    # calc_lowest_price_by_round 함수 추출
    calc_match = re.search(
        r'(def calc_lowest_price_by_round\(.*?\):.*?)(?=\ndef [a-z]|\nclass |\nif __name__|$)',
        v3_content,
        re.DOTALL
    )
    calc_function = calc_match.group(1).strip() if calc_match else None

    # create_features_v3 함수 추출
    create_match = re.search(
        r'(def create_features_v3\(.*?\):.*?)(?=\ndef [a-z]|\nclass |\nif __name__|$)',
        v3_content,
        re.DOTALL
    )
    create_function = create_match.group(1).strip() if create_match else None

    if not calc_function or not create_function:
        print("❌ v3 함수를 찾을 수 없습니다!")
        return False

    print("✅ v3 함수 추출 완료")

    # 3. 모델 경로에 v3 추가
    main_content = re.sub(
        r'(# AI 모델 로드 \(v2 모델 우선\)\nmodel = None\n)',
        r'# AI 모델 로드 (v3 모델 우선)\nmodel = None\nmodel_v3_path = Path("models/auction_model_v3.pkl")\n',
        main_content
    )
    print("✅ 모델 경로에 v3 추가")

    # 4. load_model 함수 수정 - v3 우선
    old_load_model = r'def load_model\(\):\s*"""AI 모델을 로드하는 함수"""\s*global model, model_load_time\s*# v2 모델 먼저 시도'

    new_load_model = '''def load_model():
    """AI 모델을 로드하는 함수"""
    global model, model_load_time

    # v3 모델 먼저 시도
    if model_v3_path.exists():
        try:
            model = joblib.load(model_v3_path)
            model_load_time = datetime.now()
            logger.info(f"AI 모델 v3 로드 성공: {model_v3_path}")
            return True, "v3"
        except Exception as e:
            logger.error(f"AI 모델 v3 로드 실패: {e}")

    # v2 모델 먼저 시도'''

    main_content = re.sub(old_load_model, new_load_model, main_content, flags=re.MULTILINE)
    print("✅ load_model 함수에 v3 우선 로드 추가")

    # 5. create_features 함수 앞에 v3 함수들 삽입
    # create_features 함수의 위치 찾기
    create_features_pos = main_content.find("def create_features(")

    if create_features_pos == -1:
        print("❌ create_features 함수를 찾을 수 없습니다!")
        return False

    # v3 함수들을 삽입
    v3_section = f'''

# =============================
# v3 모델 전용 함수들
# =============================

{calc_function}


{create_function}


# =============================
# 기존 모델 함수들 (v1, v2)
# =============================

'''

    main_content = (
        main_content[:create_features_pos] +
        v3_section +
        main_content[create_features_pos:]
    )
    print("✅ v3 함수들 main.py에 추가")

    # 6. 저장
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(main_content)

    print("\n" + "=" * 60)
    print("✅ v3 모델 완전 통합 완료!")
    print("=" * 60)
    print("\n변경 사항:")
    print("  - model_v3_path 추가")
    print("  - load_model()에서 v3 우선 로드")
    print("  - calc_lowest_price_by_round() 함수 추가")
    print("  - create_features_v3() 함수 추가 (53개 특성)")
    print("\n다음 단계:")
    print("  1. 서버 재시작")
    print("  2. 브라우저에서 테스트")

    return True

if __name__ == "__main__":
    success = integrate_v3()
    if success:
        print("\n패치 적용 성공! 🎉")
    else:
        print("\n패치 적용 실패 ❌")
