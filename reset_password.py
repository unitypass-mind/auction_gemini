#!/usr/bin/env python3
"""
비밀번호 재설정 스크립트
"""
import bcrypt
import sqlite3

# 비밀번호 해시 생성
password = "1234"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

print(f"새 비밀번호 해시: {hashed.decode('utf-8')}")

# 데이터베이스 업데이트
conn = sqlite3.connect('data/app.db')
cursor = conn.cursor()

cursor.execute("""
    UPDATE users
    SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
    WHERE email = ?
""", (hashed.decode('utf-8'), 'fcmtest@exam.com'))

conn.commit()
affected = cursor.rowcount
conn.close()

print(f"✅ 업데이트 완료: {affected}개 행이 변경되었습니다")
