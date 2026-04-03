"""
예측 결과 추적 데이터베이스 모듈
예측치와 실제 낙찰가를 저장하고 정확도를 분석합니다.
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Literal
import logging
import numpy as np

logger = logging.getLogger(__name__)

# 데이터베이스 경로
DB_PATH = Path("data/predictions.db")
APP_DB_PATH = Path("data/app.db")


class PredictionDB:
    """예측 결과 추적 데이터베이스 (predictions + app 분리)"""

    def __init__(self, db_path: str = None, app_db_path: str = None):
        self.predictions_db_path = db_path or DB_PATH
        self.app_db_path = app_db_path or APP_DB_PATH
        self._ensure_db_directory()
        self._init_db()

    def _ensure_db_directory(self):
        """데이터베이스 디렉토리 생성"""
        self.predictions_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.app_db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self, db_type: Literal['predictions', 'app'] = 'predictions'):
        """
        데이터베이스 연결

        Args:
            db_type: 'predictions' (예측 데이터) 또는 'app' (사용자/앱 데이터)

        Returns:
            sqlite3.Connection
        """
        if db_type == 'app':
            return sqlite3.connect(self.app_db_path)
        else:
            return sqlite3.connect(self.predictions_db_path)

    # 하위 호환성을 위한 속성
    @property
    def db_path(self):
        """기존 코드 호환성을 위한 속성 (predictions DB 경로 반환)"""
        return self.predictions_db_path

    def _init_db(self):
        """데이터베이스 초기화 및 테이블 생성"""
        self._init_predictions_db()
        self._init_app_db()

    def _init_predictions_db(self):
        """예측 데이터베이스 초기화"""
        conn = self._get_connection('predictions')
        cursor = conn.cursor()

        # 예측 결과 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_no TEXT NOT NULL,
                물건번호 TEXT,
                사건번호 TEXT,

                -- 입력 정보
                감정가 INTEGER NOT NULL,
                물건종류 TEXT,
                지역 TEXT,
                소재지 TEXT,
                면적 REAL,
                경매회차 INTEGER,
                입찰자수 INTEGER,

                -- 예측 정보
                predicted_price INTEGER NOT NULL,
                expected_profit INTEGER,
                profit_rate REAL,
                prediction_mode TEXT,
                model_used BOOLEAN,

                -- 실제 결과 (나중에 업데이트)
                actual_price INTEGER,
                actual_date DATE,

                -- 정확도 지표
                error_amount INTEGER,
                error_rate REAL,

                -- 메타 정보
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified BOOLEAN DEFAULT 0,
                source TEXT DEFAULT 'web',

                -- 인덱스
                UNIQUE(case_no, created_at)
            )
        """)

        # 인덱스 생성
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_case_no
            ON predictions(case_no)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verified
            ON predictions(verified)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at
            ON predictions(created_at DESC)
        """)

        # 추가 성능 최적화 인덱스
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_actual_price
            ON predictions(actual_price)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verified_created_at
            ON predictions(verified, created_at DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_case_no_verified
            ON predictions(case_no, verified, id DESC)
        """)

        # 통계 요약 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accuracy_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period TEXT NOT NULL,
                total_predictions INTEGER,
                verified_predictions INTEGER,
                avg_error_rate REAL,
                avg_error_amount INTEGER,
                median_error_rate REAL,
                best_accuracy REAL,
                worst_accuracy REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(period)
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"Predictions 데이터베이스 초기화 완료: {self.predictions_db_path}")

    def _init_app_db(self):
        """앱/사용자 데이터베이스 초기화"""
        conn = self._get_connection('app')
        cursor = conn.cursor()

        # 사용자 테이블 (JWT 인증용)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                name TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_admin BOOLEAN DEFAULT 0,
                notification_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)

        # 사용자 테이블 인덱스
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email
            ON users(email)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_is_active
            ON users(is_active)
        """)

        # Refresh Token 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS refresh_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_revoked BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # Refresh Token 인덱스
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id
            ON refresh_tokens(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash
            ON refresh_tokens(token_hash)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at
            ON refresh_tokens(expires_at)
        """)

        # FCM 토큰 테이블 (푸시 알림용)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fcm_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                device_id TEXT NOT NULL,
                fcm_token TEXT NOT NULL,
                device_type TEXT DEFAULT 'android',
                device_model TEXT,
                os_version TEXT,
                app_version TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE(device_id, user_id)
            )
        """)

        # FCM 토큰 인덱스
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fcm_tokens_user_id
            ON fcm_tokens(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fcm_tokens_device_id
            ON fcm_tokens(device_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fcm_tokens_is_active
            ON fcm_tokens(is_active)
        """)

        # 알림 로그 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                notification_type TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                data TEXT,
                fcm_token TEXT,
                success BOOLEAN DEFAULT 0,
                error_message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
            )
        """)

        # 알림 로그 인덱스
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notification_logs_user_id
            ON notification_logs(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notification_logs_type
            ON notification_logs(notification_type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notification_logs_sent_at
            ON notification_logs(sent_at)
        """)

        # 경매 알림 구독 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auction_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                case_number TEXT,
                address_keyword TEXT,
                min_price INTEGER,
                max_price INTEGER,
                price_drop_alert BOOLEAN DEFAULT 1,
                bid_reminder_alert BOOLEAN DEFAULT 1,
                notification_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)

        # 경매 구독 인덱스
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_auction_subs_user_id
            ON auction_subscriptions(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_auction_subs_case_number
            ON auction_subscriptions(case_number)
        """)

        conn.commit()
        conn.close()
        logger.info(f"App 데이터베이스 초기화 완료: {self.app_db_path}")

    def save_prediction(self, data: Dict[str, Any]) -> int:
        """
        예측 결과 저장 (같은 사건번호가 있으면 업데이트)

        Args:
            data: 예측 정보 딕셔너리

        Returns:
            저장된 레코드 ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            case_no = data.get('case_no') or data.get('사건번호')

            # 같은 사건번호가 이미 있는지 확인
            cursor.execute("""
                SELECT id FROM predictions
                WHERE case_no = ? OR 사건번호 = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (case_no, case_no))

            existing = cursor.fetchone()

            if existing:
                # 기존 레코드 업데이트
                cursor.execute("""
                    UPDATE predictions SET
                        물건번호 = ?, 사건번호 = ?,
                        감정가 = ?, 물건종류 = ?, 지역 = ?, 소재지 = ?, 면적 = ?, 경매회차 = ?, 입찰자수 = ?,
                        predicted_price = ?, expected_profit = ?, profit_rate = ?,
                        prediction_mode = ?, model_used = ?, source = ?,
                        입찰자수_실제 = ?, second_price = ?, 권리분석복잡도 = ?, 권리사항태그수 = ?,
                        공유지분_건물 = ?, 공유지분_토지 = ?, 청구금액 = ?, 청구금액비율 = ?,
                        created_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    data.get('물건번호'),
                    data.get('사건번호'),
                    data.get('감정가'),
                    data.get('물건종류'),
                    data.get('지역'),
                    data.get('소재지'),
                    data.get('면적'),
                    data.get('경매회차', 1),
                    data.get('입찰자수', 10),
                    data.get('predicted_price'),
                    data.get('expected_profit'),
                    data.get('profit_rate'),
                    data.get('prediction_mode'),
                    data.get('model_used', True),
                    data.get('source', 'web'),
                    data.get('입찰자수_실제'),
                    data.get('second_price'),
                    data.get('권리분석복잡도', 0),
                    data.get('권리사항태그수', 0),
                    data.get('공유지분_건물', 0),
                    data.get('공유지분_토지', 0),
                    data.get('청구금액', 0),
                    data.get('청구금액비율', 0),
                    existing['id']
                ))
                record_id = existing['id']
                logger.info(f"기존 예측 업데이트: {case_no} (ID: {record_id})")
            else:
                # 새 레코드 삽입
                cursor.execute("""
                    INSERT INTO predictions (
                        case_no, 물건번호, 사건번호,
                        감정가, 물건종류, 지역, 소재지, 면적, 경매회차, 입찰자수,
                        predicted_price, expected_profit, profit_rate,
                        prediction_mode, model_used, source,
                        입찰자수_실제, second_price, 권리분석복잡도, 권리사항태그수,
                        공유지분_건물, 공유지분_토지, 청구금액, 청구금액비율
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.get('case_no'),
                    data.get('물건번호'),
                    data.get('사건번호'),
                    data.get('감정가'),
                    data.get('물건종류'),
                    data.get('지역'),
                    data.get('소재지'),
                    data.get('면적'),
                    data.get('경매회차', 1),
                    data.get('입찰자수', 10),
                    data.get('predicted_price'),
                    data.get('expected_profit'),
                    data.get('profit_rate'),
                    data.get('prediction_mode'),
                    data.get('model_used', True),
                    data.get('source', 'web'),
                    data.get('입찰자수_실제'),
                    data.get('second_price'),
                    data.get('권리분석복잡도', 0),
                    data.get('권리사항태그수', 0),
                    data.get('공유지분_건물', 0),
                    data.get('공유지분_토지', 0),
                    data.get('청구금액', 0),
                    data.get('청구금액비율', 0),
                ))
                record_id = cursor.lastrowid
                logger.info(f"새 예측 저장: {case_no} (ID: {record_id})")

            conn.commit()
            return record_id

        except sqlite3.IntegrityError as e:
            logger.warning(f"중복 예측: {data.get('case_no')} - {e}")
            return -1
        except Exception as e:
            logger.error(f"예측 저장 실패: {e}", exc_info=True)
            conn.rollback()
            return -1
        finally:
            conn.close()

    def update_actual_result(
        self,
        case_no: str,
        actual_price: int,
        actual_date: str = None
    ) -> bool:
        """
        실제 낙찰가 업데이트

        Args:
            case_no: 사건번호
            actual_price: 실제 낙찰가
            actual_date: 낙찰 날짜

        Returns:
            업데이트 성공 여부
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 가장 최근 예측 가져오기
            cursor.execute("""
                SELECT id, predicted_price
                FROM predictions
                WHERE case_no = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (case_no,))

            result = cursor.fetchone()
            if not result:
                logger.warning(f"예측 기록을 찾을 수 없음: {case_no}")
                return False

            record_id, predicted_price = result

            # 오차 계산
            error_amount = abs(actual_price - predicted_price)
            error_rate = (error_amount / actual_price * 100) if actual_price > 0 else 0

            # 업데이트
            cursor.execute("""
                UPDATE predictions
                SET actual_price = ?,
                    actual_date = ?,
                    error_amount = ?,
                    error_rate = ?,
                    verified = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                actual_price,
                actual_date or datetime.now().strftime('%Y-%m-%d'),
                error_amount,
                error_rate,
                record_id
            ))

            conn.commit()
            logger.info(f"실제 낙찰가 업데이트: {case_no}, 오차율={error_rate:.2f}%")
            return True

        except Exception as e:
            logger.error(f"실제 낙찰가 업데이트 실패: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_accuracy_stats(self, days: int = 365) -> Dict[str, Any]:
        """
        정확도 통계 조회

        Args:
            days: 최근 며칠 데이터 (기본: 365일 = 전체 데이터)

        Returns:
            통계 딕셔너리
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN verified = 1 THEN 1 END) as verified,
                    AVG(CASE WHEN verified = 1 THEN error_rate END) as avg_error_rate,
                    AVG(CASE WHEN verified = 1 THEN error_amount END) as avg_error_amount,
                    MIN(CASE WHEN verified = 1 THEN error_rate END) as best_accuracy,
                    MAX(CASE WHEN verified = 1 THEN error_rate END) as worst_accuracy
                FROM predictions
                WHERE created_at >= datetime('now', '-' || ? || ' days')
            """, (days,))

            row = cursor.fetchone()

            # 중위값 계산을 위해 오차금액 데이터 가져오기
            cursor.execute("""
                SELECT error_amount
                FROM predictions
                WHERE verified = 1 AND error_amount IS NOT NULL
                  AND created_at >= datetime('now', '-' || ? || ' days')
                ORDER BY error_amount
            """, (days,))

            error_amounts = [r[0] for r in cursor.fetchall()]
            median_error_amount = 0
            if error_amounts:
                median_error_amount = int(np.median(error_amounts))

            # 감정가 구간별 중위 오차 계산
            price_ranges = [
                {'label': '1억 이하', 'min': 0, 'max': 100000000},
                {'label': '1억~3억', 'min': 100000000, 'max': 300000000},
                {'label': '3억~5억', 'min': 300000000, 'max': 500000000},
                {'label': '5억~10억', 'min': 500000000, 'max': 1000000000},
                {'label': '10억 초과', 'min': 1000000000, 'max': 999999999999}
            ]

            error_by_range = []
            for price_range in price_ranges:
                cursor.execute("""
                    SELECT error_amount
                    FROM predictions
                    WHERE verified = 1
                      AND error_amount IS NOT NULL
                      AND 감정가 >= ?
                      AND 감정가 < ?
                      AND created_at >= datetime('now', '-' || ? || ' days')
                    ORDER BY error_amount
                """, (price_range['min'], price_range['max'], days))

                range_errors = [r[0] for r in cursor.fetchall()]
                median_error = int(np.median(range_errors)) if range_errors else 0
                count = len(range_errors)

                error_by_range.append({
                    'range': price_range['label'],
                    'median_error': median_error,
                    'count': count
                })

            stats = {
                'total_predictions': row[0] or 0,
                'verified_predictions': row[1] or 0,
                'avg_error_rate': round(row[2] or 0, 2),
                'avg_error_amount': int(row[3] or 0),
                'median_error_amount': median_error_amount,  # 중위값 추가
                'best_accuracy': round(row[4] or 0, 2) if row[4] else None,
                'worst_accuracy': round(row[5] or 0, 2) if row[5] else None,
                'verification_rate': round((row[1] or 0) / (row[0] or 1) * 100, 2),
                'error_by_price_range': error_by_range  # 구간별 오차 추가
            }

            return stats

        except Exception as e:
            logger.error(f"통계 조회 실패: {e}", exc_info=True)
            return {}
        finally:
            conn.close()

    def get_recent_predictions(self, limit: int = 100, verified_only: bool = False) -> List[Dict[str, Any]]:
        """
        최근 예측 목록 조회

        Args:
            limit: 최대 개수
            verified_only: 검증된 것만

        Returns:
            예측 목록
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            query = """
                SELECT * FROM predictions
                WHERE 1=1
            """

            if verified_only:
                query += " AND verified = 1"

            query += " ORDER BY created_at DESC LIMIT ?"

            cursor.execute(query, (limit,))
            rows = cursor.fetchall()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"예측 목록 조회 실패: {e}", exc_info=True)
            return []
        finally:
            conn.close()

    def get_unverified_predictions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        미검증 예측 목록 조회 (실제 낙찰가 업데이트 필요)
        - 예측은 했지만 실제 낙찰가가 입력되지 않은 데이터
        - case_no 기준으로 중복 제거 (같은 물건의 최신 예측만 표시)

        Args:
            limit: 최대 개수

        Returns:
            미검증 예측 목록
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT p1.* FROM predictions p1
                INNER JOIN (
                    SELECT case_no, MAX(id) as max_id
                    FROM predictions
                    WHERE verified = 1 AND (actual_price = 0 OR actual_price IS NULL)
                    GROUP BY case_no
                ) p2 ON p1.id = p2.max_id
                ORDER BY p1.created_at DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"미검증 예측 조회 실패: {e}", exc_info=True)
            return []
        finally:
            conn.close()

    def get_prediction_by_case_no(self, case_no: str) -> Optional[Dict[str, Any]]:
        """
        사건번호로 과거 예측값 조회 (가장 최신 예측)

        Args:
            case_no: 사건번호

        Returns:
            예측 정보 딕셔너리 또는 None
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM predictions
                WHERE case_no = ? OR 사건번호 = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (case_no, case_no))

            row = cursor.fetchone()
            return dict(row) if row else None

        except Exception as e:
            logger.error(f"사건번호로 예측 조회 실패: {e}", exc_info=True)
            return None
        finally:
            conn.close()

    def get_similar_cases_count(self, property_type: str = None, region: str = None) -> Dict[str, int]:
        """
        유사 사례 개수 조회 (실제 DB 기반)

        Args:
            property_type: 물건종류 (예: '아파트')
            region: 지역 (예: '서울')

        Returns:
            {'similar_cases': 유사사례수, 'regional_data': 지역데이터수}
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 유사 사례 개수 (물건종류 + 지역 모두 일치)
            similar_query = "SELECT COUNT(*) FROM predictions WHERE actual_price > 0"
            params = []

            if property_type:
                similar_query += " AND 물건종류 LIKE ?"
                params.append(f"%{property_type}%")

            if region:
                similar_query += " AND 지역 LIKE ?"
                params.append(f"%{region}%")

            cursor.execute(similar_query, params)
            similar_count = cursor.fetchone()[0]

            # 지역 데이터 개수 (지역만 일치)
            regional_count = 0
            if region:
                cursor.execute("""
                    SELECT COUNT(*) FROM predictions
                    WHERE actual_price > 0 AND 지역 LIKE ?
                """, (f"%{region}%",))
                regional_count = cursor.fetchone()[0]
            else:
                # 지역 정보 없으면 전체 데이터
                cursor.execute("SELECT COUNT(*) FROM predictions WHERE actual_price > 0")
                regional_count = cursor.fetchone()[0]

            return {
                'similar_cases': similar_count,
                'regional_data': regional_count
            }

        except Exception as e:
            logger.error(f"유사 사례 개수 조회 실패: {e}", exc_info=True)
            return {'similar_cases': 0, 'regional_data': 0}
        finally:
            conn.close()

    def get_competition_stats(self, property_type: str = None, region: str = None) -> Dict[str, Any]:
        """
        경쟁 분석 통계 조회 (실제 DB 기반)

        Args:
            property_type: 물건종류
            region: 지역

        Returns:
            {'avg_bidders': 평균입찰자수, 'avg_success_rate': 평균낙찰률}
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = """
                SELECT
                    AVG(CAST(입찰자수 AS REAL)) as avg_bidders,
                    AVG(CAST(actual_price AS REAL) / NULLIF(CAST(감정가 AS REAL), 0) * 100) as avg_success_rate
                FROM predictions
                WHERE actual_price > 0
            """
            params = []

            if property_type:
                query += " AND 물건종류 LIKE ?"
                params.append(f"%{property_type}%")

            if region:
                query += " AND 지역 LIKE ?"
                params.append(f"%{region}%")

            cursor.execute(query, params)
            row = cursor.fetchone()

            avg_bidders = int(row[0]) if row[0] else 5
            avg_success_rate = round(row[1], 1) if row[1] else 65.5

            return {
                'avg_bidders': avg_bidders,
                'avg_success_rate': avg_success_rate
            }

        except Exception as e:
            logger.error(f"경쟁 분석 통계 조회 실패: {e}", exc_info=True)
            return {'avg_bidders': 5, 'avg_success_rate': 65.5}
        finally:
            conn.close()

    def get_similar_properties(self, property_type: str, region: str, area: float, limit: int = 6) -> List[Dict[str, Any]]:
        """
        유사 물건 목록 조회 (실제 DB 기반)

        Args:
            property_type: 물건종류
            region: 지역
            area: 면적
            limit: 최대 개수

        Returns:
            유사 물건 목록
        """
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # 면적 유사도 범위: ±20%
            area_min = area * 0.8 if area else 0
            area_max = area * 1.2 if area else 999999

            query = """
                SELECT
                    case_no, 지역, 물건종류, 면적, actual_price, created_at,
                    ABS(면적 - ?) as area_diff
                FROM predictions
                WHERE actual_price > 0
                AND 면적 BETWEEN ? AND ?
            """
            params = [area, area_min, area_max]

            if property_type:
                query += " AND 물건종류 LIKE ?"
                params.append(f"%{property_type}%")

            if region:
                query += " AND 지역 LIKE ?"
                params.append(f"%{region}%")

            query += " GROUP BY case_no ORDER BY area_diff ASC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                # 유사도 점수 계산 (면적 차이 기반)
                area_similarity = max(0, 100 - (row['area_diff'] / area * 100)) if area > 0 else 85

                results.append({
                    'address': f"{row['지역']} 인근 {row['물건종류']}",
                    'property_type': row['물건종류'],
                    'area': float(row['면적']) if row['면적'] else 85.0,
                    'winning_bid': int(row['actual_price']),
                    'auction_date': row['created_at'][:10] if row['created_at'] else '2024-01-01',
                    'similarity_score': int(area_similarity),
                    'court': '지방법원'
                })

            return results

        except Exception as e:
            logger.error(f"유사 물건 조회 실패: {e}", exc_info=True)
            return []
        finally:
            conn.close()


# 전역 인스턴스
db = PredictionDB()


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    # 샘플 예측 저장
    test_data = {
        'case_no': '202400001',
        '물건번호': 'TEST-001',
        '사건번호': '2024타경00001',
        '감정가': 300000000,
        '물건종류': '아파트',
        '지역': '서울',
        '면적': 85.0,
        '경매회차': 1,
        '입찰자수': 10,
        'predicted_price': 240000000,
        'expected_profit': 60000000,
        'profit_rate': 20.0,
        'prediction_mode': 'AI',
        'model_used': True
    }

    record_id = db.save_prediction(test_data)
    print(f"저장 완료: ID={record_id}")

    # 실제 낙찰가 업데이트
    db.update_actual_result('202400001', 245000000)

    # 통계 조회
    stats = db.get_accuracy_stats()
    print("\n정확도 통계:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # 최근 예측 조회
    recent = db.get_recent_predictions(limit=5)
    print(f"\n최근 예측 {len(recent)}건")
