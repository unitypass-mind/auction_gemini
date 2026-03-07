"""
성능 모니터링 시스템
모델 성능을 추적하고 시각화합니다.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import sqlite3
import json
import os
from datetime import datetime, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """성능 모니터링 클래스"""

    def __init__(self, db_path="data/predictions.db"):
        self.db_path = db_path
        self.metrics_dir = "logs/metrics"
        os.makedirs(self.metrics_dir, exist_ok=True)

    def get_current_metrics(self):
        """현재 모델 성능 지표 조회"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 전체 통계
            cursor.execute("""
                SELECT
                    COUNT(*) as total_count,
                    AVG(error_rate) as avg_error_rate,
                    AVG(ABS(actual_price - predicted_price)) as avg_error_amount,
                    MIN(error_rate) as min_error_rate,
                    MAX(error_rate) as max_error_rate
                FROM predictions
                WHERE actual_price IS NOT NULL
                AND actual_price > 0
            """)

            row = cursor.fetchone()

            metrics = {
                "timestamp": datetime.now().isoformat(),
                "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "total_predictions": row[0] if row else 0,
                "avg_error_rate": round(row[1], 4) if row[1] else 0,
                "avg_error_amount": int(row[2]) if row[2] else 0,
                "min_error_rate": round(row[3], 4) if row[3] else 0,
                "max_error_rate": round(row[4], 4) if row[4] else 0
            }

            # 구간별 통계
            cursor.execute("""
                SELECT
                    CASE
                        WHEN 감정가 <= 100000000 THEN '1억 이하'
                        WHEN 감정가 <= 300000000 THEN '1억~3억'
                        WHEN 감정가 <= 500000000 THEN '3억~5억'
                        WHEN 감정가 <= 1000000000 THEN '5억~10억'
                        ELSE '10억 초과'
                    END as price_range,
                    COUNT(*) as count,
                    AVG(error_rate) as avg_error_rate
                FROM predictions
                WHERE actual_price IS NOT NULL
                AND actual_price > 0
                GROUP BY price_range
            """)

            price_ranges = {}
            for row in cursor.fetchall():
                price_ranges[row[0]] = {
                    "count": row[1],
                    "avg_error_rate": round(row[2], 4) if row[2] else 0
                }

            metrics["price_ranges"] = price_ranges

            conn.close()

            return metrics

        except Exception as e:
            logger.error(f"메트릭 조회 오류: {e}")
            return None

    def save_metrics_snapshot(self):
        """현재 성능 지표를 스냅샷으로 저장"""
        metrics = self.get_current_metrics()

        if metrics:
            snapshot_file = f"{self.metrics_dir}/snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)

            logger.info(f"성능 스냅샷 저장: {snapshot_file}")

            # 메트릭 히스토리에도 추가
            self._append_to_history(metrics)

            return metrics

        return None

    def _append_to_history(self, metrics):
        """메트릭을 히스토리에 추가"""
        history_file = f"{self.metrics_dir}/metrics_history.json"

        history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                history = []

        history.append(metrics)

        # 최근 200개만 유지
        if len(history) > 200:
            history = history[-200:]

        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def get_metrics_trend(self, days=30):
        """최근 N일간의 성능 추이 조회"""
        history_file = f"{self.metrics_dir}/metrics_history.json"

        if not os.path.exists(history_file):
            logger.warning("메트릭 히스토리 파일이 없습니다.")
            return []

        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)

            # 최근 N일 필터링
            cutoff_date = datetime.now() - timedelta(days=days)

            recent_metrics = [
                m for m in history
                if datetime.fromisoformat(m['timestamp']) >= cutoff_date
            ]

            return recent_metrics

        except Exception as e:
            logger.error(f"추이 조회 오류: {e}")
            return []

    def print_current_status(self):
        """현재 상태를 출력"""
        metrics = self.get_current_metrics()

        if not metrics:
            logger.error("메트릭을 가져올 수 없습니다.")
            return

        logger.info("=" * 80)
        logger.info("📊 현재 모델 성능 지표")
        logger.info("=" * 80)
        logger.info(f"조회 시간: {metrics['date']}")
        logger.info(f"총 예측 건수: {metrics['total_predictions']:,}건")
        logger.info(f"평균 오차율: {metrics['avg_error_rate']:.2f}%")
        logger.info(f"평균 오차 금액: {metrics['avg_error_amount']:,}원")
        logger.info(f"최소 오차율: {metrics['min_error_rate']:.2f}%")
        logger.info(f"최대 오차율: {metrics['max_error_rate']:.2f}%")
        logger.info("")
        logger.info("구간별 성능:")

        for range_name, stats in metrics['price_ranges'].items():
            logger.info(f"  {range_name}: {stats['count']:,}건, 오차율 {stats['avg_error_rate']:.2f}%")

        logger.info("=" * 80)

    def check_performance_degradation(self, threshold=0.05):
        """성능 저하 감지"""
        history = self.get_metrics_trend(days=7)

        if len(history) < 2:
            logger.info("비교할 이력이 충분하지 않습니다.")
            return False

        # 최근 성능과 일주일 전 성능 비교
        current = history[-1]
        previous = history[0]

        error_rate_change = current['avg_error_rate'] - previous['avg_error_rate']

        if error_rate_change > threshold:
            logger.warning("=" * 80)
            logger.warning("⚠️ 성능 저하 감지!")
            logger.warning("=" * 80)
            logger.warning(f"일주일 전 오차율: {previous['avg_error_rate']:.2f}%")
            logger.warning(f"현재 오차율: {current['avg_error_rate']:.2f}%")
            logger.warning(f"변화량: +{error_rate_change:.2f}%p")
            logger.warning("재학습을 권장합니다.")
            logger.warning("=" * 80)
            return True

        logger.info(f"성능 안정적 (변화량: {error_rate_change:+.2f}%p)")
        return False

def main():
    """메인 함수"""
    monitor = PerformanceMonitor()

    # 현재 상태 출력
    monitor.print_current_status()

    # 스냅샷 저장
    monitor.save_metrics_snapshot()

    # 성능 저하 체크
    monitor.check_performance_degradation()

if __name__ == "__main__":
    main()
