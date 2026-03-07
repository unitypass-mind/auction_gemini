# -*- coding: utf-8 -*-
"""
기존 데이터베이스의 물건번호와 사건번호를 case_no로 업데이트
"""
import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/predictions.db')
cursor = conn.cursor()

# 물건번호가 NULL인 레코드 업데이트
cursor.execute('''
    UPDATE predictions
    SET 물건번호 = case_no
    WHERE 물건번호 IS NULL
''')

updated_item_no = cursor.rowcount
print(f"물건번호 업데이트: {updated_item_no}건")

# 사건번호가 NULL인 레코드 업데이트
cursor.execute('''
    UPDATE predictions
    SET 사건번호 = case_no
    WHERE 사건번호 IS NULL
''')

updated_case_no = cursor.rowcount
print(f"사건번호 업데이트: {updated_case_no}건")

conn.commit()
conn.close()

print("\n업데이트 완료!")
print(f"총 {max(updated_item_no, updated_case_no)}건의 레코드가 수정되었습니다.")
