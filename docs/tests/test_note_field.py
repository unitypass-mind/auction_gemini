# -*- coding: utf-8 -*-
"""
실거래가 안내 메시지 필드 테스트
"""
import sys
import io
sys.stdout.reconfigure(encoding='utf-8')

import requests

test_cases = [
    ("2024타경578276", "남동구 (거래 있음)"),
    ("2025타경299", "포항 (거래 없음)"),
    ("2024타경579705", "송도 (거래 있음)")
]

print("=" * 80)
print("real_transaction_note 필드 확인")
print("=" * 80)

for case_no, description in test_cases:
    print(f"\n[{description}] {case_no}")
    print("-" * 80)

    resp = requests.get("http://localhost:8000/auction", params={"case_no": case_no}, timeout=60)
    data = resp.json()

    if 'data' in data:
        note = data['data'].get('real_transaction_note', '⚠️ 필드 없음')
        count = data['data'].get('transactions_count', 0)

        print(f"실거래 건수: {count}건")
        print(f"안내 메시지: {note}")
    else:
        print("❌ 오류:", data.get('detail', 'Unknown'))

print("\n" + "=" * 80)
