"""단일 레코드 업데이트 테스트"""
import sqlite3
from pathlib import Path

DB_PATH = Path("data/predictions.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 하나의 레코드 조회
cursor.execute("SELECT id, case_no, predicted_price FROM predictions WHERE case_no = '2024타경56274'")
row = cursor.fetchone()
print(f"업데이트 전: ID={row[0]}, case_no={row[1]}, predicted_price={row[2]}")

# 업데이트 시도
new_predicted_price = 1234567
cursor.execute("""
    UPDATE predictions
    SET predicted_price = ?
    WHERE case_no = '2024타경56274'
""", (new_predicted_price,))

print(f"업데이트 실행됨: {cursor.rowcount}건")

# 커밋
conn.commit()
print("커밋 완료")

# 확인
cursor.execute("SELECT id, case_no, predicted_price FROM predictions WHERE case_no = '2024타경56274'")
row = cursor.fetchone()
print(f"업데이트 후: ID={row[0]}, case_no={row[1]}, predicted_price={row[2]}")

conn.close()
