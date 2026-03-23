"""
main.py의 데이터베이스 연결을 app DB와 predictions DB로 분리하는 마이그레이션 스크립트
"""
import re

# App DB 테이블 목록 (이 테이블들을 사용하는 쿼리는 'app'으로 변경)
APP_TABLES = {
    'users', 'fcm_tokens', 'refresh_tokens',
    'auction_subscriptions', 'notification_logs'
}

def migrate_db_connections(file_path='main.py'):
    """main.py의 db._get_connection() 호출을 분석하고 적절한 DB 타입 추가"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 각 db._get_connection() 호출과 그 이후 300자를 추출
    pattern = r'(conn = db\._get_connection\(\))([^#]{1,500})'

    def replace_connection(match):
        connection_line = match.group(1)
        following_code = match.group(2)

        # 다음 코드에서 사용되는 테이블 찾기
        tables_used = set()
        for table in APP_TABLES:
            if f'FROM {table}' in following_code or f'INTO {table}' in following_code or \
               f'UPDATE {table}' in following_code or f'DELETE FROM {table}' in following_code or \
               f'JOIN {table}' in following_code:
                tables_used.add(table)

        # App 테이블을 사용하면 'app' 파라미터 추가
        if tables_used:
            return f"conn = db._get_connection('app'){match.group(2)}"
        else:
            # Predictions 테이블이거나 알 수 없는 경우 그대로 유지
            return match.group(0)

    # 변경 적용
    new_content = re.sub(pattern, replace_connection, content, flags=re.IGNORECASE)

    # 백업 파일 저장
    backup_path = file_path + '.backup_migration'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[OK] 백업 파일 생성: {backup_path}")

    # 새 파일 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"[OK] 변경 완료: {file_path}")

    # 변경 사항 통계
    original_count = content.count("db._get_connection()")
    app_count = new_content.count("db._get_connection('app')")
    predictions_count = new_content.count("db._get_connection('predictions')")
    unchanged_count = new_content.count("db._get_connection())") - predictions_count

    print(f"\n=== 변경 통계 ===")
    print(f"원본 db._get_connection() 호출: {original_count}개")
    print(f"→ app DB로 변경: {app_count}개")
    print(f"→ predictions DB 명시: {predictions_count}개")
    print(f"→ 기본값 유지: {unchanged_count}개")

if __name__ == "__main__":
    migrate_db_connections()
