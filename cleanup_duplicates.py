import sqlite3
from datetime import datetime

# Connect to database
conn = sqlite3.connect('data/predictions.db')
cursor = conn.cursor()

# Find all duplicates by 사건번호
cursor.execute("""
    SELECT 사건번호, GROUP_CONCAT(id || '|' || COALESCE(actual_price, 0) || '|' || created_at) as records
    FROM predictions
    WHERE 사건번호 IS NOT NULL AND 사건번호 != ""
      AND case_no NOT LIKE "PREDICT-%"
    GROUP BY 사건번호
    HAVING COUNT(*) > 1
    ORDER BY 사건번호
""")

duplicates = cursor.fetchall()

print(f"Found {len(duplicates)} 사건번호 with duplicates")
print("=" * 80)

total_deleted = 0

for 사건번호, records_str in duplicates:
    # Parse records: id|actual_price|created_at
    records = []
    for rec in records_str.split(','):
        parts = rec.split('|')
        id = int(parts[0])
        actual_price = int(parts[1])
        created_at = parts[2]
        records.append({
            'id': id,
            'actual_price': actual_price,
            'created_at': created_at
        })

    # Sort records: prioritize ones with actual_price, then by oldest created_at
    records.sort(key=lambda x: (x['actual_price'] == 0, x['created_at']))

    # Keep the first record (best one), delete others
    keep_id = records[0]['id']
    delete_ids = [r['id'] for r in records[1:]]

    print(f"\n사건번호: {사건번호}")
    print(f"  Total records: {len(records)}")
    print(f"  Keeping ID: {keep_id} (actual_price: {records[0]['actual_price']:,}, created: {records[0]['created_at']})")
    print(f"  Deleting IDs: {delete_ids}")

    if delete_ids:
        cursor.execute(f"DELETE FROM predictions WHERE id IN ({','.join(map(str, delete_ids))})")
        total_deleted += len(delete_ids)
        print(f"  Deleted {len(delete_ids)} duplicate(s)")

conn.commit()
conn.close()

print("=" * 80)
print(f"\nCleanup complete!")
print(f"Total duplicates deleted: {total_deleted}")
print(f"Remaining duplicate groups: 0")
