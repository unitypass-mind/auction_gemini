# -*- coding: utf-8 -*-
"""
_court_site_search_async 함수를 스레드 없이 직접 asyncio.run()으로 테스트
"""
import asyncio
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# main.py 로드
import importlib.util
spec = importlib.util.spec_from_file_location("main_mod", "main.py")
main_mod = importlib.util.module_from_spec(spec)
import sys as _sys
_sys.modules['main_mod'] = main_mod
spec.loader.exec_module(main_mod)

async def main():
    print("=" * 60)
    print("직접 asyncio.run 테스트: 2024타경579705")
    print("=" * 60)

    # 스레드 래퍼 없이 직접 호출
    result = await main_mod._court_site_search_async("2024타경579705")

    if result:
        print("\n[성공!] 검색 결과:")
        for k, v in result.items():
            if k != '원본데이터':
                print(f"  {k}: {v}")
    else:
        print("\n[실패] 결과 없음")

asyncio.run(main())
