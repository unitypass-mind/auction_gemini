"""
설정 파일
환경변수 및 애플리케이션 설정 관리
"""
from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    # ================================
    # 애플리케이션 설정
    # ================================
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "change-this-in-production"
    APP_TITLE: str = "AI 기반 경매 낙찰가 예측 시스템"
    APP_VERSION: str = "1.0.0"

    # ================================
    # 서버 설정
    # ================================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_HOSTS: str = "*"
    CORS_ORIGINS: str = "*"

    # ================================
    # 외부 API 키
    # ================================
    ODCLOUD_API_KEY: Optional[str] = None

    # ================================
    # 데이터베이스
    # ================================
    DATABASE_URL: str = "sqlite:///./data/predictions.db"

    # ================================
    # 모델 설정
    # ================================
    MODEL_PATH: str = "models/auction_model_v4.pkl"
    PATTERN_PROPERTY_ROUND_PATH: str = "models/pattern_property_round.pkl"
    PATTERN_REGION_PATH: str = "models/pattern_region.pkl"
    PATTERN_COMPLEX_PATH: str = "models/pattern_complex.pkl"

    # ================================
    # 크롤링 설정
    # ================================
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    REQUEST_TIMEOUT: int = 30
    COURT_AUCTION_BASE_URL: str = "https://www.courtauction.go.kr"
    REALTRADE_API_URL: str = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"

    # ================================
    # 보안 설정
    # ================================
    RATE_LIMIT_PER_MINUTE: int = 60
    MAX_UPLOAD_SIZE_MB: int = 10

    # ================================
    # 캐싱 설정
    # ================================
    REDIS_URL: Optional[str] = None
    CACHE_EXPIRE_SECONDS: int = 3600

    # ================================
    # 로깅 설정
    # ================================
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # ================================
    # 모니터링 (선택)
    # ================================
    SENTRY_DSN: Optional[str] = None
    GA_MEASUREMENT_ID: Optional[str] = None

    # ================================
    # 예측 기본값
    # ================================
    DEFAULT_BIDDERS: int = 10
    DEFAULT_PROFIT_MARGIN: float = 0.75  # 감정가의 75%

    @property
    def allowed_hosts_list(self) -> List[str]:
        """ALLOWED_HOSTS를 리스트로 반환"""
        if self.ALLOWED_HOSTS == "*":
            return ["*"]
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",")]

    @property
    def cors_origins_list(self) -> List[str]:
        """CORS_ORIGINS를 리스트로 반환"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
