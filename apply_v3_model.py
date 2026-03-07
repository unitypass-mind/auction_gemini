"""
main.py에 v3 모델 지원을 추가하는 패치 스크립트
"""
import re

def apply_patch():
    print("main.py에 v3 모델 패치 적용 중...")

    with open("main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # 백업 생성
    with open("main.py.backup", "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ 백업 생성: main.py.backup")

    # 1. train_model_v3_simple.py에서 필요한 함수들 가져오기
    with open("train_model_v3_simple.py", "r", encoding="utf-8") as f:
        train_content = f.read()

    # calc_lowest_price_by_round 함수 추출
    calc_func_match = re.search(
        r'def calc_lowest_price_by_round\(.*?\):(.*?)(?=\n\ndef |\nclass |\nif __name__|$)',
        train_content,
        re.DOTALL
    )
    calc_function = calc_func_match.group(0) if calc_func_match else ""

    # create_features_v3 함수 추출
    create_func_match = re.search(
        r'def create_features_v3\(.*?\):(.*?)(?=\n\ndef |\nclass |\nif __name__|$)',
        train_content,
        re.DOTALL
    )
    create_function = create_func_match.group(0) if create_func_match else ""

    # 2. 모델 경로 추가
    content = re.sub(
        r'(# AI 모델 로드 \(v2 모델 우선\)\nmodel = None\n)',
        r'\1model_v3_path = Path("models/auction_model_v3.pkl")\n',
        content
    )

    # 3. load_model 함수 수정 - v3 우선 로드
    load_model_old = r'def load_model\(\):\s*"""AI 모델을 로드하는 함수"""\s*global model, model_load_time\s*# v2 모델 먼저 시도'
    load_model_new = '''def load_model():
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

    content = re.sub(load_model_old, load_model_new, content, flags=re.DOTALL)

    # 4. create_features 함수들 앞에 v3 함수들 추가
    insert_position = content.find("def create_features(")
    if insert_position > 0:
        v3_functions = f"\n\n{calc_function}\n\n{create_function}\n\n"
        content = content[:insert_position] + v3_functions + content[insert_position:]
        print("✅ v3 함수들 추가됨")

    # 5. 저장
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ main.py 패치 완료!")
    print("\n다음 단계:")
    print("1. 서버 재시작")
    print("2. 브라우저에서 2025타경63180 검색하여 테스트")

if __name__ == "__main__":
    apply_patch()
