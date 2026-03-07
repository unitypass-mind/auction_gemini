"""
JWT 인증 시스템 모듈
사용자 인증, 토큰 생성 및 검증을 담당합니다.
"""
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 설정
SECRET_KEY = "your-secret-key-change-this-in-production-2026"  # TODO: 환경변수로 이동
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1시간
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30일


def hash_password(password: str) -> str:
    """
    비밀번호 해싱

    Args:
        password: 평문 비밀번호

    Returns:
        해시된 비밀번호
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호 검증

    Args:
        plain_password: 평문 비밀번호
        hashed_password: 해시된 비밀번호

    Returns:
        일치 여부
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Access Token 생성 (1시간 유효)

    Args:
        data: 토큰에 포함할 데이터 (user_id, email 등)
        expires_delta: 만료 시간 (기본: 1시간)

    Returns:
        JWT Access Token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Refresh Token 생성 (30일 유효)

    Args:
        data: 토큰에 포함할 데이터 (user_id, email 등)

    Returns:
        JWT Refresh Token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    JWT 토큰 검증 및 디코딩

    Args:
        token: JWT 토큰
        token_type: 토큰 타입 ("access" 또는 "refresh")

    Returns:
        디코딩된 페이로드 또는 None (검증 실패 시)
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # 토큰 타입 검증
        if payload.get("type") != token_type:
            logger.warning(f"토큰 타입 불일치: expected={token_type}, got={payload.get('type')}")
            return None

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("토큰 만료")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"유효하지 않은 토큰: {e}")
        return None


def decode_token_without_verification(token: str) -> Optional[Dict[str, Any]]:
    """
    토큰을 검증 없이 디코딩 (디버깅용)

    Args:
        token: JWT 토큰

    Returns:
        디코딩된 페이로드
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception as e:
        logger.error(f"토큰 디코딩 실패: {e}")
        return None


def validate_email(email: str) -> bool:
    """
    이메일 형식 검증

    Args:
        email: 이메일 주소

    Returns:
        유효성 여부
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> tuple[bool, str]:
    """
    비밀번호 강도 검증

    Args:
        password: 비밀번호

    Returns:
        (유효성 여부, 에러 메시지)
    """
    if len(password) < 8:
        return False, "비밀번호는 최소 8자 이상이어야 합니다"

    if len(password) > 100:
        return False, "비밀번호는 최대 100자 이하여야 합니다"

    # 숫자, 영문 포함 여부 확인 (선택적)
    has_digit = any(char.isdigit() for char in password)
    has_alpha = any(char.isalpha() for char in password)

    if not (has_digit and has_alpha):
        return False, "비밀번호는 영문과 숫자를 포함해야 합니다"

    return True, ""


if __name__ == "__main__":
    # 테스트
    logging.basicConfig(level=logging.INFO)

    # 비밀번호 해싱 테스트
    password = "test1234"
    hashed = hash_password(password)
    print(f"원본 비밀번호: {password}")
    print(f"해시된 비밀번호: {hashed}")
    print(f"검증 결과: {verify_password(password, hashed)}")
    print()

    # 토큰 생성 테스트
    user_data = {"user_id": 1, "email": "test@example.com"}
    access_token = create_access_token(user_data)
    refresh_token = create_refresh_token(user_data)

    print(f"Access Token: {access_token}")
    print(f"Refresh Token: {refresh_token}")
    print()

    # 토큰 검증 테스트
    verified = verify_token(access_token, "access")
    print(f"검증된 페이로드: {verified}")

    # 이메일 검증 테스트
    print(f"\n이메일 검증:")
    print(f"test@example.com: {validate_email('test@example.com')}")
    print(f"invalid-email: {validate_email('invalid-email')}")

    # 비밀번호 검증 테스트
    print(f"\n비밀번호 검증:")
    print(f"test1234: {validate_password('test1234')}")
    print(f"short: {validate_password('short')}")
