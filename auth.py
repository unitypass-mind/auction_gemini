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
import smtplib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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


def generate_reset_token() -> str:
    """
    비밀번호 재설정 토큰 생성 (6자리 숫자 OTP)

    Returns:
        6자리 숫자 토큰 문자열
    """
    import random
    return str(random.randint(100000, 999999))


def send_password_reset_email(
    to_email: str,
    reset_token: str,
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    smtp_from_email: str,
    smtp_from_name: str = "경매 AI"
) -> bool:
    """
    비밀번호 재설정 이메일 발송

    Args:
        to_email: 수신자 이메일
        reset_token: 재설정 토큰
        smtp_host: SMTP 서버 주소
        smtp_port: SMTP 서버 포트
        smtp_username: SMTP 사용자명
        smtp_password: SMTP 비밀번호
        smtp_from_email: 발신자 이메일
        smtp_from_name: 발신자 이름

    Returns:
        발송 성공 여부
    """
    try:
        # 이메일 내용 작성
        message = MIMEMultipart("alternative")
        message["Subject"] = "[경매 AI] 비밀번호 재설정 안내"
        message["From"] = f"{smtp_from_name} <{smtp_from_email}>"
        message["To"] = to_email

        # HTML 본문
        html_body = f"""
        <html>
          <head></head>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
              <h2 style="color: #2196F3; text-align: center;">비밀번호 재설정</h2>

              <p>안녕하세요,</p>

              <p>비밀번호 재설정을 요청하셨습니다. 아래 인증번호를 앱에 입력하여 비밀번호를 재설정하실 수 있습니다.</p>

              <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                <p style="margin: 0; font-size: 14px; color: #666;">인증번호</p>
                <p style="margin: 10px 0 0 0; font-size: 32px; font-weight: bold; color: #2196F3; letter-spacing: 4px;">
                  {reset_token}
                </p>
              </div>

              <p><strong>주의사항:</strong></p>
              <ul>
                <li>이 인증번호는 1시간 동안만 유효합니다.</li>
                <li>인증번호는 한 번만 사용할 수 있습니다.</li>
                <li>비밀번호 재설정을 요청하지 않으셨다면 이 이메일을 무시하세요.</li>
              </ul>

              <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">

              <p style="font-size: 12px; color: #999; text-align: center;">
                본 메일은 발신 전용입니다. 문의사항은 앱 내 고객센터를 이용해주세요.
              </p>
            </div>
          </body>
        </html>
        """

        # 일반 텍스트 본문 (HTML을 지원하지 않는 이메일 클라이언트용)
        text_body = f"""
        [경매 AI] 비밀번호 재설정

        안녕하세요,

        비밀번호 재설정을 요청하셨습니다.
        아래 인증번호를 앱에 입력하여 비밀번호를 재설정하실 수 있습니다.

        인증번호: {reset_token}

        주의사항:
        - 이 인증번호는 1시간 동안만 유효합니다.
        - 인증번호는 한 번만 사용할 수 있습니다.
        - 비밀번호 재설정을 요청하지 않으셨다면 이 이메일을 무시하세요.

        본 메일은 발신 전용입니다.
        """

        # 이메일에 본문 추가
        part1 = MIMEText(text_body, "plain")
        part2 = MIMEText(html_body, "html")
        message.attach(part1)
        message.attach(part2)

        # SMTP 서버 연결 및 이메일 발송
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()  # TLS 암호화
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_from_email, to_email, message.as_string())

        logger.info(f"비밀번호 재설정 이메일 발송 성공: {to_email}")
        return True

    except Exception as e:
        logger.error(f"비밀번호 재설정 이메일 발송 실패: {e}", exc_info=True)
        return False


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
