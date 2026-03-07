"""
main.py에 v4 모델을 완전 통합하는 스크립트
v3 기반 + 패턴 특성 (물건×회차, 지역, 복합 패턴)
"""
import re
from pathlib import Path

def integrate_v4():
    print("=" * 60)
    print("v4 모델 완전 통합 시작")
    print("=" * 60)

    # 1. 백업 생성
    with open("main.py", "r", encoding="utf-8") as f:
        main_content = f.read()

    backup_path = "main.py.backup_before_v4"
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(main_content)
    print(f"[OK] main.py 백업 완료: {backup_path}")

    # 2. v4 함수들 가져오기
    with open("train_model_v4.py", "r", encoding="utf-8") as f:
        v4_content = f.read()

    # calc_lowest_price_by_round 함수 추출 (이미 있을 수 있음)
    calc_match = re.search(
        r'(def calc_lowest_price_by_round\(.*?\):.*?)(?=\ndef [a-z]|$)',
        v4_content,
        re.DOTALL
    )
    calc_function = calc_match.group(1).strip() if calc_match else None

    # create_features_v4 함수 추출
    create_match = re.search(
        r'(def create_features_v4\(.*?\):.*?)(?=\ndef [a-z]|$)',
        v4_content,
        re.DOTALL
    )
    create_function = create_match.group(1).strip() if create_match else None

    if not create_function:
        print("❌ v4 함수를 찾을 수 없습니다!")
        return False

    print("[OK] v4 함수 추출 완료")

    # 3. 모델 경로에 v4와 패턴 테이블 경로 추가
    # 기존 model_v3_path 바로 뒤에 추가
    old_model_section = r'(model_v3_path = Path\("models/auction_model_v3\.pkl"\))'
    new_model_section = r'\1\nmodel_v4_path = Path("models/auction_model_v4.pkl")\n\n# 패턴 테이블 경로\npattern_property_round = None\npattern_region = None\npattern_complex = None\nPATTERN_PROPERTY_ROUND_PATH = Path("models/pattern_property_round.pkl")\nPATTERN_REGION_PATH = Path("models/pattern_region.pkl")\nPATTERN_COMPLEX_PATH = Path("models/pattern_complex.pkl")'

    main_content = re.sub(old_model_section, new_model_section, main_content)
    print("[OK] 모델 경로 및 패턴 테이블 경로 추가")

    # 4. load_model 함수 수정 - v4 우선
    # v3 모델 먼저 시도 -> v4 모델 먼저 시도
    old_load_check = r'# v3 모델 먼저 시도\s+if model_v3_path\.exists\(\):'
    new_load_check = '''# v4 모델 먼저 시도
    if model_v4_path.exists():
        try:
            model = joblib.load(model_v4_path)
            model_load_time = datetime.now()
            logger.info(f"AI 모델 v4 로드 성공: {model_v4_path}")
            return True, "v4"
        except Exception as e:
            logger.error(f"AI 모델 v4 로드 실패: {e}")

    # v3 모델 시도
    if model_v3_path.exists():'''

    main_content = re.sub(old_load_check, new_load_check, main_content, flags=re.MULTILINE)
    print("[OK] load_model 함수에 v4 우선 로드 추가")

    # 5. 패턴 테이블 로드 함수 추가
    pattern_load_function = '''
def load_pattern_tables():
    """패턴 테이블을 로드하는 함수"""
    global pattern_property_round, pattern_region, pattern_complex

    try:
        if PATTERN_PROPERTY_ROUND_PATH.exists():
            pattern_property_round = joblib.load(PATTERN_PROPERTY_ROUND_PATH)
            logger.info(f"패턴 테이블 로드 성공: {len(pattern_property_round)}개 (물건×회차)")

        if PATTERN_REGION_PATH.exists():
            pattern_region = joblib.load(PATTERN_REGION_PATH)
            logger.info(f"패턴 테이블 로드 성공: {len(pattern_region)}개 (지역)")

        if PATTERN_COMPLEX_PATH.exists():
            pattern_complex = joblib.load(PATTERN_COMPLEX_PATH)
            logger.info(f"패턴 테이블 로드 성공: {len(pattern_complex)}개 (복합)")

        return True
    except Exception as e:
        logger.error(f"패턴 테이블 로드 실패: {e}")
        return False

'''

    # load_model() 함수 바로 뒤에 패턴 로드 함수 추가
    load_model_end = main_content.find("# 초기 모델 로드\nload_model()")
    if load_model_end != -1:
        main_content = (
            main_content[:load_model_end] +
            pattern_load_function +
            main_content[load_model_end:]
        )
        print("[OK] 패턴 테이블 로드 함수 추가")

    # 6. 초기화 시점에 패턴 테이블도 로드
    old_init = r'# 초기 모델 로드\nload_model\(\)'
    new_init = '# 초기 모델 로드\nload_model()\nload_pattern_tables()'
    main_content = re.sub(old_init, new_init, main_content)
    print("[OK] 초기화 시점에 패턴 테이블 로드 추가")

    # 7. create_features_v3 함수 뒤에 v4 함수 추가
    # create_features_v3 함수의 끝을 찾기
    v3_func_start = main_content.find("def create_features_v3(")
    if v3_func_start == -1:
        print("[ERROR] create_features_v3 함수를 찾을 수 없습니다!")
        return False

    # v3 함수 이후의 다음 함수 시작점 찾기
    next_func = main_content.find("\ndef create_features(", v3_func_start + 1)
    if next_func == -1:
        next_func = main_content.find("\n# ========", v3_func_start + 1)

    if next_func != -1:
        v4_section = f'''

# =============================
# v4 모델 전용 함수 (v3 + 패턴 특성)
# =============================

{create_function}

'''
        main_content = (
            main_content[:next_func] +
            v4_section +
            main_content[next_func:]
        )
        print("[OK] create_features_v4 함수 main.py에 추가")

    # 8. predict_price_advanced 함수 수정하여 v4 지원 추가
    # expected_features == 53이면 v3, == 58이면 v4
    old_feature_check = r'''# 특성 개수에 따라 적절한 함수 선택
            if expected_features > 48:'''

    new_feature_check = '''# 특성 개수에 따라 적절한 함수 선택
            if expected_features == 58:
                # v4 모델: 58개 특성 (v3 + 패턴 특성)
                features = create_features_v4(
                    start_price, property_type, region, area, auction_round, bidders,
                    bidders_actual or bidders, share_floor, share_land, debt_ratio,
                    second_price,
                    pattern_property_round=pattern_property_round,
                    pattern_region=pattern_region,
                    pattern_complex=pattern_complex
                )
                logger.info(f"v4 모델 사용 (58개 특성, 패턴 포함)")
            elif expected_features == 53:
                # v3 모델: 53개 특성
                features = create_features_v3(
                    start_price, property_type, region, area, auction_round, bidders,
                    bidders_actual or bidders, share_floor, share_land, debt_ratio,
                    second_price
                )
                logger.info(f"v3 모델 사용 (53개 특성)")
            elif expected_features > 48:'''

    main_content = re.sub(old_feature_check, new_feature_check, main_content, flags=re.MULTILINE)
    print("[OK] predict_price_advanced에 v4 모델 지원 추가")

    # 9. 저장
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(main_content)

    print("\n" + "=" * 60)
    print("[OK] v4 모델 완전 통합 완료!")
    print("=" * 60)
    print("\n변경 사항:")
    print("  - model_v4_path 추가")
    print("  - 패턴 테이블 경로 추가 (3개)")
    print("  - load_model()에서 v4 우선 로드")
    print("  - load_pattern_tables() 함수 추가")
    print("  - 초기화 시점에 패턴 테이블 로드")
    print("  - create_features_v4() 함수 추가 (58개 특성)")
    print("  - predict_price_advanced()에 v4 지원 추가")
    print("\n다음 단계:")
    print("  1. 서버 재시작")
    print("  2. 브라우저에서 테스트")
    print("  3. 정확도 탭에서 v4 모델 정보 확인")

    return True

if __name__ == "__main__":
    success = integrate_v4()
    if success:
        print("\n[SUCCESS] 패치 적용 성공!")
    else:
        print("\n[FAILED] 패치 적용 실패")
