# main.py에 feature names 추가하는 스크립트

# 파일 읽기
with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# get_model_features 함수 찾기
for i, line in enumerate(lines):
    if '@app.get("/model/features")' in line:
        # try 블록 찾기
        for j in range(i, min(i+20, len(lines))):
            if '    try:' in lines[j]:
                # try 바로 다음에 feature names 정의 추가
                insert_pos = j + 1

                feature_names_code = '''        # v4 모델의 58개 특성 이름 정의
        FEATURE_NAMES_V4 = [
            # 1. 기본 가격 특성 (5개)
            '감정가', 'log(감정가)', '최저입찰가', 'log(최저입찰가)', '최저가율',
            # 2. 물건종류 (7개)
            '아파트', '다세대', '단독주택', '오피스텔', '토지', '상가', '기타물건',
            # 3. 지역 (10개)
            '서울', '경기', '인천', '부산', '대구', '대전', '광주', '울산', '세종', '기타지역',
            # 4. 면적 관련 (4개)
            '면적', 'log(면적)', '평당가', 'log(평당가)',
            # 5. 경매 진행 상황 (5개)
            '경매회차', 'log(경매회차)', '입찰자수(예상)', '입찰자수(실제)', 'log(입찰자수)',
            # 6. 공유지분 & 부채 (4개)
            '공유지분_건물', '공유지분_토지', '청구금액비율', 'log(청구금액비율)',
            # 7. 2순위 가격 (3개)
            '2순위가격', 'log(2순위가격)', '2순위가격비율',
            # 8. 최저입찰가 상호작용 (4개)
            '최저가율×회차', '최저가율×입찰자수', '최저가×입찰자수', 'log(최저가율×회차)',
            # 9. 고급 상호작용 (7개)
            '감정가×회차', '감정가×입찰자수', '면적×회차', '평당가×회차', '회차당입찰자수', '총공유지분', '청구금액비율×회차',
            # 10. 다항 특성 (4개)
            '감정가^2', '면적^2', '회차^2', '입찰자수^2',
            # 11. 과거 패턴 특성 (5개)
            '패턴_물건회차', '패턴_지역', '패턴_복합', '패턴_상호작용', '패턴_차이'
        ]

'''

                # 해당 위치에 코드 삽입
                lines.insert(insert_pos, feature_names_code)

                # feature_names 설정 부분 수정
                for k in range(insert_pos, min(insert_pos+50, len(lines))):
                    if 'feature_names = model.get' in lines[k]:
                        lines[k] = lines[k].replace(
                            "model.get('feature_names', [])",
                            "model.get('feature_names', FEATURE_NAMES_V4)"
                        )
                    elif 'feature_names = getattr(model' in lines[k]:
                        lines[k] = lines[k].replace(
                            "getattr(model, 'feature_names_in_', [])",
                            "getattr(model, 'feature_names_in_', FEATURE_NAMES_V4)"
                        )

                break
        break

# 파일 쓰기
with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Feature names added successfully')
