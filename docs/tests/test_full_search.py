# -*- coding: utf-8 -*-
"""
main.py의 get_auction_from_court_site 함수 직접 테스트
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# main.py 모듈에서 함수 임포트 (FastAPI 앱 실행 없이)
import importlib.util
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 필요한 함수만 import
spec = importlib.util.spec_from_file_location("main_mod", "main.py")
main_mod = importlib.util.module_from_spec(spec)

# 서버 시작 코드 실행 방지 - sys.modules에 직접 로드
import sys
sys.modules['main_mod'] = main_mod
spec.loader.exec_module(main_mod)

get_court = main_mod.get_auction_from_court_site
parse = main_mod._parse_court_data

print("=" * 60)
print("법원 경매 검색 테스트: 2024타경579705")
print("=" * 60)

result = get_court("2024타경579705")

if result:
    print("\n[성공!] 검색 결과:")
    for k, v in result.items():
        if k != '원본데이터':
            print(f"  {k}: {v}")
else:
    print("\n[실패] 결과 없음")
