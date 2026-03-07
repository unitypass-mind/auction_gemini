"""
Rate Limiting 미들웨어
slowapi를 사용한 API 요청 제한
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from config import settings


# Rate Limiter 초기화
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"]
)


def setup_rate_limiting(app):
    """
    FastAPI 앱에 Rate Limiting 설정 추가

    Args:
        app: FastAPI 애플리케이션 인스턴스
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    return limiter
