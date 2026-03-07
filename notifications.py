"""
FCM 푸시 알림 시스템
Firebase Cloud Messaging을 통한 모바일 푸시 알림을 관리합니다.
"""
import firebase_admin
from firebase_admin import credentials, messaging
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import json

logger = logging.getLogger(__name__)

# Firebase 초기화 상태
_firebase_initialized = False

def initialize_firebase():
    """Firebase Admin SDK 초기화"""
    global _firebase_initialized

    if _firebase_initialized:
        return True

    try:
        # Firebase 서비스 계정 키 파일 경로
        service_account_path = os.getenv(
            'FIREBASE_SERVICE_ACCOUNT',
            'firebase-service-account.json'
        )

        if not os.path.exists(service_account_path):
            logger.warning(
                f"Firebase 서비스 계정 키 파일을 찾을 수 없습니다: {service_account_path}\n"
                "FCM 푸시 알림 기능이 비활성화됩니다.\n"
                "Firebase Console에서 서비스 계정 키를 다운로드하여 프로젝트 루트에 "
                "'firebase-service-account.json'으로 저장하세요."
            )
            return False

        # Firebase 초기화
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        logger.info("Firebase Admin SDK 초기화 완료")
        return True

    except Exception as e:
        logger.error(f"Firebase 초기화 실패: {e}")
        return False


def send_notification(
    token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
    image_url: Optional[str] = None
) -> bool:
    """
    단일 디바이스로 푸시 알림 전송

    Args:
        token: FCM 디바이스 토큰
        title: 알림 제목
        body: 알림 본문
        data: 추가 데이터 (딕셔너리)
        image_url: 알림 이미지 URL

    Returns:
        bool: 전송 성공 여부
    """
    if not _firebase_initialized:
        if not initialize_firebase():
            logger.warning("Firebase 미초기화 상태 - 알림 전송 건너뜀")
            return False

    try:
        # 알림 메시지 구성
        notification = messaging.Notification(
            title=title,
            body=body,
            image=image_url
        )

        # Android 설정
        android_config = messaging.AndroidConfig(
            priority='high',
            notification=messaging.AndroidNotification(
                sound='default',
                color='#FF6B35'  # 앱 테마 컬러
            )
        )

        # 메시지 생성
        message = messaging.Message(
            notification=notification,
            data=data or {},
            token=token,
            android=android_config
        )

        # 전송
        response = messaging.send(message)
        logger.info(f"푸시 알림 전송 성공: {response}")
        return True

    except messaging.UnregisteredError:
        logger.warning(f"유효하지 않은 FCM 토큰: {token[:20]}...")
        return False
    except Exception as e:
        logger.error(f"푸시 알림 전송 실패: {e}")
        return False


def send_multicast_notification(
    tokens: List[str],
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
    image_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    여러 디바이스로 푸시 알림 일괄 전송

    Args:
        tokens: FCM 디바이스 토큰 리스트
        title: 알림 제목
        body: 알림 본문
        data: 추가 데이터
        image_url: 알림 이미지 URL

    Returns:
        dict: 전송 결과 {'success_count': int, 'failure_count': int}
    """
    if not _firebase_initialized:
        if not initialize_firebase():
            return {'success_count': 0, 'failure_count': len(tokens)}

    if not tokens:
        return {'success_count': 0, 'failure_count': 0}

    try:
        # 최대 500개씩 분할 전송 (FCM 제한)
        batch_size = 500
        total_success = 0
        total_failure = 0

        for i in range(0, len(tokens), batch_size):
            batch_tokens = tokens[i:i + batch_size]

            # 알림 메시지 구성
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )

            android_config = messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    sound='default',
                    color='#FF6B35'
                )
            )

            # MulticastMessage 생성
            message = messaging.MulticastMessage(
                notification=notification,
                data=data or {},
                tokens=batch_tokens,
                android=android_config
            )

            # 일괄 전송
            response = messaging.send_multicast(message)
            total_success += response.success_count
            total_failure += response.failure_count

            logger.info(
                f"일괄 알림 전송 완료: "
                f"성공={response.success_count}, 실패={response.failure_count}"
            )

        return {
            'success_count': total_success,
            'failure_count': total_failure
        }

    except Exception as e:
        logger.error(f"일괄 알림 전송 실패: {e}")
        return {'success_count': 0, 'failure_count': len(tokens)}


# 알림 템플릿
class NotificationTemplates:
    """푸시 알림 템플릿 모음"""

    @staticmethod
    def auction_reminder(case_number: str, auction_date: str) -> Dict[str, str]:
        """경매일 1일 전 알림"""
        return {
            'title': '내일은 경매일입니다 📅',
            'body': f'사건번호 {case_number}의 경매가 내일({auction_date}) 진행됩니다.',
            'data': {
                'type': 'auction_reminder',
                'case_number': case_number,
                'auction_date': auction_date
            }
        }

    @staticmethod
    def price_drop_alert(case_number: str, current_price: int) -> Dict[str, str]:
        """가격 하락 알림"""
        price_text = f"{current_price:,}원"
        return {
            'title': '감정가 하락 알림 📉',
            'body': f'사건번호 {case_number}의 감정가가 {price_text}로 하락했습니다.',
            'data': {
                'type': 'price_drop',
                'case_number': case_number,
                'current_price': str(current_price)
            }
        }

    @staticmethod
    def new_auction(case_number: str, address: str) -> Dict[str, str]:
        """신규 경매 등록 알림"""
        return {
            'title': '관심 지역 신규 경매 🏠',
            'body': f'{address}에 새로운 경매 물건이 등록되었습니다.',
            'data': {
                'type': 'new_auction',
                'case_number': case_number,
                'address': address
            }
        }

    @staticmethod
    def prediction_ready(case_number: str, predicted_price: int) -> Dict[str, str]:
        """AI 예측 완료 알림"""
        price_text = f"{predicted_price:,}원"
        return {
            'title': 'AI 낙찰가 예측 완료 🤖',
            'body': f'사건번호 {case_number}의 예측 낙찰가: {price_text}',
            'data': {
                'type': 'prediction_ready',
                'case_number': case_number,
                'predicted_price': str(predicted_price)
            }
        }


def validate_fcm_token(token: str) -> bool:
    """FCM 토큰 형식 유효성 검증"""
    if not token or not isinstance(token, str):
        return False

    # FCM 토큰은 일반적으로 152자 이상
    if len(token) < 140:
        return False

    # 기본적인 형식 체크 (알파벳, 숫자, _, -, : 만 허용)
    import re
    pattern = r'^[a-zA-Z0-9_:\-]+$'
    return re.match(pattern, token) is not None
