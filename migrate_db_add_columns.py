"""
DB 마이그레이션: predictions 테이블에 최저입찰가 및 권리분석 태그 추가
"""
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "auction_analysis.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. 최저입찰가 컬럼 추가
    try:
        cursor.execute("ALTER TABLE predictions ADD COLUMN 최저입찰가 INTEGER")
        logger.info("✅ 최저입찰가 컬럼 추가 완료")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            logger.info("ℹ️  최저입찰가 컬럼이 이미 존재합니다")
        else:
            raise

    # 2. 최저가율 컬럼 추가 (최저입찰가/감정가 비율)
    try:
        cursor.execute("ALTER TABLE predictions ADD COLUMN 최저가율 REAL")
        logger.info("✅ 최저가율 컬럼 추가 완료")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            logger.info("ℹ️  최저가율 컬럼이 이미 존재합니다")
        else:
            raise

    # 3. 권리분석 태그 컬럼들 추가 (주요 태그들을 원-핫 인코딩)
    권리태그_컬럼 = [
        "tag_대항력있는임차인",
        "tag_선순위전세권",
        "tag_가압류",
        "tag_가처분",
        "tag_가등기",
        "tag_근저당권",
        "tag_지상권",
        "tag_유치권",
        "tag_전세권",
        "tag_기타권리"
    ]

    for 컬럼 in 권리태그_컬럼:
        try:
            cursor.execute(f"ALTER TABLE predictions ADD COLUMN {컬럼} INTEGER DEFAULT 0")
            logger.info(f"✅ {컬럼} 컬럼 추가 완료")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                logger.info(f"ℹ️  {컬럼} 컬럼이 이미 존재합니다")
            else:
                raise

    # 4. raw_data JSON 컬럼 추가 (ValueAuction 원본 데이터)
    try:
        cursor.execute("ALTER TABLE predictions ADD COLUMN raw_data TEXT")
        logger.info("✅ raw_data 컬럼 추가 완료")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            logger.info("ℹ️  raw_data 컬럼이 이미 존재합니다")
        else:
            raise

    conn.commit()
    conn.close()

    logger.info("\n" + "="*60)
    logger.info("✅ DB 마이그레이션 완료!")
    logger.info("="*60)
    logger.info("\n추가된 컬럼:")
    logger.info("  - 최저입찰가 (INTEGER): 실제 최저입찰가")
    logger.info("  - 최저가율 (REAL): 최저입찰가/감정가 비율")
    logger.info("  - tag_* (INTEGER): 권리분석 태그 원-핫 인코딩")
    logger.info("  - raw_data (TEXT): ValueAuction 원본 데이터 JSON")

if __name__ == "__main__":
    migrate()
