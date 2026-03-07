# -*- coding: utf-8 -*-
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/predictions.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 검증된 예측 중 최신 5건 조회
cursor.execute('''
    SELECT * FROM predictions
    WHERE actual_price IS NOT NULL
    ORDER BY created_at DESC
    LIMIT 5
''')

rows = cursor.fetchall()

print("검증된 예측 데이터 샘플 (최신 5건):")
print("=" * 80)
for row in rows:
    data = dict(row)
    print(f"\ncase_no: {data.get('case_no')}")
    print(f"사건번호: {data.get('사건번호')}")
    print(f"물건번호: {data.get('물건번호')}")
    print(f"감정가: {data.get('감정가'):,}원" if data.get('감정가') else "감정가: N/A")
    print(f"물건종류: {data.get('물건종류')}")
    print(f"지역: {data.get('지역')}")
    print(f"면적: {data.get('면적')}")
    print("-" * 80)

conn.close()
